"""Test đầu-cuối qua HTTP: /search -> /feedback -> file feedback.jsonl (cần fastapi, chạy trên máy em)."""
import io

from fastapi.testclient import TestClient
from PIL import Image

import api.main as m
from api import feedback
from api.search import Searcher


class FakeEmbedder:
    def embed(self, image):
        return [1, 0, 0, 0]


def _client(tmp_path, monkeypatch):
    monkeypatch.setattr(m, "DATA_DIR", tmp_path)
    monkeypatch.setattr(m, "LOG_WEBHOOK", "")
    m.app.state.embedder = FakeEmbedder()
    m.app.state.searcher = Searcher([[1, 0, 0, 0], [0, 1, 0, 0]], ["panda_kem", "hoa_xanh_navy"])
    m.app.state.catalog = {}
    return TestClient(m.app)


def _tim(c):
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), "white").save(buf, "PNG")
    r = c.post("/search", files={"file": ("a.png", buf.getvalue(), "image/png")})
    assert r.status_code == 200
    return r.json()["search_id"]


def test_tim_roi_bao_sai_duoc_ghi_lai(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    sid = _tim(c)
    assert (tmp_path / "queries" / f"{sid}.jpg").exists()
    r = c.post("/feedback", json={"search_id": sid, "verdict": "sai", "true_product": "hoa_xanh_navy"})
    assert r.status_code == 200
    row = feedback.load_feedback(tmp_path)[0]
    assert row["top1"] == "panda_kem" and row["true_product"] == "hoa_xanh_navy" and row["rank_that"] == 2


def test_feedback_search_id_sai_tra_404(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    r = c.post("/feedback", json={"search_id": "000000000000", "verdict": "dung"})
    assert r.status_code == 404


def test_feedback_thieu_ma_dung_tra_422(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    sid = _tim(c)
    r = c.post("/feedback", json={"search_id": sid, "verdict": "sai"})
    assert r.status_code == 422


def test_search_tra_search_id_va_hang_1_dung(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), "white").save(buf, "PNG")
    r = c.post("/search", files={"file": ("a.png", buf.getvalue(), "image/png")})
    body = r.json()
    assert r.status_code == 200 and len(body["search_id"]) == 12
    assert body["results"][0]["product_id"] == "panda_kem"


def test_search_file_rong_va_khong_phai_anh(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    assert c.post("/search", files={"file": ("a.png", b"", "image/png")}).status_code == 400
    assert c.post("/search", files={"file": ("a.txt", b"xin chao", "text/plain")}).status_code == 400
