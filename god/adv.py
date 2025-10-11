#!/usr/bin/env python3
"""
adventureworld.py
VS Code friendly + new ride types:
 - RollerCoaster: cyclic motion along a simple horizontal track
 - DropTower: vertical drop-and-lift motion (dramatic drop)
Patrons now consider a ride's "fun" value (higher is better) along with distance and queue length
to choose a target.

Run:
    python adventureworld.py -i
    python adventureworld.py -f map.csv -p params.csv
    python adventureworld.py --nogui
"""


import argparse
import csv
import math
import random
import sys
from collections import deque
from dataclasses import dataclass
from typing import List, Tuple, Optional

# --------------
# Dependency handling (attempt GUI backends for VS Code)
# --------------
missing = []
try:
    import numpy as np
except Exception:
    np = None
    missing.append("numpy")

try:
    import matplotlib
    for _backend in ("TkAgg", "Qt5Agg", "QtAgg", "WebAgg"):
        try:
            matplotlib.use(_backend)
            break
        except Exception:
            continue
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.animation import FuncAnimation
except Exception:
    plt = None
    patches = None
    FuncAnimation = None
    missing.append("matplotlib")

if missing:
    print("Note: missing modules:", ", ".join(missing))
    print("Install with: pip install matplotlib numpy")
    print("Or run with --nogui for text-only mode.\n")

# -------------------------
# Small utility dataclasses
# -------------------------
@dataclass
class Rect:
    x: float
    y: float
    w: float
    h: float

    def intersects(self, other: "Rect") -> bool:
        return not (self.x + self.w <= other.x or
                    other.x + other.w <= self.x or
                    self.y + self.h <= other.y or
                    other.y + other.h <= self.y)

    def center(self) -> Tuple[float, float]:
        return (self.x + self.w / 2.0, self.y + self.h / 2.0)

# -------------------------
# Rides: base class + types
# -------------------------
class Ride:
    """
    Base Ride:
      - name, rect: position & size
      - capacity, duration
      - queue, riders
      - fun (how attractive the ride is)
      - state: 'idle' or 'running'
    """
    def __init__(self, name: str, x: float, y: float, w: float, h: float,
                 capacity: int = 4, duration: int = 10, fun: float = 1.0):
        self.name = name
        self.rect = Rect(x, y, w, h)
        self.capacity = capacity
        self.duration = int(duration)
        self.queue: deque["Patron"] = deque()
        self.riders: List["Patron"] = []
        self.state = "idle"
        self.time_left = 0
        self.phase = 0.0
        self.fun = float(fun)  # higher means more attractive

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
            p = self.queue.popleft()
            self.riders.append(p)
            p.start_ride(self)
        if self.riders:
            self.state = "running"
            self.time_left = self.duration

    def enqueue(self, patron: "Patron"):
        self.queue.append(patron)

    def contains_point(self, x: float, y: float) -> bool:
        return (self.rect.x <= x <= self.rect.x + self.rect.w and
                self.rect.y <= y <= self.rect.y + self.rect.h)

    def draw(self, ax):
        if patches is None:
            return
        r = patches.Rectangle((self.rect.x, self.rect.y), self.rect.w, self.rect.h,
                              linewidth=1, edgecolor='k', facecolor='lightgray', alpha=0.6)
        ax.add_patch(r)
        cx, cy = self.rect.center()
        ax.text(cx, cy, f"{self.name}\nQ:{len(self.queue)} R:{len(self.riders)}", ha='center', va='center', fontsize=8)

class PirateShip(Ride):
    def step(self):
        super().step()
        self.phase += 0.05

    def draw(self, ax):
        super().draw(ax)
        if patches is None:
            return
        cx, cy = self.rect.center()
        angle = math.sin(self.phase) * 45
        length = min(self.rect.w, self.rect.h) * 0.6
        dx = length * math.cos(math.radians(angle))
        dy = length * math.sin(math.radians(angle))
        ax.plot([cx - dx/2, cx + dx/2], [cy - dy/2, cy + dy/2], linewidth=3)

