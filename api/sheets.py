"""Tích hợp Google Sheets (không cần khoá Google Cloud):
- Đọc danh mục sản phẩm từ Sheet đã "Publish to web" dạng CSV (chỉ đọc).
- Ghi nhật ký mỗi lượt tìm qua webhook Google Apps Script (có khoá bí mật).
Lỗi mạng/Sheets: dùng bản lưu cache; nhật ký không gửi được thì xếp hàng vào file để gửi lại.
"""
import csv
import io
import json
from pathlib import Path

import httpx

CATALOG_COLUMNS = ("ten", "gia", "kich_thuoc")


def parse_catalog_csv(text: str) -> dict:
    """CSV có cột ma_mau (bắt buộc), ten, gia, kich_thuoc -> {ma_mau: {...}}."""
    out = {}
    for row in csv.DictReader(io.StringIO(text)):
        ma = (row.get("ma_mau") or "").strip()
        if not ma:
            continue
        out[ma] = {c: (row.get(c) or "").strip() for c in CATALOG_COLUMNS}
    return out


def fetch_catalog(url, cache_path: Path, get=httpx.get, timeout=5.0):
    """Trả (danh_muc, nguon) với nguon in {'sheets','cache','none'}."""
    cache_path = Path(cache_path)
    if url:
        try:
            resp = get(url, timeout=timeout, follow_redirects=True)
            resp.raise_for_status()
            catalog = parse_catalog_csv(resp.text)
            if not catalog:
                raise ValueError("Sheet rỗng hoặc thiếu cột ma_mau")
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(resp.text, encoding="utf-8")
            return catalog, "sheets"
        except Exception:
            pass
    if cache_path.exists():
        catalog = parse_catalog_csv(cache_path.read_text(encoding="utf-8"))
        if catalog:
            return catalog, "cache"
    return {}, "none"


def log_search(webhook, key, row: dict, pending_path: Path, post=httpx.post, timeout=5.0) -> str:
    """Gửi 1 dòng nhật ký. Trả 'disabled' | 'sent' | 'queued'."""
    if not webhook:
        return "disabled"
    try:
        resp = post(webhook, json={**row, "key": key}, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()
        return "sent"
    except Exception:
        pending_path = Path(pending_path)
        pending_path.parent.mkdir(parents=True, exist_ok=True)
        with pending_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return "queued"


def flush_pending(webhook, key, pending_path: Path, post=httpx.post, timeout=5.0):
    """Gửi lại các dòng đang xếp hàng. Trả (da_gui, con_lai)."""
    pending_path = Path(pending_path)
    if not webhook or not pending_path.exists():
        return 0, 0
    lines = [l for l in pending_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    kept, sent = [], 0
    for line in lines:
        try:
            resp = post(webhook, json={**json.loads(line), "key": key}, timeout=timeout, follow_redirects=True)
            resp.raise_for_status()
            sent += 1
        except Exception:
            kept.append(line)
    pending_path.write_text("".join(l + "\n" for l in kept), encoding="utf-8")
    return sent, len(kept)


def reply_text(product_id: str, info: dict) -> str:
    """Câu trả lời mẫu để nhân viên dán cho khách."""
    ten, gia = info.get("ten", ""), info.get("gia", "")
    if not ten:
        return ""
    return f"Dạ mẫu này là {ten}" + (f", giá {gia}" if gia else "") + f" (mã {product_id}) ạ."
