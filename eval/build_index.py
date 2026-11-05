"""Nạp danh mục: data/catalog/<ma_mau>/*.jpg  ->  data/index.npy + data/ids.json

Chạy: python eval/build_index.py
Mỗi thư mục con là 1 sản phẩm (tên thư mục = mã mẫu). Mỗi ảnh là 1 vector.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from api.embedder import ClipEmbedder  # noqa: E402
from api.search import normalize  # noqa: E402

CATALOG = Path("data/catalog")
OUT = Path("data")


def main():
    emb = ClipEmbedder()
    vecs, ids = [], []
    for prod in sorted(p for p in CATALOG.iterdir() if p.is_dir()):
        for img in sorted(prod.glob("*")):
            if img.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
                continue
            vecs.append(emb.embed(Image.open(img)))
            ids.append(prod.name)
            print("embed", prod.name, img.name)
    OUT.mkdir(exist_ok=True)
    np.save(OUT / "index.npy", normalize(np.stack(vecs)))
    (OUT / "ids.json").write_text(json.dumps(ids, ensure_ascii=False), encoding="utf-8")
    print(f"Xong: {len(ids)} ảnh, {len(set(ids))} sản phẩm")


if __name__ == "__main__":
    main()
