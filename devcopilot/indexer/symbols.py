import ast
from dataclasses import dataclass
from typing import List

@dataclass
class SymbolMeta:
    kind: str
    name: str
    start_line: int
    end_line: int

def extract_symbols(file_path: str) -> List[SymbolMeta]:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        src = f.read()
    tree = ast.parse(src)
    symbols: List[SymbolMeta] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            end = getattr(node, 'end_lineno', node.lineno)
            symbols.append(SymbolMeta(kind="function", name=node.name, start_line=node.lineno, end_line=end))
        elif isinstance(node, ast.AsyncFunctionDef):
            end = getattr(node, 'end_lineno', node.lineno)
            symbols.append(SymbolMeta(kind="function", name=node.name, start_line=node.lineno, end_line=end))
        elif isinstance(node, ast.ClassDef):
            end = getattr(node, 'end_lineno', node.lineno)
            symbols.append(SymbolMeta(kind="class", name=node.name, start_line=node.lineno, end_line=end))
    return symbols

