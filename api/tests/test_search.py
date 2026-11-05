import io

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

from api.main import app
from api.search import Searcher


class FakeEmbedder:
    """Embedder giả: luôn trả vector [1,0,0,0], khỏi cần tải CLIP."""
    def embed(self, image):
        return np.array([1, 0, 0, 0], dtype="float32")


def anh_png():
    """Tạo ảnh PNG 10x10 trong bộ nhớ."""
    buf = io.BytesIO()
    Image.new("RGB", (10, 10)).save(buf, format="PNG")
    return buf.getvalue()


def setup_module():
    app.state.embedder = FakeEmbedder()
    app.state.searcher = Searcher(
        [[1, 0, 0, 0], [0, 1, 0, 0], [0.9, 0.1, 0, 0]],
        ["SP_A", "SP_B", "SP_C"],
    )


client = TestClient(app)


def test_search_tra_ve_dung_thu_tu():
    r = client.post("/search", files={"file": ("a.png", anh_png(), "image/png")})
    assert r.status_code == 200
    kq = r.json()["results"]
    assert kq[0]["product_id"] == "SP_A"          # vector [1,0,0,0] giống SP_A nhất
    assert [x["rank"] for x in kq] == [1, 2, 3]
    diem = [x["score"] for x in kq]
    assert diem == sorted(diem, reverse=True)     # điểm giảm dần


def test_search_file_rong():
    r = client.post("/search", files={"file": ("a.png", b"", "image/png")})
    assert r.status_code == 400


def test_search_khong_phai_anh():
    r = client.post("/search", files={"file": ("a.txt", b"xin chao", "text/plain")})
    assert r.status_code == 400
