import os
import sqlite3
from typing import Optional

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "devcopilot.db")

def ensure_db() -> sqlite3.Connection:
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS files (id INTEGER PRIMARY KEY, path TEXT UNIQUE, sha256 TEXT, size INTEGER, mtime REAL, language TEXT)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS symbols (id INTEGER PRIMARY KEY, file_id INTEGER, kind TEXT, name TEXT, start_line INTEGER, end_line INTEGER, FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE CASCADE)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS chunks (id INTEGER PRIMARY KEY, file_id INTEGER, start_line INTEGER, end_line INTEGER, text_hash TEXT, FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE CASCADE)"
    )
    return conn

def upsert_file(conn: sqlite3.Connection, path: str, sha256: str, size: int, mtime: float, language: str) -> int:
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO files(path, sha256, size, mtime, language) VALUES(?,?,?,?,?) ON CONFLICT(path) DO UPDATE SET sha256=excluded.sha256, size=excluded.size, mtime=excluded.mtime, language=excluded.language",
        (path, sha256, size, mtime, language),
    )
    cur.execute("SELECT id FROM files WHERE path=?", (path,))
    return cur.fetchone()[0]

def insert_symbol(conn: sqlite3.Connection, file_id: int, kind: str, name: str, start_line: int, end_line: int) -> None:
    conn.execute(
        "INSERT INTO symbols(file_id, kind, name, start_line, end_line) VALUES(?,?,?,?,?)",
        (file_id, kind, name, start_line, end_line),
    )

def delete_symbols_for_file(conn: sqlite3.Connection, file_id: int) -> None:
    conn.execute("DELETE FROM symbols WHERE file_id=?", (file_id,))

def delete_chunks_for_file(conn: sqlite3.Connection, file_id: int) -> None:
    conn.execute("DELETE FROM chunks WHERE file_id=?", (file_id,))

def count_files(conn: sqlite3.Connection) -> int:
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM files")
    return cur.fetchone()[0]

def get_file_id_by_path(conn: sqlite3.Connection, path: str) -> Optional[int]:
    cur = conn.cursor()
    cur.execute("SELECT id FROM files WHERE path=?", (path,))
    row = cur.fetchone()
    return row[0] if row else None

def get_symbols_by_file_id(conn: sqlite3.Connection, file_id: int):
    cur = conn.cursor()
    cur.execute("SELECT kind, name, start_line, end_line FROM symbols WHERE file_id=? ORDER BY start_line", (file_id,))
    return [{"kind": k, "name": n, "start_line": s, "end_line": e} for k, n, s, e in cur.fetchall()]

def insert_chunk(conn: sqlite3.Connection, file_id: int, start_line: int, end_line: int, text_hash: str) -> int:
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO chunks(file_id, start_line, end_line, text_hash) VALUES(?,?,?,?)",
        (file_id, start_line, end_line, text_hash),
    )
    return cur.lastrowid

def get_chunk_by_id(conn: sqlite3.Connection, chunk_id: int):
    cur = conn.cursor()
    cur.execute(
        "SELECT files.path, chunks.start_line, chunks.end_line FROM chunks JOIN files ON files.id = chunks.file_id WHERE chunks.id=?",
        (chunk_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    return {"path": row[0], "start_line": row[1], "end_line": row[2]}

def search_files(conn: sqlite3.Connection, query: str):
    cur = conn.cursor()
    q = f"%{query}%"
    cur.execute("SELECT path, language, size, mtime FROM files WHERE path LIKE ? ORDER BY path LIMIT 100", (q,))
    return [{"path": p, "language": l, "size": sz, "mtime": mt} for p, l, sz, mt in cur.fetchall()]

def search_symbols(conn: sqlite3.Connection, query: str):
    cur = conn.cursor()
    q = f"%{query}%"
    cur.execute(
        "SELECT files.path, symbols.kind, symbols.name, symbols.start_line, symbols.end_line FROM symbols JOIN files ON files.id = symbols.file_id WHERE symbols.name LIKE ? ORDER BY files.path, symbols.start_line LIMIT 200",
        (q,),
    )
    return [
        {"path": p, "kind": k, "name": n, "start_line": s, "end_line": e}
        for p, k, n, s, e in cur.fetchall()
    ]
