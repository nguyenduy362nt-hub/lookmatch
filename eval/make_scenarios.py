"""Sinh bộ tình huống kiểm tra độ bền (mô phỏng) từ ảnh catalog.

Mỗi ảnh catalog bị biến đổi giống cách ảnh khách thật hay bị: viền đen kiểu chụp màn hình,
nén JPEG mạnh + thu nhỏ, cắt lệch, xoay nhẹ, tối/sáng, mờ.
Đây là tình huống MÔ PHỎNG: dùng để kiểm tra độ bền, KHÔNG dùng làm kết luận Recall@5 thật.
Chạy: python eval/make_scenarios.py   ->  eval/scenarios/*.jpg + eval/scenarios.csv
"""
import csv
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

CATALOG = Path("data/catalog")
OUT = Path("eval/scenarios")


def black_bars(im):
    w, h = im.size
    canvas = Image.new("RGB", (w, int(h * 1.8)), "black")
    canvas.paste(im, (0, (canvas.height - h) // 2))
    return canvas


def jpeg_low(im):
    small = im.resize((max(1, im.width // 2), max(1, im.height // 2)))
    path = OUT / "_tmp.jpg"
    small.save(path, "JPEG", quality=25)
    return Image.open(path).convert("RGB")


def crop_off(im):
    w, h = im.size
    return im.crop((int(w * 0.15), int(h * 0.1), int(w * 0.85), int(h * 0.8)))


def rotate(im):
    return im.rotate(8, expand=True, fillcolor=(0, 0, 0))


def dark(im):
    return ImageEnhance.Brightness(im).enhance(0.6)


def bright(im):
    return ImageEnhance.Brightness(im).enhance(1.4)


def blur(im):
    return im.filter(ImageFilter.GaussianBlur(3))


VARIANTS = {"vien_den": black_bars, "nen_jpeg": jpeg_low, "cat_lech": crop_off,
            "xoay": rotate, "toi": dark, "sang": bright, "mo": blur}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for prod in sorted(p for p in CATALOG.iterdir() if p.is_dir()):
        imgs = sorted(i for i in prod.glob("*") if i.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})
        if not imgs:
            continue
        base = Image.open(imgs[0]).convert("RGB")
        for name, fn in VARIANTS.items():
            f = OUT / f"{prod.name}__{name}.jpg"
            fn(base).convert("RGB").save(f, "JPEG", quality=90)
            rows.append({"file": str(f).replace("\\", "/"), "product_id": prod.name, "scenario": name})
    (OUT / "_tmp.jpg").unlink(missing_ok=True)
    with open("eval/scenarios.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["file", "product_id", "scenario"])
        w.writeheader()
        w.writerows(rows)
    print(f"Đã tạo {len(rows)} tình huống ({len(VARIANTS)} kiểu x số mẫu) trong eval/scenarios.csv")


if __name__ == "__main__":
    main()
