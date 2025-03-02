import pygame
import random
from heapq import heappush, heappop
import itertools
from collections import deque

class BotController:
    def __init__(self, bot, env, strategy):
        """
        Class for controlling the bot within the environment
        """
        self.bot = bot
        self.env = env
        self.strategy = strategy
        self.path = []  # Used for Bot 1 (preplanned path)
        if strategy == 1:
            # if strategy is 1, pre-plan the path since we will not re-plan
            self.path = self.plan_path_bot1()

    def plan_path_bot1(self):
        """Plan path from the bot’s start to the button, blocking only the initial fire cell"""
        start, goal = self.bot.cell, self.env.button_cell
        blocked = {self.env.initial_fire_cell}
        return self.a_star(start, goal, blocked)

    def plan_path_bot2(self):
        """Re-plan each timestep, blocking any cells on fire"""
        start, goal = self.bot.cell, self.env.button_cell
        blocked = {cell for cell in self.env.ship.get_on_fire_cells()}
        return self.a_star(start, goal, blocked)

    def plan_path_bot3(self):
        """
        Re-plan each timestep while trying to avoid cells on fire and their adjacent open cells.
        If no path exists with stricter blocking, fall back to only blocking burning cells.
        """
        burning_cells = self.env.ship.get_on_fire_cells()
        blocked_strict = {cell for cell in burning_cells} | {n for cell in burning_cells for n in cell.neighbors if n.is_open()}
        start, goal = self.bot.cell, self.env.button_cell
        path = self.a_star(start, goal, blocked_strict)
        if not path:
            # if no path exists with strict blocking, fall back to only blocking burning cells
            blocked = {cell for cell in burning_cells}
            path = self.a_star(start, goal, blocked)
        return path

    def plan_path_bot4(self):
        """
        Risk-aware planning that considers predicted fire spread.
        This method uses an A* search that incorporates not only the distance to the goal
        (via the Manhattan heuristic) but also a risk term based on the predicted fire arrival time.
        The risk-aware f-score is computed as:
            f = tentative_g + heuristic(neighbor, goal) - (fire_arrival - tentative_g)
          which simplifies to:
            f = 2 * tentative_g + heuristic(neighbor, goal) - fire_arrival
        Moves that would reach a cell after or at the same time as the fire are skipped.
        Returns a list of cells representing the path from the bot's current cell to the button cell.
        """
        start, goal = self.bot.cell, self.env.button_cell
        fire_times = self.predict_fire_spread()

        open_set = [(0, start)]
        came_from = {}
        g_score = {start: 0}

        def heuristic(cell, goal):
            return abs(cell.row - goal.row) + abs(cell.col - goal.col)

        while open_set:
            # Tie-breaking: if multiple nodes share the minimum f-score, choose one at random.
            min_f = open_set[0][0]
            min_indices = [i for i, (f, node) in enumerate(open_set) if f == min_f]
            chosen_idx = random.choice(min_indices)
            current_f, current = open_set.pop(chosen_idx)

            if current == goal:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                # Remove starting cell if present
                if path and path[0] == start:
                    path = path[1:]
                return path

            for neighbor in current.neighbors:
                if not neighbor.is_open():
                    continue
                tentative_g = g_score[current] + 1  # arrival time at neighbor
                fire_arrival = fire_times.get(neighbor, float('inf'))
                if tentative_g >= fire_arrival:
                    # Skip neighbor if the fire would arrive by then (or earlier)
                    continue

                # Risk-aware cost: subtract the safety margin (fire_arrival - tentative_g) to prefer safer moves.
                tentative_f = tentative_g + heuristic(neighbor, goal) - (fire_arrival - tentative_g)
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    open_set.append((tentative_f, neighbor))
                    open_set.sort(key=lambda x: x[0])
        return []

    def a_star(self, start, goal, blocked):
        """
        A* search with random tiebreaking when encountering equal f-scores.
        This is used by Bots 1, 2, and 3.
        """
        open_set = [(0, start)]
        came_from = {}
        g_score = {start: 0}

        def heuristic(a, b):
            return abs(a.row - b.row) + abs(a.col - b.col)

        while open_set:
            min_f = open_set[0][0]
            min_indices = [i for i, (f, _) in enumerate(open_set) if f == min_f]
            chosen_idx = random.choice(min_indices)
            current_f, current = open_set.pop(chosen_idx)

            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                if path and path[0] == start:
                    path = path[1:]
                return path

            for neighbor in current.neighbors:
                if neighbor.is_open() and neighbor not in blocked:
                    tentative_g = g_score[current] + 1
                    if neighbor not in g_score or tentative_g < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g
                        f_score = tentative_g + heuristic(neighbor, goal)
                        open_set.append((f_score, neighbor))
                        open_set.sort(key=lambda x: x[0])
        return []

    def predict_fire_spread(self):
        """
        Predicts the arrival time of fire for each cell using multi-source BFS.
        Returns a dictionary mapping each cell (from self.env.ship) to its predicted fire arrival time.
        Cells that the fire cannot reach will have a value of infinity.
        """
        fire_times = {}
        dimension = self.env.ship.dimension
        # Initialize all cells with infinite arrival time
        for row in range(dimension):
            for col in range(dimension):
                cell = self.env.ship.get_cell(row, col)
                fire_times[cell] = float('inf')
        queue = deque()
        # Start from all cells that are currently on fire.
        for cell in self.env.ship.get_on_fire_cells():
            fire_times[cell] = 0
            queue.append(cell)
        while queue:
            current = queue.popleft()
            current_time = fire_times[current]
            for neighbor in current.neighbors:
                if not neighbor.is_open():
                    continue
                if current_time + 1 < fire_times[neighbor]:
                    fire_times[neighbor] = current_time + 1
                    queue.append(neighbor)
        return fire_times

    def get_direction_from_positions(self, current, next_cell):
        """Convert two consecutive cells into a move direction"""
        if next_cell.row < current.row:
            return "up"
        elif next_cell.row > current.row:
            return "down"
        elif next_cell.col < current.col:
            return "left"
        elif next_cell.col > current.col:
            return "right"
        return None

    def get_random_valid_move(self):
        """Return a random valid move from the bot's current position"""
        valid_moves = [self.get_direction_from_positions(self.bot.cell, neighbor)
                       for neighbor in self.bot.cell.get_open_neighbors()]
        if valid_moves:
            return random.choice(valid_moves)
        return None

    def get_next_move(self):
        """
        Return the next move direction according to the selected strategy. If no path is found,
        return a random valid move even if the adjacent cell is on fire.
        """
        if self.strategy == 0:
            return None
        if self.strategy == 1:
            if not self.path:
                return self.get_random_valid_move()
            next_cell = self.path.pop(0)
            return self.get_direction_from_positions(self.bot.cell, next_cell)
        elif self.strategy == 2:
            path = self.plan_path_bot2()
            if not path:
                return self.get_random_valid_move()
            next_cell = path[0]
            return self.get_direction_from_positions(self.bot.cell, next_cell)
        elif self.strategy == 3:
            path = self.plan_path_bot3()
            if not path:
                return self.get_random_valid_move()
            next_cell = path[0]
            return self.get_direction_from_positions(self.bot.cell, next_cell)
        elif self.strategy == 4:
            path = self.plan_path_bot4()
            if not path:
                return self.get_random_valid_move()
            next_cell = path[0]
            return self.get_direction_from_positions(self.bot.cell, next_cell)
        else:
            return None

    def make_action(self):
        """
        For manual (strategy 0): map arrow-keys to directions.
        For algorithm modes: use the precomputed or re-planned move.
        Returns "ongoing", "success", "failure", or "quit" based on the state of the simulation after the action.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if self.strategy == 0 and event.type == pygame.KEYDOWN:
                key_direction = {
                    pygame.K_UP: "up",
                    pygame.K_DOWN: "down",
                    pygame.K_LEFT: "left",
                    pygame.K_RIGHT: "right"
                }
                direction = key_direction.get(event.key)
                if direction:
                    # if cell after taking direction is valid
                    current = self.bot.cell
                    new_row, new_col = current.row, current.col
                    if direction == "up":
                        new_row -= 1
                    elif direction == "down":
                        new_row += 1
                    elif direction == "left":
                        new_col -= 1
                    elif direction == "right":
                        new_col += 1
                    if self.env.ship.cell_in_bounds(new_row, new_col):
                        target_cell = self.env.ship.get_cell(new_row, new_col)
                        if target_cell.open:
                            # if target cell is open, tick environment with chosen action
                            return self.env.tick(direction)
        if self.strategy != 0:
            direction = self.get_next_move()
            return self.env.tick(direction)
        return "ongoing"
