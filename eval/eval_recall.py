"""Tính Recall@1/5/10 trên ảnh khách thật.

Cần: data/index.npy, data/ids.json, và eval/queries.csv với cột: file,product_id
(file là đường dẫn tới ảnh khách, đặt trong eval/queries_raw/, không đưa lên GitHub)
Chạy: python eval/eval_recall.py
"""
import csv
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from api.embedder import ClipEmbedder  # noqa: E402
from api.search import Searcher  # noqa: E402


def main():
    searcher = Searcher(np.load("data/index.npy"), json.loads(Path("data/ids.json").read_text(encoding="utf-8")))
    emb = ClipEmbedder()
    rows = list(csv.DictReader(open("eval/queries.csv", encoding="utf-8")))
    hits = {1: 0, 5: 0, 10: 0}
    for r in rows:
        # lấy 40 kết quả rồi gộp theo sản phẩm (1 sản phẩm có thể có nhiều ảnh)
        res = searcher.search(emb.embed(Image.open(r["file"])), 40)
        ranked = []
        for pid, _ in res:
            if pid not in ranked:
                ranked.append(pid)
        for k in hits:
            hits[k] += r["product_id"] in ranked[:k]
    n = len(rows)
    print(f"Số ảnh query: {n}")
    for k, h in hits.items():
        print(f"Recall@{k} = {h}/{n} = {h / n:.1%}")


if __name__ == "__main__":
    main()
