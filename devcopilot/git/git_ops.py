import subprocess
import os

def _run(args, cwd):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, shell=False)

def _run_with_input(args, cwd, input_text):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, shell=False, input=input_text)

def status(repo_path: str) -> dict:
    cwd = os.path.abspath(repo_path)
    proc = _run(["git", "status", "--porcelain"], cwd)
    return {"stdout": proc.stdout, "stderr": proc.stderr, "return_code": proc.returncode}

def current_branch(repo_path: str) -> str:
    cwd = os.path.abspath(repo_path)
    proc = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd)
    return proc.stdout.strip()

def create_branch(repo_path: str, name: str) -> dict:
    cwd = os.path.abspath(repo_path)
    proc = _run(["git", "checkout", "-b", name], cwd)
    return {"stdout": proc.stdout, "stderr": proc.stderr, "return_code": proc.returncode}

def commit_all(repo_path: str, message: str) -> dict:
    cwd = os.path.abspath(repo_path)
    add = _run(["git", "add", "-A"], cwd)
    if add.returncode != 0:
        return {"stdout": add.stdout, "stderr": add.stderr, "return_code": add.returncode}
    proc = _run(["git", "commit", "-m", message], cwd)
    return {"stdout": proc.stdout, "stderr": proc.stderr, "return_code": proc.returncode}

def apply_patch_preview(repo_path: str, patch_text: str) -> dict:
    cwd = os.path.abspath(repo_path)
    args = ["git", "apply", "--check", "--stat", "--numstat", "--summary", "-"]
    proc = _run_with_input(args, cwd, patch_text)
    files = []
    for line in proc.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) == 3:
            added, deleted, path = parts
            files.append({"path": path, "added": added, "deleted": deleted})
    return {"stdout": proc.stdout, "stderr": proc.stderr, "return_code": proc.returncode, "files": files}

def apply_patch(repo_path: str, patch_text: str, index: bool = False) -> dict:
    cwd = os.path.abspath(repo_path)
    args = ["git", "apply"]
    if index:
        args.append("--index")
    args.append("-")
    proc = _run_with_input(args, cwd, patch_text)
    return {"stdout": proc.stdout, "stderr": proc.stderr, "return_code": proc.returncode}
