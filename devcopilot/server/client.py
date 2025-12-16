import json
import urllib.request
import urllib.error
import urllib.parse

def _post(url: str, payload: dict) -> bytes:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.read()

def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.read()

def start_index(repo_path: str) -> bytes:
    return _post("http://127.0.0.1:8000/index/start", {"repo_path": repo_path})

def create_task(description: str) -> bytes:
    return _post("http://127.0.0.1:8000/tasks", {"description": description})

def current_branch(repo_path: str = ".") -> bytes:
    q = urllib.parse.quote(repo_path)
    return _get(f"http://127.0.0.1:8000/git/branch/current?repo_path={q}")
