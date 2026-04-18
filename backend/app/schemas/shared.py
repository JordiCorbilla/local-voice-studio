from __future__ import annotations

from pydantic import BaseModel


class ProfileDefaults(BaseModel):
    temperature: float = 0.55
    speed: float = 1.0
    length_penalty: float = 1.0
    repetition_penalty: float = 2.2
    top_k: int = 40
    top_p: float = 0.75
    enable_text_splitting: bool = True
