import json
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import numpy as np
from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from api import feedback, security, sheets
from api.search import Searcher

DATA_DIR = Path(os.environ.get("LOOKMATCH_DATA", "data"))
TOP_K = 10
# Cấu hình tích hợp lấy từ biến môi trường, KHÔNG ghi cứng trong code/repo
CATALOG_URL = os.environ.get("LOOKMATCH_CATALOG_CSV_URL", "")
LOG_WEBHOOK = os.environ.get("LOOKMATCH_LOG_WEBHOOK", "")
LOG_KEY = os.environ.get("LOOKMATCH_LOG_KEY", "")
# Tuần 7: bảo mật – khoá API, CORS, giới hạn tần suất đều đọc từ biến môi trường (xem api/security.py)
SETTINGS = security.Settings.from_env(os.environ)
LIMITER = security.RateLimiter(SETTINGS.rate_limit, SETTINGS.rate_window)


@asynccontextmanager
async def lifespan(app):
    """Nạp sẵn chỉ mục, mô hình, danh mục khi server khởi động; gửi lại nhật ký đang chờ."""
    if app.state.searcher is None and (DATA_DIR / "index.npy").exists():
        _get_searcher()
        _get_embedder()
    _get_catalog()
    sheets.flush_pending(LOG_WEBHOOK, LOG_KEY, DATA_DIR / "log_pending.jsonl")
    yield


app = FastAPI(title="LookMatch API", version="0.9.0", lifespan=lifespan)
# CORS: mặc định "*" (phát triển). Khi triển khai đặt LOOKMATCH_CORS_ORIGINS=http://tên-miền-app,...
app.add_middleware(CORSMiddleware, allow_origins=list(SETTINGS.cors_origins),
                   allow_methods=["GET", "POST"], allow_headers=["*"])


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Frame-Options"] = "DENY"
    return response


def _client_ip(request: Request) -> str:
    if SETTINGS.trust_proxy:                       # chỉ bật khi đứng sau reverse proxy tin cậy
        fwd = request.headers.get("x-forwarded-for", "")
        if fwd:
            return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def guard(request: Request):
    """Chạy trước các endpoint nhạy cảm: giới hạn tần suất rồi mới kiểm khoá API (thử khoá sai cũng bị tính)."""
    ok, retry = LIMITER.check(_client_ip(request))
    if not ok:
        raise HTTPException(429, f"Quá nhiều yêu cầu, thử lại sau {retry} giây",
                            headers={"Retry-After": str(retry)})
    if not security.check_api_key(request.headers.get("x-api-key"), SETTINGS.api_key):
        raise HTTPException(401, "Thiếu hoặc sai khoá API")


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


@app.post("/catalog/refresh", dependencies=[Depends(guard)])
def catalog_refresh():
    """Nhân viên sửa giá trên Sheet xong bấm làm mới, không cần khởi động lại server."""
    app.state.catalog = None
    catalog = _get_catalog()
    return {"so_mau": len(catalog), "nguon": app.state.catalog_source}


@app.post("/search", dependencies=[Depends(guard)])
async def search(background: BackgroundTasks, file: UploadFile = File(...)):
    t0 = time.perf_counter()
    data = await file.read()
    try:
        image = security.open_safe_image(data)
    except security.SecurityError as e:
        raise HTTPException(e.status, str(e))
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
    # Tính năng #3: lưu ảnh + top-K để nhân viên phản hồi đúng/sai sau đó
    search_id = feedback.new_search_id()
    try:
        feedback.save_query(DATA_DIR, search_id, image, found)
    except OSError:
        search_id = ""   # đĩa đầy/không ghi được: vẫn trả kết quả tìm, chỉ mất khả năng phản hồi
    # Ghi nhật ký sau khi đã trả kết quả để Sheets chậm/lỗi không làm app chờ
    background.add_task(
        sheets.log_search, LOG_WEBHOOK, LOG_KEY,
        {"time": datetime.now().isoformat(timespec="seconds"), "file": security.safe_cell(file.filename),
         "top1": found[0][0] if found else "", "score": round(found[0][1], 4) if found else 0,
         "ms": ms, "catalog": app.state.catalog_source},
        DATA_DIR / "log_pending.jsonl")
    return {"search_id": search_id, "results": results,
            "reply_text": sheets.reply_text(found[0][0], top1_info) if found else "",
            "catalog": app.state.catalog_source}


class FeedbackIn(BaseModel):
    search_id: str = Field(max_length=32)
    verdict: str = Field(max_length=16)                        # "dung" | "sai" | "khong_co"
    true_product: str | None = Field(default=None, max_length=80)   # bắt buộc khi verdict = "sai"


@app.post("/feedback", dependencies=[Depends(guard)])
def post_feedback(body: FeedbackIn, background: BackgroundTasks):
    """Nhân viên báo kết quả đúng/sai. Ca sai được giữ lại làm dữ liệu eval (eval/harvest_failures.py)."""
    try:
        valid = set(_get_searcher().ids)
        row = feedback.record_feedback(DATA_DIR, body.search_id, body.verdict, body.true_product, valid)
    except feedback.FeedbackError as e:
        raise HTTPException(e.status, str(e))
    background.add_task(
        sheets.log_search, LOG_WEBHOOK, LOG_KEY, {**row, "loai": "phan_hoi"},
        DATA_DIR / "log_pending.jsonl")
    return {"ok": True, "da_ghi": row}
