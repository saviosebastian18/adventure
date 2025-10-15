# rides.py
import math
from collections import deque
from typing import List
from structures import Rect
if __import__('importlib').util.find_spec("numpy"):
    import numpy as np
else:
    np = None
if __import__('importlib').util.find_spec("matplotlib"):
    import matplotlib.patches as patches
else:
    patches = None

class Ride:
    def __init__(self, name: str, x: float, y: float, w: float, h: float,
                 capacity: int = 4, duration: int = 10, fun: float = 1.0):
        self.name = name
        self.rect = Rect(float(x), float(y), float(w), float(h))
        self.capacity = int(capacity)
        self.duration = int(duration)
        self.fun = float(fun)
        self.queue: deque["Patron"] = deque()
        self.riders: List["Patron"] = []
        self.state = "idle"
        self.time_left = 0
        self.phase = 0.0

    def step(self):
        if self.state == "running":
            self.time_left -= 1
            self.phase += 0.2
            if self.time_left <= 0:
                for p in list(self.riders):
                    p.finish_ride()
                self.riders.clear()
                self.state = "idle"
        if self.state == "idle" and self.queue:
            self.board()

    def board(self):
        while self.queue and len(self.riders) < self.capacity:
            patron = self.queue.popleft()
            self.riders.append(patron)
            patron.start_ride(self)
        if self.riders:
            self.state = "running"
            self.time_left = int(self.duration)

    def enqueue(self, patron: "Patron"):
        self.queue.append(patron)

    def contains_point(self, x: float, y: float) -> bool:
        return (self.rect.x <= x <= self.rect.x + self.rect.w and
                self.rect.y <= y <= self.rect.y + self.rect.h)

    def draw(self, ax):
        if patches is not None:
            r = self.rect
            box = patches.Rectangle((r.x, r.y), r.w, r.h,
                                    linewidth=1, edgecolor='k', facecolor='lightgray', alpha=0.6)
            ax.add_patch(box)
            cx, cy = r.center()
            ax.text(cx, cy, f"{self.name}\nQ:{len(self.queue)} R:{len(self.riders)}",
                    ha='center', va='center', fontsize=8)

class PirateShip(Ride):
    def step(self):
        super().step()
        self.phase += 0.05
    def draw(self, ax):
        super().draw(ax)
        if patches is not None:
            cx, cy = self.rect.center()
            angle = math.sin(self.phase) * 45
            length = min(self.rect.w, self.rect.h) * 0.6
            dx = length * math.cos(math.radians(angle))
            dy = length * math.sin(math.radians(angle))
            ax.plot([cx - dx / 2, cx + dx / 2], [cy - dy / 2, cy + dy / 2], linewidth=4, color='saddlebrown')

class FerrisWheel(Ride):
    def step(self):
        super().step()
        self.phase += 0.03 if self.state == "running" else 0.01
    def draw(self, ax):
        super().draw(ax)
        if patches is not None:
            cx, cy = self.rect.center()
            radius = min(self.rect.w, self.rect.h) * 0.45
            circ = patches.Circle((cx, cy), radius=radius, fill=False, linewidth=2, edgecolor='darkred')
            ax.add_patch(circ)
            for i in range(8):
                angle = self.phase * 20 + i * (360 / 8)
                tx = cx + radius * math.cos(math.radians(angle))
                ty = cy + radius * math.sin(math.radians(angle))
                ax.add_patch(patches.Circle((tx, ty), radius=self.rect.w * 0.05, facecolor='gold'))

class RollerCoaster(Ride):
    def __init__(self, name, x, y, w, h, capacity=8, duration=12, fun=2.0, cars=4):
        super().__init__(name, x, y, w, h, capacity=capacity, duration=duration, fun=fun)
        self.cars = int(cars)
    def step(self):
        super().step()
        self.phase += 0.1 if self.state == "running" else 0.02
    def draw(self, ax):
        super().draw(ax)
        if patches is not None and np is not None:
            cx, cy = self.rect.center()
            xs = np.linspace(self.rect.x, self.rect.x + self.rect.w, 100)
            ys = cy + np.sin(xs / (self.rect.w / 4) + self.phase * 5) * (self.rect.h * 0.25)
            ax.plot(xs, ys, linewidth=2, color='steelblue')
            for i in range(self.cars):
                offset = i * (2 * math.pi / self.cars)
                t = (self.phase * 10 + offset) % (2 * math.pi)
                tx = cx + (self.rect.w * 0.4) * math.cos(t)
                ty = cy + (self.rect.h * 0.3) * math.sin(t*2)
                ax.add_patch(patches.Rectangle((tx - 0.5, ty - 0.25), 1, 0.5, facecolor='crimson'))

class DropTower(Ride):
    def __init__(self, name, x, y, w, h, capacity=12, duration=8, fun=1.8):
        super().__init__(name, x, y, w, h, capacity=capacity, duration=duration, fun=fun)
    def step(self):
        super().step()
        self.phase += 0.05
    def draw(self, ax):
        super().draw(ax)
        if patches is not None:
            cx, cy = self.rect.center()
            ax.plot([cx, cx], [self.rect.y, self.rect.y + self.rect.h], linewidth=4, color='dimgray')
            if self.state == "running":
                t = (1 - max(0, self.time_left) / max(1, self.duration))
                if t < 0.5:
                    frac = t / 0.5
                    gondola_y = self.rect.y + self.rect.h * 0.9 * frac
                else:
                    frac = (t - 0.5) / 0.5
                    gondola_y = self.rect.y + self.rect.h * 0.9 * (1 - frac**3)
            else:
                gondola_y = self.rect.y
            ax.add_patch(patches.Rectangle((cx - self.rect.w*0.3, gondola_y), self.rect.w*0.6, self.rect.h*0.05, facecolor='orange'))