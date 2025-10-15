# structures.py
from dataclasses import dataclass
from typing import Tuple

@dataclass
class Rect:
    x: float
    y: float
    w: float
    h: float

    def overlap(self, other: "Rect") -> bool:
        return not (self.x + self.w <= other.x or
                    other.x + other.w <= self.x or
                    self.y + self.h <= other.y or
                    other.y + other.h <= self.y)

    def center(self) -> Tuple[float, float]:
        return self.x + self.w / 2.0, self.y + self.h / 2.0