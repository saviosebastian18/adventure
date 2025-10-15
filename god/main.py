# main.py
import argparse
import random
import importlib.util


from park import Park
from utils import load_rides_from_csv

_missing = []
if not importlib.util.find_spec("numpy"):
    _missing.append("numpy")

if importlib.util.find_spec("matplotlib"):
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation
else:
    plt = None
    FuncAnimation = None
    _missing.append("matplotlib")

if _missing:
    print(f"Note: missing modules: {', '.join(_missing)}")
    print("Installation with: pip install matplotlib numpy")
    print("Or try running with the --nogui flag for a text-only simulation.\n")

def run_simulation(park: Park, max_patrons: int, steps: int, nogui: bool):
    if not nogui and plt is None:
        print("Error")
        retur=
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