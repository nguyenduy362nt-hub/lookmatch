"""Cô lập test khỏi biến môi trường của terminal (vd. LOOKMATCH_API_KEY em đặt để chạy server)."""
import pytest


@pytest.fixture(autouse=True)
def _cau_hinh_sach(monkeypatch):
    try:
        import api.main as m
    except ImportError:          # môi trường chưa có FastAPI/CLIP: các test thuần Python vẫn chạy
        return
    from api import security
    monkeypatch.setattr(m, "SETTINGS", security.Settings())
    monkeypatch.setattr(m, "LIMITER", security.RateLimiter(1000, 60))
