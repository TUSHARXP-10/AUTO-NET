import json
import urllib.request

def _post(url: str, payload: dict) -> bytes:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return r.read()

def start_index(repo_path: str) -> bytes:
    return _post("http://127.0.0.1:8000/index/start", {"repo_path": repo_path})

def create_task(description: str) -> bytes:
    return _post("http://127.0.0.1:8000/tasks", {"description": description})

