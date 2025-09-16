from __future__ import annotations
from pathlib import Path
import glob

def discover_inputs(paths: list[str]) -> list[str]:
    files: list[str] = []
    for p in paths:
        if any(c in p for c in "*?[]"):
            files.extend(glob.glob(p))
        else:
            path = Path(p)
            if path.is_dir():
                files.extend(str(x) for x in path.rglob("*") if x.is_file())
            elif path.is_file():
                files.append(str(path))
    # Filtra duplicados e ignora PDFs já no destino se necessário
    return sorted(set(files))
