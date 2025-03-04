import random
from bot import Bot
from botcontroller import BotController

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
        self.ship.ignite_cell(fire_cell)
        self.initial_fire_cell = fire_cell
        self.bot = Bot(bot_cell, self.ship)
        self.initial_bot_cell = bot_cell

        # Record the robot's path (starting with its initial cell)
        self.bot_path = [bot_cell]

    def update_fire(self):
        """
        Update fire spread for one timestep. Each open cell (not already burning) with
        burning neighbors catches fire with probability 1 - (1 - q)^K.
        """
        new_fire_cells = set()
        # Use a set comprehension to gather candidate neighbors from burning cells.
        candidate_cells = {neighbor for cell in self.ship.on_fire_cells
                           for neighbor in cell.neighbors
                           if neighbor.is_open() and not neighbor.on_fire}

        for cell in candidate_cells:
            burning_neighbors = sum(1 for n in cell.neighbors if n.is_on_fire())
            if burning_neighbors > 0:
                probability = 1 - (1 - self.q) ** burning_neighbors
                if random.random() < probability:
                    new_fire_cells.add(cell)
        for new_fire in new_fire_cells:
            self.ship.ignite_cell(new_fire)

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
                self.ship.extinguish_cell(cell)
            return "success"

        self.update_fire()

        if curr_bot_cell.is_on_fire() or self.button_cell.is_on_fire():
            return "failure"

        return "ongoing"

    def is_winnable(self, tries=2):
        """
        For a given environment, test all strategies. If any strategy results in a win,
        return True (simulation winnable). Otherwise, return False.
        """
        for t in range(tries):
            for strat in [1, 2, 3, 4]:
                controller = BotController(self.bot, self, strat)
                result = "ongoing"
                # Run simulation until terminal state
                while result == "ongoing":
                    result = controller.make_action()
                if result == "success":
                    self.reset()
                    return True
                self.reset()
        self.reset()
        return False

    def reset(self):
        """
        Reset the environment to its initial state
        """
        for cell in self.ship.get_on_fire_cells():
            self.ship.extinguish_cell(cell)
        self.bot.cell = self.initial_bot_cell
        self.bot_path = [self.bot.cell]
        self.ship.ignite_cell(self.initial_fire_cell)
        self.ship.history_fire_cells.clear()

