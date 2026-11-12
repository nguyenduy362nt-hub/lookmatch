"""Tính Recall@1/5/10 và (nếu có cột scenario) thống kê theo từng kiểu tình huống.

Dùng: python eval/eval_recall.py [file_csv]     (mặc định eval/queries.csv)
CSV cần cột: file,product_id  (tuỳ chọn: scenario). Ảnh khách thật để ngoài GitHub.
"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from api.embedder import ClipEmbedder  # noqa: E402
from api.search import Searcher  # noqa: E402

KS = (1, 5, 10)


def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "eval/queries.csv"
    searcher = Searcher(np.load("data/index.npy"), json.loads(Path("data/ids.json").read_text(encoding="utf-8")))
    emb = ClipEmbedder()
    rows = list(csv.DictReader(open(csv_path, encoding="utf-8")))
    total = {k: 0 for k in KS}
    by = defaultdict(lambda: {"n": 0, **{k: 0 for k in KS}})
    for r in rows:
        res = searcher.search(emb.embed(Image.open(r["file"])), 40)
        ranked = []
        for pid, _ in res:
            if pid not in ranked:
                ranked.append(pid)
        tag = r.get("scenario", "tat_ca") or "tat_ca"
        by[tag]["n"] += 1
        for k in KS:
            ok = r["product_id"] in ranked[:k]
            total[k] += ok
            by[tag][k] += ok
    n = len(rows)
    print(f"File: {csv_path} | Số ảnh query: {n}")
    for k in KS:
        print(f"Recall@{k} = {total[k]}/{n} = {total[k] / n:.1%}")
    if len(by) > 1:
        print("\nTheo tình huống (Recall@1 / Recall@5):")
        for tag, d in by.items():
            print(f"  {tag:10s} n={d['n']:3d}  R@1={d[1]}/{d['n']}  R@5={d[5]}/{d['n']}")


if __name__ == "__main__":
    main()
