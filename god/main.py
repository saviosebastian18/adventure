# main.py
import argparse
import random
import importlib.util

from park import Park
from utils import load_rides_from_csv

miss = []
if not importlib.util.find_spec("numpy"):
    miss.append("numpy")

if importlib.util.find_spec("matplotlib"):
    import matplotlib
    matplotlib.use('TkAgg') 
    

    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation
else:
    plt = None
    FuncAnimation = None
    miss.append("matplotlib")

if miss:
    print(f"!!!!!!missing modules!!!: {', '.join(miss)}")

def run_simulation(park: Park, max_patrons: int, steps: int, nogui: bool):
    
    if nogui:
        for i in range(steps):
            if len(park.patrons) < max_patrons:
                park.spawn_patron()
            park.step()
            if i % 20 == 0:
                print(f"Step {park.time}, Patrons: {len(park.patrons)}")
    else:
        fig, ax = plt.subplots(figsize=(12, 8))
        def update(frame):
            ax.clear()
            if len(park.patrons) < max_patrons:
                park.spawn_patron()
            park.step()
            ax.set_facecolor('lightgreen')
            for ride in park.rides:
                ride.draw(ax)
            px = []
            for p in park.patrons:
                px.append(p.x)
            py = []
            for p in park.patrons:
                py.append(p.y)
            ax.scatter(px, py, s=10, c='blue', alpha=0.8)
            ax.set_xlim(0, park.width)
            ax.set_ylim(0, park.height)
            ax.set_aspect('equal', adjustable='box')
            ax.set_title(f"Theme Park Simulation | Time: {park.time} | Patrons: {len(park.patrons)}")
        
        
        anim = FuncAnimation(fig, update, frames=steps, interval=50, repeat=False)
        plt.show()

def main():
    # --- Step 1: Set up argument parsing ---
    # This part allows us to run the script with custom settings from the command line.
    parser = argparse.ArgumentParser(description="A simple theme park simulation.")
    parser.add_argument("map_file", nargs='?', default="map.csv",
                        help="Path to the CSV file defining the park layout. Defaults to 'map.csv'")
    parser.add_argument("--steps", type=int, default=1000, help="Number of simulation steps to run.")
    parser.add_argument("--patrons", type=int, default=50, help="Maximum number of patrons in the park.")
    parser.add_argument("--nogui", action="store_true", help="Run in text-only mode without visualization.")
    args = parser.parse_args()

    # --- Step 2: Load data and prepare the park ---
    print("--- Theme Park Simulator ---")
    
    # Create an empty park object first
    park = Park()
    
    # Try to load rides from the CSV file the user provided
    rides = load_rides_from_csv(args.map_file)

    # IMPORTANT: Check if the rides list is empty. If it is, we can't continue.
    if not rides:
        print(f"Error: No rides were loaded from the file '{args.map_file}'. Exiting.")
        return  # Stop the function here

    # If we have rides, add them to our park one by one
    for ride in rides:
        park.add_ride(ride)

    # --- Step 3: Run the simulation ---
    # Print a message to the user so they know what's happening
    print(f"Loaded {len(park.rides)} rides from '{args.map_file}'.")
    print(f"Running simulation for {args.steps} steps with up to {args.patrons} patrons.")
    
    # Call the main function that runs the simulation
    run_simulation(park, args.patrons, args.steps, args.nogui)
    
    print("Simulation finished.")

# This line makes sure the main() function is called when you run the script
if __name__ == "__main__":
    main()