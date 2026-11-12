import io
import json
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import numpy as np
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError

from api import sheets
from api.search import Searcher

DATA_DIR = Path(os.environ.get("LOOKMATCH_DATA", "data"))
MAX_BYTES = 8 * 1024 * 1024
TOP_K = 10
# Cấu hình tích hợp lấy từ biến môi trường, KHÔNG ghi cứng trong code/repo
CATALOG_URL = os.environ.get("LOOKMATCH_CATALOG_CSV_URL", "")
LOG_WEBHOOK = os.environ.get("LOOKMATCH_LOG_WEBHOOK", "")
LOG_KEY = os.environ.get("LOOKMATCH_LOG_KEY", "")


@asynccontextmanager
async def lifespan(app):
    """Nạp sẵn chỉ mục, mô hình, danh mục khi server khởi động; gửi lại nhật ký đang chờ."""
    if app.state.searcher is None and (DATA_DIR / "index.npy").exists():
        _get_searcher()
        _get_embedder()
    _get_catalog()
    sheets.flush_pending(LOG_WEBHOOK, LOG_KEY, DATA_DIR / "log_pending.jsonl")
    yield


app = FastAPI(title="LookMatch API", version="0.3.0", lifespan=lifespan)
# CORS mở hoàn toàn chỉ dùng khi phát triển; khi triển khai thật giới hạn theo tên miền.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.state.searcher = None   # Searcher; test có thể gán trực tiếp
app.state.embedder = None   # đối tượng có .embed(PIL.Image)
app.state.catalog = None    # dict {ma_mau: {ten, gia, kich_thuoc}}; test có thể gán trực tiếp
app.state.catalog_source = "none"


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


def _get_catalog():
    if app.state.catalog is None:
        app.state.catalog, app.state.catalog_source = sheets.fetch_catalog(
            CATALOG_URL, DATA_DIR / "catalog_cache.csv")
    return app.state.catalog


@app.post("/catalog/refresh")
def catalog_refresh():
    """Nhân viên sửa giá trên Sheet xong bấm làm mới, không cần khởi động lại server."""
    app.state.catalog = None
    catalog = _get_catalog()
    return {"so_mau": len(catalog), "nguon": app.state.catalog_source}


@app.post("/search")
async def search(background: BackgroundTasks, file: UploadFile = File(...)):
    t0 = time.perf_counter()
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
    found = searcher.search(vector, TOP_K)
    catalog = _get_catalog()
    results = []
    for i, (pid, s) in enumerate(found):
        info = catalog.get(pid, {})
        results.append({"rank": i + 1, "product_id": pid, "score": round(s, 4),
                        "ten": info.get("ten", ""), "gia": info.get("gia", "")})
    top1_info = catalog.get(found[0][0], {}) if found else {}
    ms = int((time.perf_counter() - t0) * 1000)
    # Ghi nhật ký sau khi đã trả kết quả để Sheets chậm/lỗi không làm app chờ
    background.add_task(
        sheets.log_search, LOG_WEBHOOK, LOG_KEY,
        {"time": datetime.now().isoformat(timespec="seconds"), "file": file.filename or "",
         "top1": found[0][0] if found else "", "score": round(found[0][1], 4) if found else 0,
         "ms": ms, "catalog": app.state.catalog_source},
        DATA_DIR / "log_pending.jsonl")
    return {"results": results,
            "reply_text": sheets.reply_text(found[0][0], top1_info) if found else "",
            "catalog": app.state.catalog_source}
