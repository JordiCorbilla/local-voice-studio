from __future__ import annotations

import json
from typing import Any


def dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=True)


def loads(value: str | None, default: Any):
    if not value:
        return default
    return json.loads(value)
