from collections import deque
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

    def tick(self):
        """
        Returns:
            A string indicating the simulation status:
              - "ongoing" if the simulation should continue,
              - "success" if the bot has reached the button (and the fire is extinguished),
              - "failure" if the bot is caught by the fire.
        """
        # TODO should an invalid direction (ie hitting a wall) be allowed and be considered a "tick"?
        # create a queue to push the bot's new position
        # move the bot
        # check for neighbours and look for bot's new position.
        # update ship status.
        # direction the bot should move: "up", "down", "left", or "right"
        print(self.bot.row)
        print(self.bot.col)
        m = self.bot.row
        n = self.bot.col


        curr_bot_cell = self.ship.get_cell(m, n)

        q = deque()
        q.append((m, n))

        dx = [-1, 0, 1, 0]
        dy = [0, 1, 0, -1]

        ship_row = 40
        ship_col = 40

        dis = [[-1 for _ in range(ship_col)] for _ in range(ship_row)]

        dis[m][n] = 0

        while q:
            ind = q.popleft()

            for i in range(4):
                x = ind[0] + dx[i]
                y = ind[1] + dy[i]

                if 0 <= x < ship_row and 0 <= y < ship_col and dis[x][y] == -1:
                    dis[x][y] = dis[ind[0]][ind[1]] + 1
                    new_cell = self.ship.get_cell(x, y)
                    q.append((x, y))
                    if new_cell.is_on_fire():
                        return "failure"
                    if new_cell is self.button_cell:
                        # Button pressed: fire is instantly extinguished
                        for cell in self.ship.get_on_fire_cells():
                            cell.extinguish()
                        return "success"
    # Move the bot to the next position in the queue
        if q:
            next_pos = q.popleft()
            self.bot.move(next_pos[0], next_pos[1])
            print(f"Bot moved to: ({next_pos[0]}, {next_pos[1]})")

        # Update the fire after the bot has moved
        self.update_fire()

        # Check if the bot is on fire after the fire update
        if self.ship.get_cell(self.bot.row, self.bot.col).is_on_fire():
            print(f"Bot caught on fire after move at: ({self.bot.row}, {self.bot.col})")
            return "failure"

        print("Simulation ongoing...")
        return "ongoing"
        
