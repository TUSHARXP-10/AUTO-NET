import os
import numpy as np
import faiss

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
INDEX_PATH = os.path.join(DATA_DIR, "faiss.index")

def ensure_index(dim: int):
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(INDEX_PATH):
        return faiss.read_index(INDEX_PATH)
    base = faiss.IndexFlatIP(dim)
    idx = faiss.IndexIDMap2(base)
    return idx

def save_index(index):
    faiss.write_index(index, INDEX_PATH)

def reset_index(dim: int):
    os.makedirs(DATA_DIR, exist_ok=True)
    base = faiss.IndexFlatIP(dim)
    idx = faiss.IndexIDMap2(base)
    save_index(idx)
    return idx

def _normalize(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v, axis=1, keepdims=True) + 1e-12
    return v / n

def add_vectors(index, ids: np.ndarray, vectors: np.ndarray):
    index.add_with_ids(_normalize(vectors.astype(np.float32)), ids.astype(np.int64))

def search(index, vectors: np.ndarray, top_k: int):
    D, I = index.search(_normalize(vectors.astype(np.float32)), top_k)
    return D, I