class FerrisWheel(Ride):
    def step(self):
        super().step()
        if self.state == "running":
            self.phase += 0.3
        else:
            self.phase += 0.02

    def draw(self, ax):
        super().draw(ax)
        if patches is None:
            return
        cx, cy = self.rect.center()
        radius = min(self.rect.w, self.rect.h) * 0.45
        circle = patches.Circle((cx, cy), radius=radius, fill=False, linewidth=1)
        ax.add_patch(circle)
        angle = (self.phase * 30) % 360
        tx = cx + radius * math.cos(math.radians(angle))
        ty = cy + radius * math.sin(math.radians(angle))
        ax.plot([cx, tx], [cy, ty], linewidth=1.5)
        ax.scatter([tx], [ty], s=20)

class RollerCoaster(Ride):
    """
    RollerCoaster: visualizes multiple cars travelling along a simple horizontal track
    - duration controls how long a "run" lasts
    - phase is used to place cars along the track
    """
    def __init__(self, name, x, y, w, h, capacity=8, duration=12, fun=2.0, cars=4):
        super().__init__(name, x, y, w, h, capacity=capacity, duration=duration, fun=fun)
        self.cars = int(cars)

    def step(self):
        super().step()
        # speed up phase when running
        if self.state == "running":
            self.phase += 0.6
        else:
            self.phase += 0.05

    def draw(self, ax):
        super().draw(ax)
        if patches is None:
            return
        cx, cy = self.rect.center()
        # draw a track as a wavy line across the ride rect
        xs = [self.rect.x + i * (self.rect.w / 20.0) for i in range(21)]
        ys = [cy + math.sin((x - self.rect.x) / self.rect.w * math.pi * 2 + self.phase * 0.3) * (self.rect.h * 0.2) for x in xs]
        ax.plot(xs, ys, linewidth=2)
        # draw cars evenly spaced along the track using phase
        for i in range(self.cars):
            t = (self.phase * 0.5 + i * (2 * math.pi / max(1,self.cars))) % (2 * math.pi)
            tx = cx + math.cos(t) * (self.rect.w * 0.4)
            ty = cy + math.sin(t) * (self.rect.h * 0.25)
            ax.add_patch(patches.Circle((tx, ty), radius=0.3))

class DropTower(Ride):
    """
    DropTower: riders sit at top, then drop quickly (visualized by a dot moving down)
    - duration controls total cycle; drop happens near start
    """
    def __init__(self, name, x, y, w, h, capacity=6, duration=8, fun=1.8):
        super().__init__(name, x, y, w, h, capacity=capacity, duration=duration, fun=fun)

    def step(self):
        super().step()
        # phase used to animate height of the gondola
        if self.state == "running":
            # more dramatic phase change during running
            self.phase += 0.8
        else:
            self.phase += 0.05

    def draw(self, ax):
        super().draw(ax)
        if patches is None:
            return
        cx, cy = self.rect.center()
        # tower line
        ax.plot([cx, cx], [self.rect.y, self.rect.y + self.rect.h], linewidth=2)
        # compute gondola vertical position:
        # when running, make it drop quickly (sin-shaped) using phase and duration
        if self.state == "running":
            t = (1 - max(0, self.time_left) / max(1, self.duration))  # 0->1 through run
            # drop mostly in first half, then return for next cycle
            if t < 0.45:
                frac = (t / 0.45)  # 0..1 drop
                gy = self.rect.y + self.rect.h * (0.95 - 0.8 * frac)
            else:
                # bounce back slowly
                frac = (t - 0.45) / (1 - 0.45)
                gy = self.rect.y + self.rect.h * (0.15 + 0.8 * frac)
        else:
            gy = self.rect.y + self.rect.h * 0.95
        ax.add_patch(patches.Rectangle((cx - 0.8, gy - 0.3), 1.6, 0.6, facecolor='saddlebrown'))

