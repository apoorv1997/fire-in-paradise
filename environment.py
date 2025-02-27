# environment.py
import random
from bot import Bot

class Environment:
    """
    The Environment class handles time-stepping the simulation and updating the state of the ship.
    """
    def __init__(self, ship, q=0.3):
        self.ship = ship
        self.q = q
        self.button_cell = None
        self.bot = None

        open_cells = self.ship.get_open_cells()
        if len(open_cells) < 3:
            raise Exception("Not enough open cells to place the bot, button, and fire")

        # Randomly select three distinct open cells to initialize the bot, button, and fire
        bot_cell, self.button_cell, fire_cell = random.sample(open_cells, 3)
        fire_cell.ignite()
        self.initial_fire_cell = fire_cell
        self.bot = Bot(bot_cell, self.ship)

        # Record the robot's path (starting with its initial cell)
        self.bot_path = [bot_cell]
        # Record every cell that gets ignited during the simulation
        self.history_fire = {fire_cell}

    def update_fire(self):
        """
        Update fire spread for one timestep. Each open cell (not already burning) with
        burning neighbors catches fire with probability 1 - (1 - q)^K
        """
        new_fire_cells = []
        for cell in self.ship.get_open_cells():
            if not cell.on_fire:
                burning_neighbor_sum = cell.count_burning_neighbors()
                if burning_neighbor_sum > 0:
                    probability = 1 - (1 - self.q) ** burning_neighbor_sum
                    if random.random() < probability:
                        new_fire_cells.append(cell)
        for new_fire in new_fire_cells:
            new_fire.ignite()
            self.history_fire.add(new_fire)

    def tick(self, bot_direction):
        """
        Progress the simulation by one timestep (move bot in chosen direction and update fire and check for terminal state)

        Returns:
            "ongoing" if the simulation should continue,
            "success" if the bot has reached the button (fire is then extinguished),
            "failure" if the bot is caught by fire.
        """
        self.bot.move(bot_direction)
        self.bot_path.append(self.bot.cell)
        curr_bot_cell = self.bot.cell

        if curr_bot_cell.is_on_fire() or self.button_cell.is_on_fire():
            return "failure"

        if curr_bot_cell is self.button_cell:
            for cell in self.ship.get_on_fire_cells():
                cell.extinguish()
            return "success"

        self.update_fire()

        if curr_bot_cell.is_on_fire() or self.button_cell.is_on_fire():
            return "failure"

        return "ongoing"
