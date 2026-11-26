"""Chạy eval: ảnh -> CLIP -> top-K -> chấm tự động bằng api/evaluation.py.

  python eval/run_eval.py [eval/cases.csv] [--k 5] [--threshold 0.80]

Cách chấm: một ca ĐẠT khi mẫu đúng nằm trong top-K (K=5, theo giả thuyết H1: Recall@5 >= 80%).
Sinh: eval/report.md (tổng hợp + bảng ca trượt) và eval/hand_read.csv (10 ca ngẫu nhiên để đọc tay).
"""
import argparse
import csv
import json
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from api import evaluation  # noqa: E402


def rank_ids(searcher, vector, depth=40):
    ranked = []
    for pid, _ in searcher.search(vector, depth):
        if pid not in ranked:
            ranked.append(pid)
    return ranked


def run(cases, searcher, embedder, k):
    # Bài học W5: chỉ mục chưa nạp lại thì mẫu mới không bao giờ tìm thấy -> báo ngay, không để thành "lỗi mô hình"
    missing = sorted({c["true_product"] for c in cases} - set(searcher.ids))
    if missing:
        print(f"CẢNH BÁO: {len(missing)} mẫu đúng không có trong chỉ mục: {missing}. Chạy python eval/build_index.py")
    out = []
    for c in cases:
        ranked = rank_ids(searcher, embedder.embed(Image.open(c["image"])))
        ok, rank = evaluation.score_case(ranked, c["true_product"], k)
        out.append({**c, "passed": ok, "rank": rank, "top1": ranked[0] if ranked else "",
                    "top5": " ".join(ranked[:5])})
    return out


def write_report(results, summ, k, threshold, path):
    L = [f"# Báo cáo eval (K={k}, ngưỡng đạt {threshold:.0%})", "",
         f"- Tổng: {summ['passed']}/{summ['n']} = {summ['rate']:.1%} · MRR = {summ['mrr']:.3f} · "
         f"{'ĐẠT' if summ['rate'] >= threshold else 'CHƯA ĐẠT'} ngưỡng", "",
         "| Nguồn | Đạt/Số ca | Tỉ lệ |", "|---|---|---|"]
    for s, d in summ["by_source"].items():
        L.append(f"| {s} | {d['passed']}/{d['n']} | {d['rate']:.1%} |")
    L += ["", "## Ca trượt", "", "| case_id | nguồn | mẫu đúng | top-1 hệ thống | hạng mẫu đúng | ghi chú |",
          "|---|---|---|---|---|---|"]
    for r in results:
        if not r["passed"]:
            L.append(f"| {r['case_id']} | {r['source']} | {r['true_product']} | {r['top1']} | "
                     f"{r['rank'] or '>'+str(k)} | {r.get('note','')} |")
    Path(path).write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cases", nargs="?", default="eval/cases.csv")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--threshold", type=float, default=0.80)
    a = ap.parse_args()
    from api.embedder import ClipEmbedder
    from api.search import Searcher
    searcher = Searcher(np.load("data/index.npy"),
                        json.loads(Path("data/ids.json").read_text(encoding="utf-8")))
    cases = evaluation.load_cases(a.cases)
    results = run(cases, searcher, ClipEmbedder(), a.k)
    summ = evaluation.summarize(results)
    write_report(results, summ, a.k, a.threshold, "eval/report.md")
    random.Random(42).shuffle(sample := list(results))
    with open("eval/hand_read.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["case_id", "image", "true_product", "top1", "top5", "tu_dong_cham", "em_doc_tay_dung_sai", "ghi_chu"])
        for r in sample[:10]:
            w.writerow([r["case_id"], r["image"], r["true_product"], r["top1"], r["top5"],
                        "dat" if r["passed"] else "truot", "", ""])
    print(f"Đạt {summ['passed']}/{summ['n']} = {summ['rate']:.1%} (MRR {summ['mrr']:.3f})")
    for s, d in summ["by_source"].items():
        print(f"  {s:15s} {d['passed']}/{d['n']} = {d['rate']:.1%}")
    print("Đã ghi eval/report.md và eval/hand_read.csv")
