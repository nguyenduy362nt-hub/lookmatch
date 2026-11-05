"""Lõi tìm kiếm: cosine trên vector đã chuẩn hoá L2 (ADR-3).

Dùng FAISS IndexFlatIP nếu cài được faiss; không thì dùng numpy.
Với chỉ mục Flat hai cách cho kết quả giống hệt nhau (tích vô hướng, quét toàn bộ).
"""
import numpy as np

try:
    import faiss  # type: ignore
except ImportError:  # pragma: no cover
    faiss = None


def normalize(v):
    """Chuẩn hoá L2 theo hàng. Vector toàn 0 gây ValueError."""
    v = np.asarray(v, dtype="float32")
    single = v.ndim == 1
    if single:
        v = v[None, :]
    norms = np.linalg.norm(v, axis=1, keepdims=True)
    if np.any(norms == 0):
        raise ValueError("vector có độ dài 0")
    v = v / norms
    return v[0] if single else v


class Searcher:
    def __init__(self, vectors, ids):
        vectors = normalize(vectors)
        if vectors.ndim != 2:
            raise ValueError(f"vectors phải có dạng (n, d), nhận được {vectors.shape}")
        if len(ids) != len(vectors):
            raise ValueError("số id khác số vector")
        self.ids = list(ids)
        self.dim = vectors.shape[1]
        self._vectors = np.ascontiguousarray(vectors)
        self._index = None
        if faiss is not None:
            self._index = faiss.IndexFlatIP(self.dim)
            self._index.add(self._vectors)

    def search(self, query, k=10):
        """Trả về list[(id, điểm cosine)] giảm dần; tối đa k phần tử."""
        if k <= 0:
            raise ValueError("k phải > 0")
        q = normalize(np.asarray(query, dtype="float32"))
        if q.shape[0] != self.dim:
            raise ValueError("sai số chiều vector")
        k = min(k, len(self.ids))
        if self._index is not None:
            scores, idx = self._index.search(q[None, :], k)
            pairs = zip(idx[0], scores[0])
        else:
            scores = self._vectors @ q
            top = np.argsort(-scores)[:k]
            pairs = ((i, scores[i]) for i in top)
        return [(self.ids[int(i)], float(s)) for i, s in pairs]
