from fastapi import FastAPI
from pydantic import BaseModel
from dataclasses import asdict
from devcopilot.indexer.scanner import scan_repo
from devcopilot.indexer.symbols import extract_symbols
from devcopilot.indexer.embedder import encode_texts
from devcopilot.search.faiss_store import ensure_index, add_vectors, save_index, search as faiss_search, reset_index
from devcopilot.utils.db import ensure_db, upsert_file, insert_symbol, delete_symbols_for_file, count_files, get_file_id_by_path, get_symbols_by_file_id, search_files, search_symbols, delete_chunks_for_file, insert_chunk, get_chunk_by_id
from devcopilot.runner.pytest_runner import run_pytest
from devcopilot.git.git_ops import status as git_status, current_branch, create_branch, commit_all, apply_patch_preview, apply_patch

app = FastAPI()
_index_state = {"repo": None, "files": [], "count": 0}

class IndexReq(BaseModel):
    repo_path: str

class TaskReq(BaseModel):
    description: str

class PatchReq(BaseModel):
    repo_path: str = "."
    patch_text: str

class PatchApplyReq(BaseModel):
    repo_path: str = "."
    patch_text: str
    confirm: bool = False
    index: bool = False

@app.post("/index/start")
def index_start(req: IndexReq):
    conn = ensure_db()
    fresh_index = None
    metas = scan_repo(req.repo_path)
    for m in metas:
        file_id = upsert_file(conn, m.path, m.sha256, m.size, m.mtime, m.language)
        delete_symbols_for_file(conn, file_id)
        delete_chunks_for_file(conn, file_id)
        if m.language == "python":
            for sym in extract_symbols(m.path):
                insert_symbol(conn, file_id, sym.kind, sym.name, sym.start_line, sym.end_line)
        with open(m.path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        if len(lines) == 0:
            continue
        chunks = []
        if m.language == "python":
            syms = get_symbols_by_file_id(conn, file_id)
            if syms:
                for s in syms:
                    start = max(1, s["start_line"]) if isinstance(s["start_line"], int) else 1
                    end = max(start, s["end_line"]) if isinstance(s["end_line"], int) else start
                    text = "".join(lines[start-1:end])
                    if text.strip():
                        chunks.append((start, end, text))
        if not chunks:
            text = "".join(lines)
            chunks.append((1, len(lines), text))
        import hashlib
        vecs = encode_texts([c[2] for c in chunks])
        if fresh_index is None:
            fresh_index = reset_index(vecs.shape[1])
        index = ensure_index(vecs.shape[1])
        ids = []
        for (start, end, text), vec in zip(chunks, vecs):
            h = hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()
            cid = insert_chunk(conn, file_id, start, end, h)
            ids.append(cid)
        import numpy as np
        add_vectors(index, np.array(ids, dtype=np.int64), vecs)
        save_index(index)
    conn.commit()
    _index_state["repo"] = req.repo_path
    _index_state["files"] = metas
    _index_state["count"] = count_files(conn)
    sample = [asdict(m) for m in metas[:10]]
    return {"status": "completed", "repo": req.repo_path, "count": _index_state["count"], "sample": sample}

@app.get("/index/status")
def index_status():
    conn = ensure_db()
    return {"repo": _index_state["repo"], "count": count_files(conn)}

@app.get("/symbols")
def get_symbols(path: str):
    conn = ensure_db()
    fid = get_file_id_by_path(conn, path)
    if fid is None:
        return {"symbols": []}
    return {"symbols": get_symbols_by_file_id(conn, fid)}

@app.get("/files/search")
def files_search(query: str):
    conn = ensure_db()
    return {"files": search_files(conn, query)}

@app.get("/symbols/search")
def symbols_search(query: str):
    conn = ensure_db()
    return {"symbols": search_symbols(conn, query)}

@app.get("/search")
def combined_search(query: str, limit: int = 50):
    conn = ensure_db()
    files = search_files(conn, query)
    symbols = search_symbols(conn, query)
    def score(entry):
        q = query.lower()
        if entry.get("type") == "symbol":
            name = entry.get("name", "").lower()
            if name == q:
                return 100
            if q in name:
                return 80
        path = entry.get("path", "").lower()
        base = path.split("\\")[-1].split("/")[-1]
        if base == q:
            return 70
        if q in base:
            return 60
        if q in path:
            return 50
        return 0
    combined = ([{**f, "type": "file"} for f in files] + [{**s, "type": "symbol"} for s in symbols])
    combined.sort(key=score, reverse=True)
    return {"results": combined[:limit]}

@app.get("/search/semantic")
def semantic_search(query: str, top_k: int = 10):
    vec = encode_texts([query])
    index = ensure_index(vec.shape[1])
    D, I = faiss_search(index, vec, top_k)
    conn = ensure_db()
    results = []
    for score, cid in zip(D[0].tolist(), I[0].tolist()):
        if cid == -1:
            continue
        meta = get_chunk_by_id(conn, int(cid))
        if meta:
            results.append({"path": meta["path"], "start_line": meta["start_line"], "end_line": meta["end_line"], "score": float(score)})
    return {"results": results}

@app.post("/tasks")
def tasks_create(req: TaskReq):
    return {"id": 1, "status": "pending", "description": req.description}

@app.post("/tests/run")
def tests_run(repo_path: str = ".", command: str = "pytest -q"):
    return run_pytest(repo_path, command)

@app.get("/git/status")
def api_git_status(repo_path: str = "."):
    return git_status(repo_path)

@app.post("/git/branch")
def api_git_branch(repo_path: str = ".", name: str = "devcopilot-task"):
    return create_branch(repo_path, name)

@app.post("/git/commit")
def api_git_commit(repo_path: str = ".", message: str = "devcopilot change"):
    return commit_all(repo_path, message)

@app.get("/git/branch/current")
def api_git_branch_current(repo_path: str = "."):
    return {"branch": current_branch(repo_path)}
@app.post("/patch/preview")
def api_patch_preview(req: PatchReq):
    return apply_patch_preview(req.repo_path, req.patch_text)

@app.post("/patch/apply")
def api_patch_apply(req: PatchApplyReq):
    if not req.confirm:
        return {"error": "approval_required", "message": "Set confirm=true to apply"}
    return apply_patch(req.repo_path, req.patch_text, req.index)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
