"""Test cho tích hợp Google Sheets (viết theo đặc tả trước khi có code)."""
import io
import json

from fastapi.testclient import TestClient
from PIL import Image

from api import sheets
from api.main import app
from api.search import Searcher

CSV = "ma_mau,ten,gia,kich_thuoc\npanda_kem,Bộ chăn ga Panda kem,1.250.000đ,1m6x2m\nhoa_xanh_navy,Bộ Hoa xanh navy,1.100.000đ,1m8x2m\n"


class FakeResp:
    def __init__(self, text="", status=200):
        self.text, self.status = text, status

    def raise_for_status(self):
        if self.status >= 400:
            raise RuntimeError(f"HTTP {self.status}")


def test_doc_danh_muc_tu_csv():
    cat = sheets.parse_catalog_csv(CSV)
    assert cat["panda_kem"]["ten"] == "Bộ chăn ga Panda kem"
    assert cat["hoa_xanh_navy"]["gia"] == "1.100.000đ"


def test_sheets_loi_thi_dung_ban_cache(tmp_path):
    cache = tmp_path / "catalog_cache.csv"
    cache.write_text(CSV, encoding="utf-8")

    def get_loi(*a, **k):
        raise ConnectionError("mất mạng")

    cat, nguon = sheets.fetch_catalog("https://x/y.csv", cache, get=get_loi)
    assert nguon == "cache" and "panda_kem" in cat


def test_nhat_ky_loi_thi_xep_hang(tmp_path):
    pending = tmp_path / "log_pending.jsonl"

    def post_loi(*a, **k):
        return FakeResp(status=500)

    kq = sheets.log_search("https://hook", "khoa", {"top1": "panda_kem"}, pending, post=post_loi)
    assert kq == "queued"
    assert json.loads(pending.read_text(encoding="utf-8").splitlines()[0])["top1"] == "panda_kem"


def test_search_tra_them_ten_va_gia():
    class Fake:
        def embed(self, image):
            return [1, 0, 0, 0]

    app.state.embedder = Fake()
    app.state.searcher = Searcher([[1, 0, 0, 0], [0, 1, 0, 0]], ["panda_kem", "hoa_xanh_navy"])
    app.state.catalog = sheets.parse_catalog_csv(CSV)
    app.state.catalog_source = "sheets"
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), "white").save(buf, "PNG")
    r = TestClient(app).post("/search", files={"file": ("a.png", buf.getvalue(), "image/png")})
    assert r.status_code == 200
    body = r.json()
    assert body["results"][0]["ten"] == "Bộ chăn ga Panda kem"
    assert "1.250.000đ" in body["reply_text"]
