"""Test gom ca sai thật vào bộ eval + chạy eval với embedder giả (không cần CLIP)."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from api import evaluation, feedback
from api.search import Searcher

ROOT = Path(__file__).resolve().parents[2]


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "eval" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_gom_ca_sai_thanh_case_sai_that(tmp_path):
    harvest = _load("harvest_failures")
    sid = feedback.new_search_id()
    feedback.save_query(tmp_path, sid, Image.new("RGB", (8, 8)), [("panda_kem", 0.9), ("ke_soc_xam", 0.8)])
    feedback.record_feedback(tmp_path, sid, "sai", "ke_soc_xam", {"panda_kem", "ke_soc_xam"})
    out = tmp_path / "cases.csv"
    n, cases = harvest.harvest(tmp_path, out, tmp_path / "real")
    assert n == 1 and cases[0]["source"] == "sai_that" and cases[0]["true_product"] == "ke_soc_xam"
    assert (tmp_path / "real" / f"real_{sid}.jpg").exists()
    n2, _ = harvest.harvest(tmp_path, out, tmp_path / "real")      # chạy lại không thêm trùng
    assert n2 == 0
    assert len(evaluation.load_cases(out)) == 1


def test_run_eval_bao_dung_ca_truot(tmp_path):
    run_eval = _load("run_eval")

    class Fake:
        def embed(self, image):          # luôn trả vector của mẫu A
            return np.array([1, 0, 0, 0], dtype="float32")

    searcher = Searcher(np.eye(4), ["A", "B", "C", "D"])
    img = tmp_path / "x.jpg"
    Image.new("RGB", (8, 8)).save(img)
    cases = [{"case_id": "c1", "image": str(img), "true_product": "A", "source": "mo_phong", "note": ""},
             {"case_id": "c2", "image": str(img), "true_product": "D", "source": "sai_that", "note": ""}]
    res = run_eval.run(cases, searcher, Fake(), k=1)
    assert [r["passed"] for r in res] == [True, False]
    assert res[1]["top1"] == "A"


def test_canh_bao_khi_chi_muc_thieu_mau(tmp_path, capsys):
    run_eval = _load("run_eval")

    class Fake:
        def embed(self, image):
            return np.array([1, 0], dtype="float32")

    img = tmp_path / "x.jpg"
    Image.new("RGB", (8, 8)).save(img)
    cases = [{"case_id": "c1", "image": str(img), "true_product": "mau_moi", "source": "sai_that", "note": ""}]
    res = run_eval.run(cases, Searcher(np.eye(2), ["A", "B"]), Fake(), k=5)
    assert res[0]["passed"] is False
    assert "mau_moi" in capsys.readouterr().out


def test_nhap_manifest_gan_nguon_theo_ket_qua_lan_dau(tmp_path):
    imp = _load("import_real")

    class Fake:
        def embed(self, image):          # luôn giống mẫu A nhất
            return np.array([1, 0, 0], dtype="float32")

    searcher = Searcher(np.eye(3), ["A", "B", "C"])
    files = []
    for n in ("dung", "sai", "ai", "khongco"):
        p = tmp_path / f"{n}.jpg"
        Image.new("RGB", (8, 8)).save(p)
        files.append(str(p))
    rows = [{"file": files[0], "true_product": "A", "origin": "thuc", "note": ""},
            {"file": files[1], "true_product": "B", "origin": "thuc", "note": ""},
            {"file": files[2], "true_product": "A", "origin": "ai_tao", "note": ""},
            {"file": files[3], "true_product": "", "origin": "thuc", "note": ""},
            {"file": files[0], "true_product": "Z_moi", "origin": "thuc", "note": ""}]
    rep, cases = imp.import_manifest(rows, searcher, Fake(), tmp_path / "c.csv", tmp_path / "real")
    src = {c["case_id"]: c["source"] for c in cases}
    assert src == {"real_dung": "anh_khach_that", "real_sai": "sai_that", "real_ai": "ai_tao"}
    assert rep["khong_co"] == ["khongco"] and rep["thieu_mau"] == [("dung", "Z_moi")]
    rep2, cases2 = imp.import_manifest(rows, searcher, Fake(), tmp_path / "c.csv", tmp_path / "real")
    assert rep2["added"] == 0 and len(cases2) == 3          # chạy lại không thêm trùng
    assert len(evaluation.load_cases(tmp_path / "c.csv")) == 3


def test_lay_mau_ngau_nhien_ca_mo_phong(tmp_path):
    harvest = _load("harvest_failures")
    sim = tmp_path / "sim.csv"
    sim.write_text("file,product_id,scenario\n" + "".join(f"a{i}.jpg,p{i},xoay\n" for i in range(20)), encoding="utf-8")
    n, cases = harvest.harvest(tmp_path, tmp_path / "c.csv", tmp_path / "real", sim, sample=5)
    assert n == 5 and all(c["source"] == "mo_phong" for c in cases)
    n2, cases2 = harvest.harvest(tmp_path, tmp_path / "c2.csv", tmp_path / "real", sim, sample=5)
    assert [c["case_id"] for c in cases2] == [c["case_id"] for c in cases]      # seed cố định: lần nào cũng cùng 5 ca


def test_chan_doan_do_cosine_ca_nham(tmp_path):
    diag = _load("diagnose")

    class Fake:
        def embed(self, image):
            return np.array([1, 0.2, 0], dtype="float32")   # gần A hơn B

    img = tmp_path / "x.jpg"
    Image.new("RGB", (8, 8)).save(img)
    vecs = np.array([[1, 0, 0], [0.9, 0.5, 0], [0, 0, 1]], dtype="float32")
    cases = [{"case_id": "c1", "image": str(img), "true_product": "B", "source": "sai_that", "note": ""},
             {"case_id": "c2", "image": str(img), "true_product": "A", "source": "sai_that", "note": ""},
             {"case_id": "c3", "image": str(img), "true_product": "B", "source": "mo_phong", "note": ""}]
    rows = diag.diagnose(cases, vecs, ["A", "B", "C"], Fake())
    assert [r["case_id"] for r in rows] == ["c1"]            # c2 đúng, c3 mô phỏng bị bỏ qua
    assert rows[0]["nham"] == "A" and rows[0]["hang_dung"] == 2
    assert rows[0]["cos_nham"] > rows[0]["cos_dung"] and rows[0]["cos_2_mau"] > 0.8
