"""Tuần 7 – các biện pháp bảo mật của API (thuần Python, không cần FastAPI để test).

1. Kiểm tra đầu vào ảnh: giới hạn dung lượng, chỉ nhận JPEG/PNG/WebP theo NỘI DUNG file
   (không tin đuôi file hay Content-Type), giới hạn số điểm ảnh (chống "bom giải nén").
2. Giới hạn tần suất theo địa chỉ IP (cửa sổ trượt) – chống gọi dồn làm treo server CPU.
3. Khoá API trong header X-API-Key, so sánh thời gian không đổi, đọc từ biến môi trường.
4. Làm sạch tên file trước khi ghi vào Google Sheet (chống chèn công thức =HYPERLINK(...)).
5. Cấu hình (khoá, CORS, ngưỡng) đọc từ biến môi trường, không ghi cứng trong code.
"""
import hmac
import io
import re
import time
from collections import deque
from dataclasses import dataclass

from PIL import Image, UnidentifiedImageError

ALLOWED_FORMATS = ("JPEG", "PNG", "WEBP")
MAX_BYTES = 8 * 1024 * 1024
MAX_PIXELS = 40_000_000          # ~ ảnh 6300x6300; điện thoại phổ thông thường ≤ 50 MP nhưng đã nén lại khi gửi Zalo


class SecurityError(ValueError):
    """Đầu vào bị từ chối; .status là mã HTTP, .headers là header kèm theo (nếu có)."""

    def __init__(self, message, status=400, headers=None):
        super().__init__(message)
        self.status = status
        self.headers = headers or {}


# ---------------------------------------------------------------- 1. kiểm tra ảnh
def open_safe_image(data: bytes, max_bytes: int = MAX_BYTES, max_pixels: int = MAX_PIXELS):
    """Trả về PIL.Image đã nạp xong hoặc ném SecurityError. Kiểm tra theo thứ tự rẻ → đắt."""
    if not data:
        raise SecurityError("File rỗng", 400)
    if len(data) > max_bytes:
        raise SecurityError(f"Ảnh quá lớn (tối đa {max_bytes // (1024 * 1024)} MB)", 413)
    try:
        probe = Image.open(io.BytesIO(data))      # chỉ đọc phần đầu file, chưa giải nén điểm ảnh
        fmt, (w, h) = probe.format, probe.size
    except Image.DecompressionBombError:
        raise SecurityError("Kích thước ảnh quá lớn", 413)
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError):
        raise SecurityError("File không phải ảnh hợp lệ", 400)
    if fmt not in ALLOWED_FORMATS:
        raise SecurityError("Chỉ nhận ảnh JPEG, PNG hoặc WebP", 415)
    if w * h > max_pixels:
        raise SecurityError("Kích thước ảnh quá lớn", 413)
    try:
        image = Image.open(io.BytesIO(data))
        image.load()                              # giải nén thật; file hỏng sẽ lỗi ở đây
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError):
        raise SecurityError("File ảnh bị hỏng", 400)
    return image


# ---------------------------------------------------------------- 2. giới hạn tần suất
class RateLimiter:
    """Cửa sổ trượt: tối đa max_calls yêu cầu / window_s giây cho mỗi khoá (thường là IP).

    Bộ nhớ có chặn trên (max_keys) để kẻ tấn công đổi IP liên tục không làm đầy RAM.
    """

    def __init__(self, max_calls=60, window_s=60, clock=time.monotonic, max_keys=10_000):
        self.max_calls, self.window_s, self.clock, self.max_keys = max_calls, window_s, clock, max_keys
        self._hits = {}

    def check(self, key):
        """Trả (được_phép, số_giây_chờ). Mỗi lần gọi tính là một yêu cầu."""
        now = self.clock()
        if len(self._hits) >= self.max_keys:
            self._prune(now)
        q = self._hits.setdefault(key, deque())
        while q and now - q[0] >= self.window_s:
            q.popleft()
        if len(q) >= self.max_calls:
            return False, max(1, int(self.window_s - (now - q[0])) + 1)
        q.append(now)
        return True, 0

    def _prune(self, now):
        for k in [k for k, q in self._hits.items() if not q or now - q[-1] >= self.window_s]:
            del self._hits[k]
        if len(self._hits) >= self.max_keys:      # vẫn đầy: bỏ bớt khoá cũ nhất
            for k in list(self._hits)[: self.max_keys // 10]:
                del self._hits[k]


# ---------------------------------------------------------------- 3. khoá API
def check_api_key(provided, expected) -> bool:
    """expected rỗng = chưa bật xác thực (chế độ phát triển). So sánh thời gian không đổi."""
    if not expected:
        return True
    if not provided:
        return False
    return hmac.compare_digest(provided.encode("utf-8"), expected.encode("utf-8"))


# ---------------------------------------------------------------- 4. làm sạch ô Sheet
_CTRL = re.compile(r"[\x00-\x1f\x7f]")


def safe_cell(text, max_len=100) -> str:
    """Bỏ ký tự điều khiển, cắt độ dài; chặn công thức (= + - @) bằng dấu nháy đơn đứng đầu."""
    s = _CTRL.sub(" ", str(text or "")).strip()[:max_len]
    if s[:1] in ("=", "+", "-", "@"):
        s = "'" + s
    return s


# ---------------------------------------------------------------- 5. cấu hình
def _int(v, default):
    try:
        n = int(v)
        return n if n > 0 else default
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Settings:
    api_key: str = ""
    cors_origins: tuple = ("*",)
    rate_limit: int = 60
    rate_window: int = 60
    trust_proxy: bool = False

    @classmethod
    def from_env(cls, env):
        origins = tuple(o.strip() for o in (env.get("LOOKMATCH_CORS_ORIGINS") or "*").split(",") if o.strip())
        return cls(
            api_key=(env.get("LOOKMATCH_API_KEY") or "").strip(),
            cors_origins=origins or ("*",),
            rate_limit=_int(env.get("LOOKMATCH_RATE_LIMIT"), 60),
            rate_window=_int(env.get("LOOKMATCH_RATE_WINDOW"), 60),
            trust_proxy=(env.get("LOOKMATCH_TRUST_PROXY") or "").strip().lower() in ("1", "true", "yes"),
        )
