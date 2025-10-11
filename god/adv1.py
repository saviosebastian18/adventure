#!/usr/bin/env python3

import argparse
import csv
import math
import random
import sys
import os
import importlib.util
from dataclasses import dataclass
from typing import List, Tuple, Optional
from collections import deque

_missing = []

if importlib.util.find_spec("numpy"):
    import numpy as np
else:
    np = None
    _missing.append("numpy")

if importlib.util.find_spec("matplotlib"):
    import matplotlib
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.animation import FuncAnimation
else:
    plt = None
    patches = None
    FuncAnimation = None
    _missing.append("matplotlib")

if _missing:
    print(f"Note: missing modules: {', '.join(_missing)}")
    print("Installation with: pip install matplotlib numpy")
    print("Or try running with the --nogui flag for a text-only simulation.\n")

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

def is_numeric(s: str) -> bool:
    s = str(s).strip()
    if s.startswith('-') or s.startswith('+'):
        s = s[1:]
    return s.replace('.', '', 1).isdigit()

def load_rides_from_csv(path: str) -> List[Ride]:
    rides = []
    if os.path.exists(path):
        with open(path, newline='') as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                if row and not row[0].strip().startswith("#"):
                    if len(row) >= 5 and all(is_numeric(v) for v in row[1:5]):
                        name = row[0].strip()
                        typ = name.split(" ")[0]
                        x, y, w, h = [float(v) for v in row[1:5]]
                        
                        cap = int(row[5]) if len(row) > 5 and row[5] and is_numeric(row[5]) else 8
                        dur = int(row[6]) if len(row) > 6 and row[6] and is_numeric(row[6]) else 10
                        fun = float(row[7]) if len(row) > 7 and row[7] and is_numeric(row[7]) else 1.0
                        
                        ride = make_ride_by_type(typ, f"{name}-{i}", x, y, w, h, cap, dur, fun)
                        if ride:
                            rides.append(ride)
                    else:
                        print(f"Skipping invalid row in {path}: {row}")
    else:
        print(f"Error: Map file not found at '{path}'")
    return rides

def make_ride_by_type(typ: str, name: str, x: float, y: float, w: float, h: float,
                      cap: int, dur: int, fun: float) -> Optional[Ride]:
    t = typ.lower()
    ride = None
    if "pirate" in t or "ship" in t:
        ride = PirateShip(name, x, y, w, h, capacity=cap, duration=dur, fun=fun)
    elif "ferris" in t or "wheel" in t:
        ride = FerrisWheel(name, x, y, w, h, capacity=cap, duration=dur, fun=fun)
    elif "coaster" in t or "roller" in t:
        ride = RollerCoaster(name, x, y, w, h, capacity=cap, duration=dur, fun=fun)
    elif "drop" in t or "tower" in t:
        ride = DropTower(name, x, y, w, h, capacity=cap, duration=dur, fun=fun)
    else:
        print(f"Warning: Unknown ride type '{typ}' for ride '{name}'.")
    return ride

def run_simulation(park: Park, max_patrons: int, steps: int, nogui: bool):
    if not nogui and plt is None:
        print("Error: Matplotlib is required for GUI mode. Run with --nogui or install it.")
        return

    if nogui:
        for i in range(steps):
            if len(park.patrons) < max_patrons and random.random() < 0.2:
                park.spawn_patron()
            park.step()
            if i % 20 == 0:
                print(f"Step {park.time}, Patrons: {len(park.patrons)}")
    else:
        fig, ax = plt.subplots(figsize=(12, 8))

        def update(frame):
            ax.clear()
            if len(park.patrons) < max_patrons and random.random() < 0.2:
                park.spawn_patron()
            park.step()

            ax.set_facecolor('lightgreen')
            for ride in park.rides:
                ride.draw(ax)
            
            patron_x = [p.x for p in park.patrons]
            patron_y = [p.y for p in park.patrons]
            ax.scatter(patron_x, patron_y, s=10, c='blue', alpha=0.8)

            ax.set_xlim(0, park.width)
            ax.set_ylim(0, park.height)
            ax.set_aspect('equal', adjustable='box')
            ax.set_title(f"Theme Park Simulation | Time: {park.time} | Patrons: {len(park.patrons)}")
            
        _ = FuncAnimation(fig, update, frames=steps, interval=50, repeat=False)
        plt.show()

def main():
    parser = argparse.ArgumentParser(description="A simple theme park simulation.")
    parser.add_argument("map_file", nargs='?', default="map.csv",
                        help="Path to the CSV file defining the park layout. Defaults to 'map.csv'")
    parser.add_argument("--steps", type=int, default=1000, help="Number of simulation steps to run.")
    parser.add_argument("--patrons", type=int, default=50, help="Maximum number of patrons in the park.")
    parser.add_argument("--nogui", action="store_true", help="Run in text-only mode without visualization.")
    args = parser.parse_args()

    print("--- Theme Park Simulator ---")
    park = Park()
    rides = load_rides_from_csv(args.map_file)
    if not rides:
        print("No rides loaded. Exiting.")
    else:
        for ride in rides:
            park.add_ride(ride)
        
        print(f"Loaded {len(park.rides)} rides from '{args.map_file}'.")
        print(f"Running simulation for {args.steps} steps with up to {args.patrons} patrons.")
        
        run_simulation(park, args.patrons, args.steps, args.nogui)
        print("Simulation finished.")

if __name__ == "__main__":
    main()