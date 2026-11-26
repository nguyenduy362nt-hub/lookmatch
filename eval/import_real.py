"""Nhập ảnh khách/ảnh shop mới gửi thành ca eval, GÁN NHÃN BẰNG MANIFEST do em xác nhận.

  python eval/import_real.py [eval/manifest_real.csv]

manifest cột: file, true_product, origin, note
  origin = thuc    : ảnh chụp thật (shop/khách)
  origin = ai_tao  : ảnh do AI tạo hoặc có watermark AI (không tính là ảnh thật)
  true_product trống = mẫu shop không có trong danh mục (đo riêng, không tính Recall)
Nguồn ca được quyết định bằng KẾT QUẢ LẦN ĐẦU hệ thống tìm ảnh này:
  origin=ai_tao -> ai_tao;  top-1 sai -> sai_that;  top-1 đúng -> anh_khach_that.
Giống hệt nhân viên bấm Đúng/Sai, chỉ khác là nhãn đọc từ manifest. Chạy lại không thêm trùng.
"""
import csv
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from api import evaluation  # noqa: E402

FIELDS = ["case_id", "image", "true_product", "source", "note"]


def import_manifest(rows, searcher, embedder, out_csv, real_dir):
    from PIL import Image
    out_csv, real_dir = Path(out_csv), Path(real_dir)
    real_dir.mkdir(parents=True, exist_ok=True)
    cases = []
    if out_csv.exists():
        with open(out_csv, encoding="utf-8", newline="") as f:
            cases = list(csv.DictReader(f))
    have = {c["case_id"] for c in cases}
    report = {"added": 0, "khong_co": [], "thieu_mau": []}
    ids = set(searcher.ids)
    for r in rows:
        stem = Path(r["file"]).stem
        cid = f"real_{stem}"
        true = (r.get("true_product") or "").strip()
        if not true:
            report["khong_co"].append(stem)
            continue
        if true not in ids:
            report["thieu_mau"].append((stem, true))     # chưa build_index sau khi thêm mẫu
            continue
        if cid in have:
            continue
        ranked = []
        for pid, _ in searcher.search(embedder.embed(Image.open(r["file"])), 40):
            if pid not in ranked:
                ranked.append(pid)
        if r.get("origin") == "ai_tao":
            source = "ai_tao"
        else:
            source = "anh_khach_that" if ranked and ranked[0] == true else "sai_that"
        dst = real_dir / f"{cid}.jpg"
        shutil.copy(r["file"], dst)
        rank = ranked.index(true) + 1 if true in ranked else None
        cases.append({"case_id": cid, "image": str(dst).replace("\\", "/"), "true_product": true,
                      "source": source, "note": f"top1 lần đầu={ranked[0] if ranked else ''}; hạng mẫu đúng={rank}; {r.get('note','')}"})
        have.add(cid)
        report["added"] += 1
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(cases)
    return report, cases


if __name__ == "__main__":
    import json

    import numpy as np
    from api.embedder import ClipEmbedder
    from api.search import Searcher
    manifest = sys.argv[1] if len(sys.argv) > 1 else "eval/manifest_real.csv"
    with open(manifest, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    searcher = Searcher(np.load("data/index.npy"), json.loads(Path("data/ids.json").read_text(encoding="utf-8")))
    rep, cases = import_manifest(rows, searcher, ClipEmbedder(), "eval/cases.csv", "eval/real")
    print(f"Thêm {rep['added']} ca. Tổng {len(cases)} ca.")
    if rep["khong_co"]:
        print("Ảnh 'shop không có mẫu này' (không tính Recall):", rep["khong_co"])
    if rep["thieu_mau"]:
        print("CẢNH BÁO mẫu chưa có trong chỉ mục, chạy python eval/build_index.py rồi chạy lại:", rep["thieu_mau"])
    from collections import Counter
    print(dict(Counter(c["source"] for c in cases)))
