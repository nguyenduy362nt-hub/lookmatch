"""Gom phản hồi của nhân viên thành ca eval.

  python eval/harvest_failures.py                 # đọc data/feedback.jsonl + data/queries/
  python eval/harvest_failures.py --simulated eval/scenarios.csv   # thêm ca mô phỏng (nhãn mo_phong)

Quy ước nguồn gốc (cột source):
  sai_that        nhân viên bấm "Sai" trên ảnh khách thật -> ca khó nhất, giữ lại để sửa
  anh_khach_that  nhân viên bấm "Đúng" trên ảnh khách thật
  mo_phong        ảnh catalog bị biến đổi bằng code (KHÔNG tính là ảnh thật)
Ảnh khách nằm ở eval/real/ (đã .gitignore) -- không đưa lên GitHub.
Chạy lại nhiều lần an toàn: ca đã có (cùng search_id) không bị thêm trùng.
"""
import argparse
import csv
import random
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from api import feedback  # noqa: E402

FIELDS = ["case_id", "image", "true_product", "source", "note"]


def read_cases(path):
    if not Path(path).exists():
        return []
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def harvest(data_dir, out_csv, real_dir, simulated_csv=None, sample=None):
    cases = read_cases(out_csv)
    have = {c["case_id"] for c in cases}
    real_dir = Path(real_dir)
    real_dir.mkdir(parents=True, exist_ok=True)
    added = 0
    for fb in feedback.load_feedback(data_dir):
        if fb["verdict"] == "khong_co" or not fb.get("true_product"):
            continue                       # mẫu không có trong kho: không đo được Recall
        cid = f"real_{fb['search_id']}"
        src_img = Path(data_dir) / "queries" / f"{fb['search_id']}.jpg"
        if cid in have or not src_img.exists():
            continue
        shutil.copy(src_img, real_dir / f"{cid}.jpg")
        source = "anh_khach_that" if fb["verdict"] == "dung" else "sai_that"
        note = f"top1 lúc đó={fb['top1']}; hạng mẫu đúng={fb['rank_that']}"
        cases.append({"case_id": cid, "image": str(real_dir / f"{cid}.jpg").replace("\\", "/"),
                      "true_product": fb["true_product"], "source": source, "note": note})
        have.add(cid)
        added += 1
    if simulated_csv:
        sim = read_cases(simulated_csv)
        if sample:   # chọn NGẪU NHIÊN (seed cố định), không chọn theo kết quả để tránh thiên lệch
            sim = random.Random(42).sample(sim, min(sample, len(sim)))
        for r in sim:
            cid = f"sim_{r['product_id']}__{r['scenario']}"
            if cid in have:
                continue
            cases.append({"case_id": cid, "image": r["file"], "true_product": r["product_id"],
                          "source": "mo_phong", "note": r["scenario"]})
            have.add(cid)
            added += 1
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(cases)
    return added, cases


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data")
    ap.add_argument("--out", default="eval/cases.csv")
    ap.add_argument("--real-dir", default="eval/real")
    ap.add_argument("--simulated", default=None)
    ap.add_argument("--sample", type=int, default=None, help="chỉ lấy N ca mô phỏng ngẫu nhiên (seed 42)")
    a = ap.parse_args()
    n, cases = harvest(a.data, a.out, a.real_dir, a.simulated, a.sample)
    from collections import Counter
    print(f"Thêm {n} ca. Tổng {len(cases)} ca:", dict(Counter(c['source'] for c in cases)))
