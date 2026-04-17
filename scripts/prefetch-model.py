from __future__ import annotations

import sys


def main() -> int:
    try:
        from TTS.api import TTS
    except Exception as exc:
        print(f"Unable to import Coqui TTS: {exc}")
        return 1

    model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
    print(f"Prefetching {model_name}...")
    TTS(model_name, progress_bar=True)
    print("Model ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
