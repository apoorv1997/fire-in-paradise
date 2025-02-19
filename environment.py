import random
from bot import Bot

class Environment:
    """
    The Environment class handles time-stepping the simulation and updating the state of the ship
    """

    def __init__(self, ship, q=0.3):
        self.ship = ship
        self.q = q         # The flammability parameter (0 ≤ q ≤ 1). A higher q makes the fire spread faster
        self.button_cell = None
        self.bot = None

        open_cells = self.ship.get_open_cells()
        if len(open_cells) < 3:
            raise Exception("Not enough open cells to place the bot, button, and fire.")

        # Randomly select three distinct open cells
        bot_cell, self.button_cell, fire_cell = random.sample(open_cells, 3)
        fire_cell.ignite()
        self.bot = Bot(ship, bot_cell.row, bot_cell.col)


    def update_fire(self):
        """
        Update the fire spread for one timestep.
        For each open cell that is not yet burning, count how many of its neighbors are burning.
        Then, the cell catches fire with probability 1 - (1 - q)^K. Applied to all cells
        based on the state at the beginning of the timestep.
        """
        new_fire_cells = []
        for cell in self.ship.get_open_cells():
            if not cell.on_fire:
                burning_neighbor_sum = cell.count_burning_neighbors()
                if burning_neighbor_sum > 0:
                    probability = 1 - (1 - self.q) ** burning_neighbor_sum
                    if random.random() < probability:
                        new_fire_cells.append(cell)
        # Update fire cells (all updates occur simultaneously)
        for new_fire in new_fire_cells:
            new_fire.ignite()

    def tick(self, bot_direction):
        """
        Returns:
            A string indicating the simulation status:
              - "ongoing" if the simulation should continue,
              - "success" if the bot has reached the button (and the fire is extinguished),
              - "failure" if the bot is caught by the fire.
        """
        # TODO should an invalid direction (ie hitting a wall) be allowed and be considered a "tick"?
        # direction the bot should move: "up", "down", "left", or "right"
        self.bot.move(bot_direction)
        curr_bot_cell = self.ship.get_cell(self.bot.row, self.bot.col)

        # Immediately check if the bot has moved into a burning cell.
        if curr_bot_cell.is_on_fire():
            return "failure"

        # Check if the bot has reached the button.
        if curr_bot_cell is self.button_cell:
            # Button pressed: fire is instantly extinguished
            for cell in self.ship.get_on_fire_cells():
                cell.extinguish()
            return "success"

        # Advance the fire
        self.update_fire()

        # Check again whether the fire has reached the bot
        if curr_bot_cell.is_on_fire():
            return "failure"

        return "ongoing"
