import subprocess
import shlex
import os
import sys

def run_pytest(repo_path: str, command: str = "pytest -q") -> dict:
    cwd = os.path.abspath(repo_path)
    args = shlex.split(command)
    try:
        proc = subprocess.run(args, cwd=cwd, capture_output=True, text=True, shell=False)
    except Exception:
        proc = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=cwd, capture_output=True, text=True, shell=False)
    out = proc.stdout
    err = proc.stderr
    code = proc.returncode
    summary = {}
    last = out.strip().splitlines()[-1] if out.strip() else ""
    summary["last_line"] = last
    summary["return_code"] = code
    return {"ok": code == 0, "summary": summary, "stdout": out, "stderr": err}

