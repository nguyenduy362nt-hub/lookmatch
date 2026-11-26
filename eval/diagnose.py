"""Chẩn đoán ca trượt top-1: đo độ giống (cosine) của ảnh truy vấn với mẫu đúng và mẫu bị nhầm.

  python eval/diagnose.py [eval/cases.csv]

In ra, cho mỗi ca thật có top-1 sai:
  cos_dung  = độ giống của ảnh truy vấn với ảnh catalog của mẫu ĐÚNG
  cos_nham  = độ giống với ảnh catalog của mẫu bị NHẦM (top-1)
  cos_2_mau = độ giống GIỮA hai ảnh catalog đó (cao nghĩa là hai mẫu vốn rất giống nhau trong mắt CLIP)
Ghi thêm eval/diagnose.md. Dùng làm bằng chứng nguyên nhân cho bảng lỗi tiêu biểu.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from api import evaluation  # noqa: E402
from api.search import normalize  # noqa: E402


def diagnose(cases, vectors, ids, embedder):
    vectors = normalize(vectors)
    first = {}
    for i, pid in enumerate(ids):
        first.setdefault(pid, i)            # vector đầu tiên của mỗi mẫu
    out = []
    for c in cases:
        if c["source"] == "mo_phong":
            continue
        q = normalize(embedder.embed(Image.open(c["image"])))
        sims = vectors @ q
        best = {}
        for i, pid in enumerate(ids):
            best[pid] = max(best.get(pid, -1.0), float(sims[i]))
        ranked = sorted(best, key=best.get, reverse=True)
        top1, true = ranked[0], c["true_product"]
        if top1 == true:
            continue
        out.append({"case_id": c["case_id"], "source": c["source"], "dung": true, "nham": top1,
                    "hang_dung": ranked.index(true) + 1 if true in ranked else None,
                    "cos_dung": best.get(true), "cos_nham": best[top1],
                    "cos_2_mau": float(vectors[first[true]] @ vectors[first[top1]])})
    return out


if __name__ == "__main__":
    import numpy as np
    from api.embedder import ClipEmbedder
    cases = evaluation.load_cases(sys.argv[1] if len(sys.argv) > 1 else "eval/cases.csv")
    rows = diagnose(cases, np.load("data/index.npy"),
                    json.loads(Path("data/ids.json").read_text(encoding="utf-8")), ClipEmbedder())
    L = ["| case_id | nguồn | mẫu đúng | mẫu bị nhầm | hạng mẫu đúng | cos_dung | cos_nham | cos_2_mau |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['case_id']} | {r['source']} | {r['dung']} | {r['nham']} | {r['hang_dung']} | "
                 f"{r['cos_dung']:.3f} | {r['cos_nham']:.3f} | {r['cos_2_mau']:.3f} |")
    text = "\n".join(L)
    print(text)
    Path("eval/diagnose.md").write_text(text + "\n", encoding="utf-8")
