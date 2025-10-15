# utils.py
import csv
import os
from typing import List, Optional
from rides import Ride, PirateShip, FerrisWheel, RollerCoaster, DropTower

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