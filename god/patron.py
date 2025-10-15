# patron.py
import math
import random
from typing import Optional

from rides import Ride

class Patron:
    _id_counter = 0

    def __init__(self, x: float, y: float, park: "Park"):
        self.id = Patron._id_counter
        Patron._id_counter += 1
        self.x = float(x)
        self.y = float(y)
        self.park = park
        self.state = "roaming"
        self.target: Optional[Ride] = None
        self.speed = random.uniform(0.4, 0.8)

    def step(self):
        if self.state == "roaming":
            if not self.target or random.random() < 0.03:
                self.choose_target()
            if self.target:
                tx, ty = self.target.rect.center()
                self.move_towards(tx, ty)
                if self.is_near_ride(self.target):
                    self.state = "queuing"
                    self.target.enqueue(self)
            else:
                self.random_walk()
        elif self.state == "leaving":
            ex, ey = self.park.closest_entrance(self.x, self.y)
            self.move_towards(ex, ey)
            if math.hypot(self.x - ex, self.y - ey) < 1.0:
                self.park.despawn(self)

    def choose_target(self):
        if not self.park.rides:
            self.target = None
            return
        best_score = -float("inf")
        best_ride = None
        fun_weight, dist_weight, queue_weight = 3.0, -0.1, -0.5
        for r in self.park.rides:
            cx, cy = r.rect.center()
            dist = math.hypot(self.x - cx, self.y - cy)
            score = (r.fun * fun_weight) + (dist * dist_weight) + (len(r.queue) * queue_weight)
            if score > best_score:
                best_score = score
                best_ride = r
        self.target = best_ride

    def move_towards(self, tx: float, ty: float):
        dx, dy = tx - self.x, ty - self.y
        dist = math.hypot(dx, dy)
        if dist > 1e-6:
            step = min(self.speed, dist)
            nx = self.x + (dx / dist) * step
            ny = self.y + (dy / dist) * step
            self.x, self.y = self.park.clamp_point(nx, ny)

    def random_walk(self):
        angle = random.random() * 2 * math.pi
        self.x += math.cos(angle) * 0.5 * self.speed
        self.y += math.sin(angle) * 0.5 * self.speed
        self.x, self.y = self.park.clamp_point(self.x, self.y)

    def is_near_ride(self, ride: Ride) -> bool:
        cx, cy = ride.rect.center()
        return math.hypot(self.x - cx, self.y - cy) < max(ride.rect.w, ride.rect.h) * 0.7

    def start_ride(self, ride: Ride):
        self.state = "riding"
        self.target = ride
        cx, cy = ride.rect.center()
        self.x = cx + random.uniform(-0.1, 0.1)
        self.y = cy + random.uniform(-0.1, 0.1)

    def finish_ride(self):
        self.state = "roaming"
        self.target = None
        if random.random() < 0.10:
            self.state = "leaving"