# -------------------------
# Patron (park visitor)
# -------------------------
class Patron:
    _id_counter = 0

    def __init__(self, x: float, y: float, park: "Park"):
        self.id = Patron._id_counter
        Patron._id_counter += 1
        self.x = x
        self.y = y
        self.park = park
        self.state = "roaming"
        self.target: Optional[Ride] = None
        self.speed = random.uniform(0.6, 1.4)

    def step(self):
        if self.state == "roaming":
            # small chance to re-evaluate target so people don't get stuck
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
        elif self.state == "queuing":
            # waiting in line (no action)
            pass
        elif self.state == "riding":
            # on ride until ride calls finish_ride()
            pass
        elif self.state == "leaving":
            ex, ey = self.park.closest_entrance(self.x, self.y)
            self.move_towards(ex, ey)
            if math.hypot(self.x - ex, self.y - ey) < 1.0:
                self.park.despawn(self)

    def choose_target(self):
        """
        New choice rule:
          score = distance - alpha * fun + beta * queue_length
        Patrons prefer rides with higher 'fun' and shorter queues, balanced with distance.
        """
        if not self.park.rides:
            self.target = None
            return
        scored = []
        for r in self.park.rides:
            cx, cy = r.rect.center()
            dist = math.hypot(self.x - cx, self.y - cy)
            qlen = len(r.queue)
            # constants to tune preference
            alpha = 8.0   # how much fun matters (bigger -> prefer fun more)
            beta = 2.0    # penalty per person in queue
            score = dist - alpha * r.fun + beta * qlen
            scored.append((score, r))
        scored.sort(key=lambda x: x[0])
        self.target = scored[0][1]

    def move_towards(self, tx: float, ty: float):
        dx = tx - self.x
        dy = ty - self.y
        dist = math.hypot(dx, dy)
        if dist < 1e-6:
            return
        step = min(self.speed * 0.8, dist)
        nx = self.x + dx / dist * step
        ny = self.y + dy / dist * step
        for r in self.park.rides:
            if r.rect.x <= nx <= r.rect.x + r.rect.w and r.rect.y <= ny <= r.rect.y + r.rect.h:
                nx = self.x + (-dy / dist) * step * 0.6
                ny = self.y + (dx / dist) * step * 0.6
                break
        self.x, self.y = self.park.clamp_point(nx, ny)

    def random_walk(self):
        angle = random.random() * 2 * math.pi
        self.x += math.cos(angle) * 0.5 * self.speed
        self.y += math.sin(angle) * 0.5 * self.speed
        self.x, self.y = self.park.clamp_point(self.x, self.y)

    def is_near_ride(self, ride: Ride) -> bool:
        cx, cy = ride.rect.center()
        return math.hypot(self.x - cx, self.y - cy) < max(ride.rect.w, ride.rect.h) * 0.6

    def start_ride(self, ride: Ride):
        self.state = "riding"
        self.target = ride
        cx, cy = ride.rect.center()
        self.x, self.y = cx + random.uniform(-0.3, 0.3), cy + random.uniform(-0.3, 0.3)

    def finish_ride(self):
        self.state = "roaming"
        self.target = None
        if random.random() < 0.12:
            self.state = "leaving"

