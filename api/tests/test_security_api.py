"""Tuần 7 – tấn công thử qua HTTP vào API thật (cần fastapi; chạy trên máy em và trên CI)."""
import io

from fastapi.testclient import TestClient
from PIL import Image

import api.main as m
from api import security
from api.search import Searcher


class FakeEmbedder:
    def embed(self, image):
        return [1, 0, 0, 0]


def _client(tmp_path, monkeypatch, **cau_hinh):
    monkeypatch.setattr(m, "DATA_DIR", tmp_path)
    monkeypatch.setattr(m, "LOG_WEBHOOK", "")
    monkeypatch.setattr(m, "SETTINGS", security.Settings(**cau_hinh))
    monkeypatch.setattr(m, "LIMITER", security.RateLimiter(m.SETTINGS.rate_limit, m.SETTINGS.rate_window))
    m.app.state.embedder = FakeEmbedder()
    m.app.state.searcher = Searcher([[1, 0, 0, 0], [0, 1, 0, 0]], ["panda_kem", "hoa_xanh_navy"])
    m.app.state.catalog = {}
    return TestClient(m.app)


def _anh(fmt="PNG"):
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), "white").save(buf, fmt)
    return buf.getvalue()


def _tim(c, ten="a.png", noi_dung=None, headers=None):
    return c.post("/search", files={"file": (ten, noi_dung if noi_dung is not None else _anh(), "image/png")},
                  headers=headers or {})


def test_health_luon_mo_khong_can_khoa(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch, api_key="bi-mat")
    assert c.get("/health").status_code == 200


def test_khong_co_khoa_api_bi_chan_401(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch, api_key="bi-mat")
    assert _tim(c).status_code == 401
    assert _tim(c, headers={"X-API-Key": "sai"}).status_code == 401
    assert c.post("/catalog/refresh").status_code == 401
    assert c.post("/feedback", json={"search_id": "abc", "verdict": "dung"}).status_code == 401


def test_dung_khoa_api_thi_tim_duoc(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch, api_key="bi-mat")
    r = _tim(c, headers={"X-API-Key": "bi-mat"})
    assert r.status_code == 200 and r.json()["search_id"]


def test_chua_dat_khoa_thi_chay_che_do_phat_trien(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    assert _tim(c).status_code == 200


def test_goi_don_dap_bi_429_kem_retry_after(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch, rate_limit=3, rate_window=60)
    ma = [_tim(c).status_code for _ in range(5)]
    assert ma == [200, 200, 200, 429, 429]
    r = _tim(c)
    assert int(r.headers["Retry-After"]) >= 1


def test_doan_khoa_lien_tuc_cung_bi_gioi_han(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch, api_key="bi-mat", rate_limit=3, rate_window=60)
    ma = [_tim(c, headers={"X-API-Key": f"doan{i}"}).status_code for i in range(5)]
    assert ma == [401, 401, 401, 429, 429]


def test_file_gia_dang_anh_bi_chan_400(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    r = _tim(c, ten="virus.jpg", noi_dung=b"<script>alert(1)</script>")
    assert r.status_code == 400


def test_gif_bi_chan_415(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    assert _tim(c, ten="a.gif", noi_dung=_anh("GIF")).status_code == 415


def test_anh_qua_lon_bi_chan_413(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    r = _tim(c, noi_dung=b"\x89PNG" + b"0" * (9 * 1024 * 1024))
    assert r.status_code == 413


def test_ten_file_cong_thuc_duoc_lam_sach_truoc_khi_ghi_nhat_ky(tmp_path, monkeypatch):
    ghi = []
    monkeypatch.setattr(m.sheets, "log_search", lambda url, key, payload, pending: ghi.append(payload))
    c = _client(tmp_path, monkeypatch)
    assert _tim(c, ten='=HYPERLINK("http://evil.example","x").png').status_code == 200
    assert ghi and ghi[0]["file"].startswith("'=")


def test_header_an_toan_co_mat(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    h = c.get("/health").headers
    assert h["x-content-type-options"] == "nosniff"
    assert h["cache-control"] == "no-store"
    assert h["x-frame-options"] == "DENY"


def test_phan_hoi_qua_dai_bi_422(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    r = c.post("/feedback", json={"search_id": "a" * 500, "verdict": "dung"})
    assert r.status_code == 422
    r = c.post("/feedback", json={"search_id": "abc", "verdict": "sai", "true_product": "x" * 500})
    assert r.status_code == 422


def test_search_id_duong_dan_la_bi_chan(tmp_path, monkeypatch):
    c = _client(tmp_path, monkeypatch)
    r = c.post("/feedback", json={"search_id": "../../etc/passwd", "verdict": "dung"})
    assert r.status_code in (400, 422)
