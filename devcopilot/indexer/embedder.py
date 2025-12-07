from typing import List
import os
import numpy as np

_model = None

def _load_model():
    global _model
    if _model is not None:
        return _model
    os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
    os.environ.setdefault("TRANSFORMERS_NO_JAX", "1")
    os.environ.setdefault("TRANSFORMERS_NO_FLAX", "1")
    from sentence_transformers import SentenceTransformer
    try:
        _model = SentenceTransformer("jina-embeddings-v2-base-code")
    except Exception:
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model

def encode_texts(texts: List[str]) -> np.ndarray:
    m = _load_model()
    vecs = m.encode(texts, convert_to_numpy=True, normalize_embeddings=False)
    return vecs.astype(np.float32)