# -------------------------
# Park: contains rides/patrons
# -------------------------
class Park:
    def __init__(self, width: float = 60.0, height: float = 40.0):
        self.width = width
        self.height = height
        self.rides: List[Ride] = []
        self.entrances: List[Tuple[float, float]] = [(0.5, height/2.0), (width - 0.5, height/2.0)]
        self.patrons: List[Patron] = []
        self.time = 0

    def add_ride(self, ride: Ride) -> bool:
        for r in self.rides:
            if r.rect.intersects(ride.rect):
                return False
        self.rides.append(ride)
        return True

    def spawn_patron(self, entrance: Optional[Tuple[float,float]] = None) -> Patron:
        if entrance is None:
            entrance = random.choice(self.entrances)
        p = Patron(entrance[0] + random.uniform(-0.8, 0.8),
                   entrance[1] + random.uniform(-0.8, 0.8),
                   self)
        self.patrons.append(p)
        return p

    def despawn(self, patron: Patron):
        if patron in self.patrons:
            self.patrons.remove(patron)

    def closest_entrance(self, x: float, y: float) -> Tuple[float, float]:
        return min(self.entrances, key=lambda e: math.hypot(x - e[0], y - e[1]))

    def clamp_point(self, x: float, y: float) -> Tuple[float, float]:
        x = max(0.5, min(self.width - 0.5, x))
        y = max(0.5, min(self.height - 0.5, y))
        return x, y

    def step(self):
        self.time += 1
        for r in self.rides:
            r.step()
        for p in list(self.patrons):
            p.step()

# -------------------------
# CSV loaders & factory
# -------------------------
def load_map_csv(path: str) -> List[Tuple[str, float, float, float, float, int, int, float]]:
    rows = []
    with open(path, newline='') as f:
        rdr = csv.reader(f)
        for row in rdr:
            if not row or row[0].strip().startswith('#'):
                continue
            typ = row[0].strip()
            x = float(row[1]); y = float(row[2]); w = float(row[3]); h = float(row[4])
            cap = int(row[5]) if len(row) > 5 and row[5] else 4
            dur = int(row[6]) if len(row) > 6 and row[6] else 10
            fun = float(row[7]) if len(row) > 7 and row[7] else 1.0
            rows.append((typ, x, y, w, h, cap, dur, fun))
    return rows

def load_params_csv(path: str) -> dict:
    params = {}
    with open(path, newline='') as f:
        rdr = csv.reader(f)
        for row in rdr:
            if not row or row[0].strip().startswith('#'):
                continue
            k = row[0].strip(); v = row[1].strip()
            try:
                params[k] = int(v)
            except ValueError:
                try:
                    params[k] = float(v)
                except ValueError:
                    params[k] = v
    return params

def make_ride_by_type(typ: str, name: str, x: float, y: float, w: float, h: float,
                      cap: int, dur: int, fun: float) -> Ride:
    t = typ.lower()
    if 'pirate' in t or 'ship' in t:
        return PirateShip(name, x, y, w, h, capacity=cap, duration=dur, fun=fun)
    if 'ferris' in t or 'wheel' in t:
        return FerrisWheel(name, x, y, w, h, capacity=cap, duration=dur, fun=fun)
    if 'coaster' in t or 'roller' in t:
        return RollerCoaster(name, x, y, w, h, capacity=cap, duration=dur, fun=fun, cars=4)
    if 'drop' in t or 'tower' in t:
        return DropTower(name, x, y, w, h, capacity=cap, duration=dur, fun=fun)
    return Ride(name, x, y, w, h, capacity=cap, duration=dur, fun=fun)

