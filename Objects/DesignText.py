from typing import Tuple

from Objects.DesignObj import DesignObj


class DesignText(DesignObj):
    def __init__(self, *, text: str, font: str, size: int, color: Tuple[float, float, float, float], **kwargs):
        super().__init__(**kwargs)
        self.text: str = text
        self.font: str = font
        self.size: int = size
        self.color: Tuple[float, float, float, float] = color
