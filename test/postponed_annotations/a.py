from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class A:
    p: Path | None
