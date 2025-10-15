# park.py
import math
import random
from typing import List, Tuple

from rides import Ride
from patron import Patron

class Park:
    def __init__(self, width: float = 100.0, height: float = 70.0):
        self.width = float(width)
        self.height = float(height)
        self.rides: List[Ride] = []
        self.entrances: List[Tuple[float, float]] = [(1.0, height / 2.0)]
        self.patrons: List[Patron] = []
        self.time = 0

    def add_ride(self, ride: Ride) -> bool:
        can_add = True
        for r in self.rides:
            if r.rect.overlap(ride.rect):
                print(f"Warning: Could not add ride '{ride.name}'. Overlaps with '{r.name}'.")
                can_add = False
        if can_add:
            self.rides.append(ride)
        return can_add

    def spawn_patron(self):
        entrance = random.choice(self.entrances)
        p = Patron(entrance[0], entrance[1], park=self)
        self.patrons.append(p)
        return p

    def despawn(self, patron: Patron):
        if patron in self.patrons:
            self.patrons.remove(patron)

    def closest_entrance(self, x: float, y: float) -> Tuple[float, float]:
        return min(self.entrances, key=lambda e: math.hypot(x - e[0], y - e[1]))

    def clamp_point(self, x: float, y: float) -> Tuple[float, float]:
        xx = max(0.5, min(self.width - 0.5, x))
        yy = max(0.5, min(self.height - 0.5, y))
        return xx, yy

    def step(self):
        self.time += 1
        for r in self.rides:
            r.step()
        for p in self.patrons:
            p.step()