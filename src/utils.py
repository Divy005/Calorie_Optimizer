# src/utils.py

from pathlib import Path
from typing import Union

PathLike = Union[str, Path]


def ensure_dir(path: PathLike) -> None:
    """
    Ensure that a directory exists. If it does not exist, create it.
    """
    p = Path(path)
    if not p.exists():
        p.mkdir(parents=True, exist_ok=True)


def project_root() -> Path:
    """
    Return the root directory of the project (where main.py is located).
    """
    return Path(__file__).resolve().parents[1]
