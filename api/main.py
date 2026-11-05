import io
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError

from api.search import Searcher

@asynccontextmanager
async def lifespan(app):
    """Nạp sẵn chỉ mục và mô hình khi server khởi động, để lượt tìm đầu tiên không bị chậm."""
    if app.state.searcher is None and (DATA_DIR / "index.npy").exists():
        _get_searcher()
        _get_embedder()
    yield


app = FastAPI(title="LookMatch API", version="0.2.0", lifespan=lifespan)
# Cho phép app Flutter chạy trên trình duyệt (cổng khác) gọi API. Chỉ dùng khi phát triển;
# khi triển khai thật sẽ giới hạn allow_origins theo tên miền của app.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.state.searcher = None   # Searcher; test có thể gán trực tiếp
app.state.embedder = None   # đối tượng có .embed(PIL.Image)

DATA_DIR = Path(os.environ.get("LOOKMATCH_DATA", "data"))
MAX_BYTES = 8 * 1024 * 1024
TOP_K = 10


@app.get("/")
def root():
    return {"name": "LookMatch API", "version": app.version}


@app.get("/health")
def health():
    return {"status": "ok"}


def _get_searcher():
    if app.state.searcher is None:
        vec, ids = DATA_DIR / "index.npy", DATA_DIR / "ids.json"
        if not (vec.exists() and ids.exists()):
            raise HTTPException(503, "Chưa có chỉ mục. Chạy: python eval/build_index.py")
        app.state.searcher = Searcher(np.load(vec), json.loads(ids.read_text(encoding="utf-8")))
    return app.state.searcher


def _get_embedder():
    if app.state.embedder is None:
        from api.embedder import ClipEmbedder
        app.state.embedder = ClipEmbedder()
    return app.state.embedder


@app.post("/search")
async def search(file: UploadFile = File(...)):
    data = await file.read()
    if not data:
        raise HTTPException(400, "File rỗng")
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "Ảnh quá lớn (tối đa 8 MB)")
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(400, "File không phải ảnh hợp lệ")
    searcher = _get_searcher()
    vector = _get_embedder().embed(image)
    results = searcher.search(vector, TOP_K)
    return {"results": [{"rank": i + 1, "product_id": pid, "score": round(s, 4)}
                        for i, (pid, s) in enumerate(results)]}