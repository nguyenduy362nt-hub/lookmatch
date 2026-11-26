"""Tính năng #3: nhân viên phản hồi đúng/sai cho từng lượt tìm; ca sai được giữ lại làm dữ liệu eval.

Mỗi lượt /search lưu ảnh truy vấn + top-K vào data/queries/<search_id>.{jpg,json}.
Phản hồi ghi nối vào data/feedback.jsonl (mỗi dòng một JSON). Không gọi mạng ở đây
để test được mà không cần FastAPI/CLIP.
"""
import json
import re
import uuid
from datetime import datetime
from pathlib import Path

VERDICTS = ("dung", "sai", "khong_co")  # đúng top-1 | sai (kèm mã đúng) | shop không có mẫu này
_ID_RE = re.compile(r"^[0-9a-f]{12}$")


class FeedbackError(ValueError):
    """Dữ liệu phản hồi không hợp lệ; .status là mã HTTP gợi ý."""

    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def new_search_id() -> str:
    return uuid.uuid4().hex[:12]


def save_query(data_dir, search_id, image, top):
    """Lưu ảnh (PIL.Image) và top-K của lượt tìm. top = [(mã, điểm), ...]."""
    qdir = Path(data_dir) / "queries"
    qdir.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(qdir / f"{search_id}.jpg", quality=90)
    meta = {"search_id": search_id, "time": datetime.now().isoformat(timespec="seconds"),
            "top": [[pid, round(float(s), 4)] for pid, s in top]}
    (qdir / f"{search_id}.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")


def load_query_meta(data_dir, search_id):
    if not _ID_RE.match(search_id or ""):          # chặn ../ và chuỗi lạ
        raise FeedbackError("search_id không hợp lệ", 400)
    p = Path(data_dir) / "queries" / f"{search_id}.json"
    if not p.exists():
        raise FeedbackError("Không tìm thấy lượt tìm này", 404)
    return json.loads(p.read_text(encoding="utf-8"))


def record_feedback(data_dir, search_id, verdict, true_product, valid_ids):
    """Kiểm tra rồi ghi 1 phản hồi. Trả dict đã ghi (có 'rank_that' = thứ hạng mẫu đúng trong top-K)."""
    if verdict not in VERDICTS:
        raise FeedbackError(f"verdict phải là một trong {VERDICTS}", 422)
    meta = load_query_meta(data_dir, search_id)
    top_ids = [pid for pid, _ in meta["top"]]
    if verdict == "dung":
        true_product = top_ids[0] if top_ids else None
    elif verdict == "sai":
        if not true_product:
            raise FeedbackError("verdict=sai thì phải kèm true_product (mã mẫu đúng)", 422)
        if true_product not in valid_ids:
            raise FeedbackError(f"true_product '{true_product}' không có trong danh mục", 422)
        if top_ids and true_product == top_ids[0]:
            raise FeedbackError("Mã đúng trùng với mẫu hạng 1: kết quả đã đúng, hãy bấm Đúng", 422)
    else:
        true_product = None
    rank = top_ids.index(true_product) + 1 if true_product in top_ids else None
    row = {"time": datetime.now().isoformat(timespec="seconds"), "search_id": search_id,
           "verdict": verdict, "top1": top_ids[0] if top_ids else "",
           "true_product": true_product, "rank_that": rank}
    with (Path(data_dir) / "feedback.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def load_feedback(data_dir):
    p = Path(data_dir) / "feedback.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
