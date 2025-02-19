from ship import Ship
from visualizer import Visualizer
from environment import Environment


# TODO ensure grader runs using Python 3.6
# TODO should the button catch on fire?
def main():
    ship = Ship(dimension=20)
    ship.generate_maze()
    env = Environment(ship, q=0.3)


    viz = Visualizer(ship, cell_size=20, env=env)
    # Display the grid with a bot you can control manually with arrow keys
    viz.draw_grid_with_interactive_robot()

    # Just display the grid image
    # viz.draw_static_grid()


if __name__ == "__main__":
    main()
