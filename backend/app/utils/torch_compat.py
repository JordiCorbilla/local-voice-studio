from __future__ import annotations

import inspect
from typing import Any


def patch_torch_load_for_coqui(torch_module: Any) -> None:
    """Restore pre-2.6 torch.load behavior for trusted Coqui checkpoints."""
    current = torch_module.load
    if getattr(current, "__lvs_patched__", False):
        return

    try:
        signature = inspect.signature(current)
    except (TypeError, ValueError):
        return

    if "weights_only" not in signature.parameters:
        return

    def wrapped(*args: Any, **kwargs: Any):
        kwargs.setdefault("weights_only", False)
        return current(*args, **kwargs)

    wrapped.__lvs_patched__ = True  # type: ignore[attr-defined]
    torch_module.load = wrapped