# -------------------------
# Main simulation & plotting
# -------------------------
def run_simulation(interactive=False, mapfile=None, paramsfile=None, nogui=False):
    width, height = 60.0, 40.0
    num_initial_patrons = 12
    spawn_rate = 0.08
    steps = 400

    park = Park(width=width, height=height)

    if mapfile:
        try:
            entries = load_map_csv(mapfile)
            for i, (typ, x, y, w, h, cap, dur, fun) in enumerate(entries):
                name = f"{typ}_{i}"
                r = make_ride_by_type(typ, name, x, y, w, h, cap, dur, fun)
                if not park.add_ride(r):
                    print(f"Warning: ride '{name}' overlaps existing rides and was skipped.")
        except Exception as e:
            print("Failed to load map file:", e)
    else:
        # defaults: include RollerCoaster and DropTower
        park.add_ride(PirateShip("PirateShip", 6, 6, 8, 6, capacity=6, duration=12, fun=1.2))
        park.add_ride(FerrisWheel("FerrisWheel", 26, 20, 12, 12, capacity=8, duration=16, fun=1.0))
        park.add_ride(RollerCoaster("RollerCoaster", 44, 8, 12, 8, capacity=8, duration=14, fun=2.4, cars=5))
        park.add_ride(DropTower("DropTower", 36, 28, 6, 10, capacity=6, duration=8, fun=1.9))

    if paramsfile:
        try:
            params = load_params_csv(paramsfile)
            num_initial_patrons = int(params.get("num_initial_patrons", num_initial_patrons))
            spawn_rate = float(params.get("spawn_rate", spawn_rate))
            steps = int(params.get("steps", steps))
            width = float(params.get("width", width))
            height = float(params.get("height", height))
        except Exception as e:
            print("Failed to load params file:", e)

    if interactive:
        try:
            num_initial_patrons = int(input(f"Initial patrons [{num_initial_patrons}]: ") or num_initial_patrons)
            spawn_rate = float(input(f"Spawn rate (0-1) [{spawn_rate}]: ") or spawn_rate)
            steps = int(input(f"Simulation steps [{steps}]: ") or steps)
        except Exception:
            print("Invalid input, using defaults.")

    for _ in range(num_initial_patrons):
        park.spawn_patron()

    if nogui or plt is None:
        print("Running in text-only mode (no GUI).")
        for i in range(steps):
            if random.random() < spawn_rate:
                park.spawn_patron()
            park.step()
            if i % 20 == 0:
                ride_names = ", ".join([f"{r.name}(Q{len(r.queue)}/R{len(r.riders)})" for r in park.rides])
                print(f"Step {park.time}: patrons={len(park.patrons)}; rides: {ride_names}")
        print("Simulation finished (text-only).")
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_xlim(0, park.width)
    ax.set_ylim(0, park.height)
    ax.set_title("Adventure World - simulation")

    def update(frame):
        ax.clear()
        ax.set_xlim(0, park.width)
        ax.set_ylim(0, park.height)
        ax.set_title(f"Adventure World - step {park.time}")
        if random.random() < spawn_rate:
            park.spawn_patron()
        park.step()
        for r in park.rides:
            r.draw(ax)
        for e in park.entrances:
            ax.plot(e[0], e[1], marker='s', markersize=6)
            ax.text(e[0], e[1] + 1.0, "Entrance", fontsize=7, ha='center')
        xs = [p.x for p in park.patrons]
        ys = [p.y for p in park.patrons]
        colors = []
        for p in park.patrons:
            if p.state == "roaming":
                colors.append('blue')
            elif p.state == "queuing":
                colors.append('orange')
            elif p.state == "riding":
                colors.append('green')
            else:
                colors.append('red')
        if xs:
            ax.scatter(xs, ys, c=colors, s=20)
        ax.text(1, park.height - 1, f"Patrons: {len(park.patrons)}  Spawn rate: {spawn_rate}", fontsize=8)
        if park.time >= steps:
            anim.event_source.stop()

    anim = FuncAnimation(fig, update, interval=120)
    plt.show()

# -------------------------
# CLI
# -------------------------
def main():
    parser = argparse.ArgumentParser(description="Adventure World simulator (with new rides)")
    parser.add_argument("-i", "--interactive", action="store_true", help="interactive mode (ask inputs)")
    parser.add_argument("-f", "--mapfile", type=str, help="map csv file: type,x,y,w,h,capacity,duration,fun")
    parser.add_argument("-p", "--paramsfile", type=str, help="params csv file: key,value")
    parser.add_argument("--nogui", action="store_true", help="run without opening a matplotlib window (text-only)")
    args = parser.parse_args()
    run_simulation(interactive=args.interactive, mapfile=args.mapfile, paramsfile=args.paramsfile, nogui=args.nogui)

if __name__ == "__main__":
    main()