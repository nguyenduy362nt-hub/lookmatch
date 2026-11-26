"""Tuần 7 – test các biện pháp bảo mật thuần Python (không cần FastAPI/CLIP).

Mỗi test là một đầu vào độc hại hoặc một tình huống tấn công cụ thể, kèm kết quả mong đợi.
"""
import io

import pytest
from PIL import Image

from api import feedback, security


def _png(size=(8, 8), mode="RGB", fmt="PNG"):
    buf = io.BytesIO()
    Image.new(mode, size, "white" if mode == "RGB" else 0).save(buf, fmt)
    return buf.getvalue()


def _loi(data, **kw):
    with pytest.raises(security.SecurityError) as e:
        security.open_safe_image(data, **kw)
    return e.value


# ---------- 1. kiểm tra đầu vào ảnh ----------
def test_anh_hop_le_duoc_nhan():
    assert security.open_safe_image(_png()).size == (8, 8)
    assert security.open_safe_image(_png(fmt="JPEG")).size == (8, 8)


def test_file_rong_bi_chan_400():
    assert _loi(b"").status == 400


def test_van_ban_dat_ten_jpg_bi_chan_400():
    # Kẻ tấn công đổi đuôi .jpg cho một trang HTML/script: ta kiểm tra nội dung nên vẫn chặn
    assert _loi(b"<html><script>alert(1)</script></html>").status == 400


def test_anh_qua_dung_luong_bi_chan_413():
    assert _loi(_png(), max_bytes=10).status == 413


def test_dinh_dang_khong_cho_phep_bi_chan_415():
    assert _loi(_png(fmt="GIF")).status == 415
    assert _loi(_png(fmt="BMP")).status == 415


def test_anh_qua_nhieu_diem_anh_bi_chan_413():
    # PNG đơn sắc 8000x8000 = 64 triệu điểm ảnh: file nhỏ nhưng giải nén rất tốn RAM
    assert _loi(_png((8000, 8000), mode="1"), max_pixels=40_000_000).status == 413


def test_bom_giai_nen_bi_chan_413_truoc_khi_giai_nen():
    # 20000x20000 = 400 triệu điểm ảnh, vượt cả ngưỡng cứng của Pillow
    assert _loi(_png((20000, 20000), mode="1")).status == 413


def test_anh_bi_cat_cut_bi_chan_400():
    assert _loi(_png((64, 64), fmt="JPEG")[:200]).status == 400


# ---------- 2. giới hạn tần suất ----------
class _Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def test_gioi_han_tan_suat_chan_sau_n_lan_va_mo_lai_sau_cua_so():
    clk = _Clock()
    rl = security.RateLimiter(max_calls=3, window_s=60, clock=clk)
    assert [rl.check("1.1.1.1")[0] for _ in range(3)] == [True, True, True]
    ok, retry = rl.check("1.1.1.1")
    assert ok is False and 1 <= retry <= 61
    clk.t += 61
    assert rl.check("1.1.1.1")[0] is True


def test_gioi_han_tan_suat_tach_theo_tung_ip():
    rl = security.RateLimiter(max_calls=1, window_s=60, clock=_Clock())
    assert rl.check("a")[0] is True
    assert rl.check("a")[0] is False
    assert rl.check("b")[0] is True          # IP khác không bị ảnh hưởng


def test_gioi_han_tan_suat_khong_phinh_bo_nho_khi_doi_ip_lien_tuc():
    clk = _Clock()
    rl = security.RateLimiter(max_calls=5, window_s=60, clock=clk, max_keys=100)
    for i in range(1000):
        clk.t += 0.01
        rl.check(f"ip-{i}")
    assert len(rl._hits) <= 100


# ---------- 3. khoá API ----------
def test_khoa_api_chua_bat_thi_cho_qua():
    assert security.check_api_key(None, "") is True


def test_khoa_api_thieu_hoac_sai_bi_tu_choi():
    assert security.check_api_key(None, "abc") is False
    assert security.check_api_key("", "abc") is False
    assert security.check_api_key("abd", "abc") is False
    assert security.check_api_key("abc ", "abc") is False


def test_khoa_api_dung_duoc_nhan_ke_ca_ky_tu_tieng_viet():
    assert security.check_api_key("abc", "abc") is True
    assert security.check_api_key("mật-khẩu", "mật-khẩu") is True


# ---------- 4. làm sạch ô Sheet ----------
def test_ten_file_chua_cong_thuc_bi_vo_hieu():
    assert security.safe_cell('=HYPERLINK("http://evil.example","x").jpg').startswith("'=")
    assert security.safe_cell("+cmd|' /C calc'!A0").startswith("'+")
    assert security.safe_cell("@SUM(1+1)").startswith("'@")
    assert security.safe_cell("-2+3").startswith("'-")


def test_ten_file_binh_thuong_giu_nguyen_va_cat_do_dai_va_bo_ky_tu_dieu_khien():
    assert security.safe_cell("anh_khach.jpg") == "anh_khach.jpg"
    assert security.safe_cell("a\r\nb\x00c") == "a  b c"
    assert len(security.safe_cell("x" * 500)) == 100
    assert security.safe_cell(None) == ""


# ---------- 5. cấu hình từ biến môi trường ----------
def test_cau_hinh_mac_dinh():
    s = security.Settings.from_env({})
    assert s.api_key == "" and s.cors_origins == ("*",) and s.rate_limit == 60 and s.trust_proxy is False


def test_cau_hinh_doc_tu_moi_truong_va_bo_qua_gia_tri_hong():
    s = security.Settings.from_env({"LOOKMATCH_API_KEY": " k ", "LOOKMATCH_CORS_ORIGINS": "http://a, http://b",
                                    "LOOKMATCH_RATE_LIMIT": "abc", "LOOKMATCH_RATE_WINDOW": "-5",
                                    "LOOKMATCH_TRUST_PROXY": "true"})
    assert s.api_key == "k" and s.cors_origins == ("http://a", "http://b")
    assert s.rate_limit == 60 and s.rate_window == 60 and s.trust_proxy is True


# ---------- lọc dữ liệu cá nhân trong ảnh lưu lại ----------
def test_anh_luu_lai_khong_con_exif_gps(tmp_path):
    img = Image.new("RGB", (16, 16), "white")
    exif = Image.Exif()
    exif[0x010F] = "HangDienThoai"          # Make
    gps = exif.get_ifd(0x8825)              # GPS IFD
    gps[1], gps[2] = "N", (10.0, 46.0, 0.0)
    buf = io.BytesIO()
    img.save(buf, "JPEG", exif=exif)
    goc = Image.open(io.BytesIO(buf.getvalue()))
    assert len(goc.getexif()) > 0           # ảnh gốc có EXIF thật

    sid = feedback.new_search_id()
    feedback.save_query(tmp_path, sid, goc, [("panda_kem", 0.9)])
    luu = Image.open(tmp_path / "queries" / f"{sid}.jpg")
    assert len(luu.getexif()) == 0          # bản lưu đã sạch EXIF/GPS
