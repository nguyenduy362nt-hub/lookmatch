"""Cách chấm eval (thuần Python, không cần mô hình): một ca ĐẠT khi mẫu đúng nằm trong top-K."""
import csv
from collections import defaultdict
from pathlib import Path

SOURCES = ("sai_that", "anh_khach_that", "ai_tao", "mo_phong")  # nguồn gốc ca (ai_tao = ảnh do AI tạo/có watermark AI); ghi rõ để không "độn" số liệu


def score_case(ranked_ids, true_id, k=5):
    """Đạt nếu true_id có trong k mã đầu. Trả (đạt: bool, hạng: int|None)."""
    top = list(ranked_ids)[:k]
    if true_id in top:
        return True, top.index(true_id) + 1
    return False, None


def load_cases(csv_path):
    """CSV cột: case_id, image, true_product, source, note."""
    rows = []
    with open(csv_path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r.get("source") not in SOURCES:
                raise ValueError(f"Ca {r.get('case_id')}: source phải thuộc {SOURCES}")
            rows.append(r)
    ids = [r["case_id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("case_id bị trùng")
    return rows


def summarize(results):
    """results: list dict có 'source','passed','rank'. Trả tổng + theo nguồn + MRR."""
    by = defaultdict(lambda: [0, 0])
    rr = 0.0
    for r in results:
        by[r["source"]][1] += 1
        by[r["source"]][0] += 1 if r["passed"] else 0
        rr += 1.0 / r["rank"] if r.get("rank") else 0.0
    n = len(results)
    ok = sum(v[0] for v in by.values())
    return {"n": n, "passed": ok, "rate": (ok / n) if n else 0.0,
            "mrr": (rr / n) if n else 0.0,
            "by_source": {s: {"passed": v[0], "n": v[1], "rate": v[0] / v[1]} for s, v in by.items()}}
