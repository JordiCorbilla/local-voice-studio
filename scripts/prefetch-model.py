from __future__ import annotations

import sys


def main() -> int:
    try:
        import torch
        from TTS.api import TTS
    except Exception as exc:
        print(f"Unable to import Coqui TTS: {exc}")
        return 1

    root = __file__
    from pathlib import Path

    backend_dir = Path(root).resolve().parents[1] / "backend"
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    from app.utils.torch_compat import patch_torch_load_for_coqui

    patch_torch_load_for_coqui(torch)

    model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
    print(f"Prefetching {model_name}...")
    TTS(model_name, progress_bar=True)
    print("Model ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
