import os
import hashlib
from dataclasses import dataclass

@dataclass
class FileMeta:
    path: str
    sha256: str
    size: int
    mtime: float
    language: str

def detect_language(path: str) -> str:
    if path.endswith(".py"):
        return "python"
    return "unknown"

def file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def scan_repo(root: str):
    metas = []
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            p = os.path.join(dirpath, name)
            lang = detect_language(p)
            if lang == "unknown":
                continue
            st = os.stat(p)
            metas.append(FileMeta(
                path=p,
                sha256=file_hash(p),
                size=st.st_size,
                mtime=st.st_mtime,
                language=lang
            ))
    return metas

