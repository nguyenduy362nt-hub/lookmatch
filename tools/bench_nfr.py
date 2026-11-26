"""Đo hiệu năng và độ ổn định của /search (NFR): độ trễ p50/p95/max và tỉ lệ lỗi.

    python tools/bench_nfr.py --image data/catalog/panda_kem/anh1.jpg --api-key <khoá> --n 40
Giới hạn mặc định 60 yêu cầu/phút/IP; nếu gặp 429 hãy thêm --pause 1.1 hoặc đặt LOOKMATCH_RATE_LIMIT=1000 khi đo.
Lượt khởi động (làm nóng mô hình) được tách riêng, không tính vào p95.
"""
import argparse
import math
import statistics
import time
from pathlib import Path

import httpx


def pct(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, math.ceil(p / 100 * len(xs)) - 1)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8000")   # không dùng "localhost" (Windows chậm ~2 giây/yêu cầu do thử IPv6)
    ap.add_argument("--image", required=True)
    ap.add_argument("--api-key", default="")
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--warmup", type=int, default=2)
    ap.add_argument("--pause", type=float, default=0.0)
    a = ap.parse_args()
    data = Path(a.image).read_bytes()
    h = {"X-API-Key": a.api_key} if a.api_key else {}

    client = httpx.Client(timeout=120)

    def one():
        t = time.perf_counter()
        try:
            r = client.post(f"{a.url}/search", files={"file": ("q.jpg", data, "image/jpeg")}, headers=h)
            return time.perf_counter() - t, r.status_code
        except httpx.HTTPError:
            return time.perf_counter() - t, 0

    warm = [one() for _ in range(a.warmup)]
    res = []
    for _ in range(a.n):
        res.append(one())
        time.sleep(a.pause)
    ok = [t for t, c in res if c == 200]
    loi5xx = sum(1 for _, c in res if c == 0 or c >= 500)
    gioi_han = sum(1 for _, c in res if c == 429)
    print(f"Làm nóng: {', '.join(f'{t:.2f}s({c})' for t, c in warm)}")
    print(f"\n| Số yêu cầu | Thành công | Lỗi 5xx/mất kết nối | Bị giới hạn 429 | p50 (s) | p95 (s) | max (s) |")
    print("|---|---|---|---|---|---|---|")
    if ok:
        print(f"| {a.n} | {len(ok)} | {loi5xx} ({100 * loi5xx / a.n:.1f}%) | {gioi_han} | "
              f"{statistics.median(ok):.2f} | {pct(ok, 95):.2f} | {max(ok):.2f} |")
    else:
        print(f"| {a.n} | 0 | {loi5xx} | {gioi_han} | - | - | - |")
    if gioi_han:
        print("\nCó yêu cầu bị 429: kết quả p95 chỉ tính các yêu cầu thành công; chạy lại với --pause 1.1.")


if __name__ == "__main__":
    main()
