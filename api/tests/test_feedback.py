"""Test tự động cho tính năng #3 (phản hồi + thu ca sai) và cách chấm eval."""
import csv
import json

import pytest
from PIL import Image

from api import evaluation, feedback

IDS = {"panda_kem", "hoa_xanh_navy", "ke_soc_xam"}


def _luu(tmp_path, top=("panda_kem", "hoa_xanh_navy", "ke_soc_xam")):
    sid = feedback.new_search_id()
    feedback.save_query(tmp_path, sid, Image.new("RGB", (8, 8), "white"),
                        [(p, 0.9 - i * 0.1) for i, p in enumerate(top)])
    return sid


def test_phan_hoi_dung_gan_top1(tmp_path):
    sid = _luu(tmp_path)
    row = feedback.record_feedback(tmp_path, sid, "dung", None, IDS)
    assert row["true_product"] == "panda_kem" and row["rank_that"] == 1
    assert len(feedback.load_feedback(tmp_path)) == 1


def test_phan_hoi_sai_ghi_hang_cua_mau_dung(tmp_path):
    sid = _luu(tmp_path)
    row = feedback.record_feedback(tmp_path, sid, "sai", "ke_soc_xam", IDS)
    assert row["top1"] == "panda_kem" and row["rank_that"] == 3


def test_sai_ma_khong_co_trong_top_thi_hang_none(tmp_path):
    sid = _luu(tmp_path, top=("panda_kem", "hoa_xanh_navy"))
    row = feedback.record_feedback(tmp_path, sid, "sai", "ke_soc_xam", IDS)
    assert row["rank_that"] is None


def test_sai_thieu_ma_dung_bi_tu_choi(tmp_path):
    sid = _luu(tmp_path)
    with pytest.raises(feedback.FeedbackError) as e:
        feedback.record_feedback(tmp_path, sid, "sai", None, IDS)
    assert e.value.status == 422
    assert feedback.load_feedback(tmp_path) == []          # không ghi gì


def test_ma_dung_ngoai_danh_muc_bi_tu_choi(tmp_path):
    sid = _luu(tmp_path)
    with pytest.raises(feedback.FeedbackError):
        feedback.record_feedback(tmp_path, sid, "sai", "mau_la_hoac_go_nham", IDS)


def test_search_id_la_hoac_duong_dan_nguy_hiem(tmp_path):
    with pytest.raises(feedback.FeedbackError) as e1:
        feedback.record_feedback(tmp_path, "../../etc/passwd", "dung", None, IDS)
    assert e1.value.status == 400
    with pytest.raises(feedback.FeedbackError) as e2:
        feedback.record_feedback(tmp_path, "aaaaaaaaaaaa", "dung", None, IDS)
    assert e2.value.status == 404


def test_cham_diem_top5():
    assert evaluation.score_case(["a", "b", "c"], "c", k=5) == (True, 3)
    assert evaluation.score_case(["a", "b", "c", "d", "e", "f"], "f", k=5) == (False, None)


def test_tong_hop_theo_nguon_va_mrr():
    res = [{"source": "sai_that", "passed": False, "rank": None},
           {"source": "sai_that", "passed": True, "rank": 2},
           {"source": "mo_phong", "passed": True, "rank": 1}]
    s = evaluation.summarize(res)
    assert s["n"] == 3 and s["passed"] == 2
    assert s["by_source"]["sai_that"]["rate"] == 0.5
    assert round(s["mrr"], 3) == round((0 + 0.5 + 1) / 3, 3)


def test_nap_ca_eval_tu_choi_nguon_la(tmp_path):
    p = tmp_path / "c.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["case_id", "image", "true_product", "source", "note"])
        w.writerow(["x1", "a.jpg", "panda_kem", "tu_nghi_ra", ""])
    with pytest.raises(ValueError):
        evaluation.load_cases(p)


def test_bao_sai_nhung_ma_dung_trung_hang_1_bi_tu_choi(tmp_path):
    """Lỗi thật gặp khi chạy app 19/11: bấm Sai rồi gõ đúng mã hạng 1 thì từng được ghi nhận."""
    sid = _luu(tmp_path)
    with pytest.raises(feedback.FeedbackError) as e:
        feedback.record_feedback(tmp_path, sid, "sai", "panda_kem", IDS)
    assert e.value.status == 422
    assert feedback.load_feedback(tmp_path) == []
