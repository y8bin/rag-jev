from __future__ import annotations

import hashlib
import json
import os
import platform
from pathlib import Path
from typing import Any, Iterable
from functools import lru_cache


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def read_jsonl(path: str | Path) -> list[dict]:
    result = []
    with Path(path).open(encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if line.strip():
                try:
                    result.append(json.loads(line))
                except json.JSONDecodeError as e:
                    raise ValueError(f"{path}:{i}: invalid JSON") from e
    return result


def write_json(path: str | Path, value: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    temp = p.with_name(p.name + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    os.replace(temp, p)


def write_jsonl(path: str | Path, rows: Iterable[dict]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    temp = p.with_name(p.name + ".tmp")
    with temp.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
    os.replace(temp, p)


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def file_hash(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def environment_manifest() -> dict:
    from importlib.metadata import version, PackageNotFoundError
    versions = {}
    for name in ["legal-rag-jev", "numpy", "qdrant-client", "httpx", "pydantic", "tiktoken", "sentence-transformers"]:
        try:
            versions[name] = version(name)
        except PackageNotFoundError:
            pass
    return {"python": platform.python_version(), "platform": platform.platform(), "dependencies": versions}


@lru_cache(maxsize=1)
def implementation_digest() -> str:
    return digest({p.name: file_hash(p) for p in sorted(Path(__file__).parent.glob("*.py"))})
