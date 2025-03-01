import json
import time
from cell import CellEncoder
from ship import Ship
import sys
from visualizer import Visualizer
from environment import Environment

def main():
    main_data = []
    for i in range(500):
        ship = Ship(dimension=20)
        ship.generate_maze()
        env = Environment(ship, q=0.3)


        viz = Visualizer(ship, cell_size=20, env=env)
        # Display the grid with a bot you can control manually with arrow keys
        data = viz.draw_grid_with_interactive_robot(sys.argv)
        main_data.append(data)
        
    open(f"data/output_{int(time.time())}.json", "w").write(json.dumps(main_data, indent=4, cls=CellEncoder))
        # Just display the grid image
        # viz.draw_static_grid()


if __name__ == "__main__":
    main()
