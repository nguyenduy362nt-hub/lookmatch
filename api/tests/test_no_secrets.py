"""Tuần 7 – quét mã nguồn: không để khoá, URL webhook, URL Sheet riêng tư hay khoá AWS nằm trong repo."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUET = ("api", "eval", "app/lib", "integration", "tools", ".github")
DUOI = {".py", ".dart", ".gs", ".yml", ".yaml", ".json"}
# Ghép chuỗi để file test này không tự khớp với chính nó
MAU = {
    "URL webhook Apps Script": "script" + r"\.google\.com/macros/s/[A-Za-z0-9_\-]{20,}",
    "URL Sheet đã xuất bản": "docs" + r"\.google\.com/spreadsheets/d/e/2PACX-[A-Za-z0-9_\-]{20,}",
    "Khoá AWS": "AK" + r"IA[0-9A-Z]{16}",
    "Khoá gán cứng": r"LOOKMATCH_LOG_KEY\s*=\s*['\"][^'\"<>\s]{6,}['\"]",
    "Khoá API gán cứng": r"LOOKMATCH_API_KEY\s*=\s*['\"][^'\"<>\s]{6,}['\"]",
}


def test_khong_co_bi_mat_trong_ma_nguon():
    loi = []
    for thu_muc in QUET:
        goc = ROOT / thu_muc
        if not goc.exists():
            continue
        for f in goc.rglob("*"):
            if f.suffix not in DUOI or f.name == Path(__file__).name or "__pycache__" in f.parts:
                continue
            text = f.read_text(encoding="utf-8", errors="ignore")
            for ten, mau in MAU.items():
                if re.search(mau, text):
                    loi.append(f"{f.relative_to(ROOT)}: {ten}")
    assert not loi, "Phát hiện bí mật trong mã nguồn:\n" + "\n".join(loi)
