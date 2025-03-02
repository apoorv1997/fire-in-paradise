from ship import Ship
from visualizer import Visualizer
from environment import Environment
from botcontroller import BotController

def main():
    # -- WARNING: run with Python 3.6 -- #

    ship_dimension = 20  # dimension sets the nxn ship grid size
    q = 0.6  # flammability parameter 0-1 (higher q = more flammable cells)
    cell_size = 20  # Size of each cell in pixels on rendered grid
    realtime = True  # Set True for real-time simulation, False for static display at terminal state
    tick_interval = 0.5 # seconds between each tick in real-time simulation

    # Set strategy for type of bot control:
    # 0: Manual (use arrow keys to move),
    # 1: Bot 1 (preplan once, ignoring future fire spread),
    # 2: Bot 2 (replan each timestep, blocking burning cells),
    # 3: Bot 3 (replan each timestep, blocking burning cells and, if possible, cells adjacent to fire)
    # 4: Bot 4 (custom strategy)
    strategy = 5


    ship = Ship(ship_dimension)
    env = Environment(ship, q)
    viz = Visualizer(ship, cell_size, env)

    if strategy == 0:
        controller = BotController(env.bot, env, 0)
        viz.draw_grid_with_interactive_robot(controller)
    else:
        controller = BotController(env.bot, env, strategy)
        viz.draw_grid_with_algorithmic_robot(controller, realtime, tick_interval)

if __name__ == "__main__":
    main()
