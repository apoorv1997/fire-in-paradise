import functools
import math
import pygame
import random
import heapq
from collections import deque

class BotController:
    def __init__(self, bot, env, strategy):
        """
        Class for controlling the bot within the environment.
        :param bot: The bot object.
        :param env: The environment, which holds the ship, button cell, fire cell, etc.
        :param strategy: The strategy number (0 for manual, 1-5 for algorithms).
        """
        self.bot = bot
        self.env = env
        self.strategy = strategy
        self.path = []  # Used for Bot 1 (preplanned path)
        if strategy == 1:
            # Strategy 1: pre-plan the path (no re-planning)
            self.path = self.plan_path_bot1()

    def plan_path_bot1(self):
        """Plan a path from the bot's start cell to the button, blocking only the initial fire cell."""
        start, goal = self.bot.cell, self.env.button_cell
        blocked = {self.env.initial_fire_cell}
        return self.a_star(start, goal, blocked)

    def plan_path_bot2(self):
        """Re-plan each timestep blocking any cells that are on fire."""
        start, goal = self.bot.cell, self.env.button_cell
        blocked = {cell for cell in self.env.ship.get_on_fire_cells()}
        return self.a_star(start, goal, blocked)

    def plan_path_bot3(self):
        """
        Re-plan each timestep while trying to avoid cells on fire and their adjacent open cells.
        If no path exists with strict blocking, fall back to only blocking burning cells.
        """
        burning_cells = self.env.ship.get_on_fire_cells()
        blocked_strict = {cell for cell in burning_cells} | {
            n for cell in burning_cells for n in cell.neighbors if n.is_open()
        }
        start, goal = self.bot.cell, self.env.button_cell
        path = self.a_star(start, goal, blocked_strict)
        if not path:
            blocked = {cell for cell in burning_cells}
            path = self.a_star(start, goal, blocked)
        return path


    # ----------------------------------------------------------------
    # Strategy 4: More-Risk A*
    # ----------------------------------------------------------------
    def plan_path_bot4(self, q):
        """
        Replicates the 'a_star_more_risk' logic to compute a path from the bot's
        current cell to the button while considering fire spread.

        Returns a list of (row, col) tuples representing the path,
        or an empty list if no path is found.
        """
        # Get current position and goal
        m, n = self.bot.cell.row, self.bot.cell.col
        # goal = (self.env.button_cell.row, self.env.button_cell.col)
        start = self.env.ship.get_cell(m, n)
        goal = self.env.ship.get_cell(self.env.button_cell.row, self.env.button_cell.col)
        #blocked = {self.env.ship.get_cell(r, c) for r, c in blocked_hash}
        open_heap = []
        g_score = {start: 0}
        came_from = {}

        fire_time = self.predict_fire_spread([(self.env.initial_fire_cell.row,
                                               self.env.initial_fire_cell.col)])
        arrival_time = 0
        def heuristic(a, b):
            return abs(a.row - b.row) + abs(a.col - b.col)

        counter = 0
        initial_f = heuristic(start, goal)
        heapq.heappush(open_heap, (initial_f, counter, start))
        counter += 1

        while open_heap:
            current_f, _, current = heapq.heappop(open_heap)
            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                if path and path[0] == start:
                    path = path[1:]
                return tuple((cell.row, cell.col) for cell in path)
            for neighbor in current.neighbors:
                if neighbor.is_open() and neighbor.is_open() and (not neighbor.is_on_fire()) and neighbor.count_burning_neighbors() == 0:
                    tentative_g = g_score[current] + 1
                    arrival_time = tentative_g
                    fire_arrival = fire_time[neighbor.row][neighbor.col]
                    if neighbor not in g_score or tentative_g < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g
                        fire_weight = 0.02
                        f_score = tentative_g + heuristic(neighbor, goal) - fire_weight * (fire_arrival)
                        heapq.heappush(open_heap, (f_score, counter, neighbor))
                        counter += 1
        return tuple()
        #path = self.smooth_path(path)
        return path


    def smooth_path(self, path):
        """
        Smooth the path to avoid unnecessary detours.
        """
        if not path:
            return path

        smoothed_path = [path[0]]
        for i in range(1, len(path) - 1):
            prev = smoothed_path[-1]
            curr = path[i]
            next = path[i + 1]
            if not (prev[0] == next[0] or prev[1] == next[1]):
                smoothed_path.append(curr)
        smoothed_path.append(path[-1])

        return smoothed_path

    def predict_fire_spread(self, fire_starts):
        """
        BFS-based fire spread prediction.
        Returns a 2D matrix (list of lists) of fire arrival times.
        """
        dim = self.env.ship.dimension
        fire_time = [[float('inf')] * dim for _ in range(dim)]
        queue = deque()

        for x, y in fire_starts:
            fire_time[x][y] = 0
            queue.append((x, y, 0))

        while queue:
            x, y, t = queue.popleft()
            for neighbor_cell in self.env.ship.get_cell(x, y).neighbors:
                nx, ny = neighbor_cell.row, neighbor_cell.col
                # Use the snippet condition: if not open and not yet assigned a time.
                if (not self.env.ship.get_cell(nx, ny).is_open()) and (fire_time[nx][ny] == float('inf')):
                    fire_time[nx][ny] = t + 1
                    queue.append((nx, ny, t + 1))
        return fire_time

    @staticmethod
    def manhattan_distance(a, b):
        """Manhattan distance"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    # ----------------------------------------------------------------


    def a_star(self, start, goal, blocked):
        """
        Cached A* search to find a path from start to goal, avoiding blocked cells.
        Returns a list of cell objects.
        """
        blocked_hash = frozenset((cell.row, cell.col) for cell in blocked)
        path_coords = self._cached_a_star(start.row, start.col, goal.row, goal.col, blocked_hash)
        return [self.env.ship.get_cell(r, c) for r, c in path_coords]


    @functools.lru_cache(maxsize=128)
    def _cached_a_star(self, start_row, start_col, goal_row, goal_col, blocked_hash):
        """
        Cached version of A* that works with hashable parameters.
        """
        start = self.env.ship.get_cell(start_row, start_col)
        goal = self.env.ship.get_cell(goal_row, goal_col)
        blocked = {self.env.ship.get_cell(r, c) for r, c in blocked_hash}

        open_heap = []
        g_score = {start: 0}
        came_from = {}

        def heuristic(a, b):
            return abs(a.row - b.row) + abs(a.col - b.col)

        counter = 0
        initial_f = heuristic(start, goal)
        heapq.heappush(open_heap, (initial_f, counter, start))
        counter += 1

        while open_heap:
            current_f, _, current = heapq.heappop(open_heap)
            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                if path and path[0] == start:
                    path = path[1:]
                return tuple((cell.row, cell.col) for cell in path)
            for neighbor in current.neighbors:
                if neighbor.is_open() and neighbor not in blocked:
                    tentative_g = g_score[current] + 1
                    if neighbor not in g_score or tentative_g < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g
                        f_score = tentative_g + heuristic(neighbor, goal)
                        heapq.heappush(open_heap, (f_score, counter, neighbor))
                        counter += 1
        return tuple()

    def get_direction_from_positions(self, current, next_cell):
        """Convert two consecutive cells into a move direction."""
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
        """Return a random valid move from the bot's current position."""
        valid_moves = [self.get_direction_from_positions(self.bot.cell, neighbor)
                       for neighbor in self.bot.cell.get_open_neighbors()]
        if valid_moves:
            return random.choice(valid_moves)
        return None

    def get_next_move(self, q):
        """
        Return the next move direction according to the selected strategy.
        If no valid path is found, return a random valid move.
        """
        if self.strategy == 0:
            return None
        elif self.strategy == 1:
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
            path = self.plan_path_bot4(q)
            if not path:
                return self.get_random_valid_move()
            next_rc = path[0]
            if next_rc == (self.bot.cell.row, self.bot.cell.col) and len(path) > 1:
                next_rc = path[1]
            return self.get_direction_from_positions(self.bot.cell,
                                                     self.env.ship.get_cell(next_rc[0], next_rc[1]))
        else:
            return None

    def make_action(self, q):
        """
        For manual control (strategy 0), process arrow keys.
        For algorithmic strategies, compute the next move and call env.tick(direction).
        """
        if self.strategy != 0:
            direction = self.get_next_move(q)
            return self.env.tick(direction)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                keymap = {
                    pygame.K_UP: "up",
                    pygame.K_DOWN: "down",
                    pygame.K_LEFT: "left",
                    pygame.K_RIGHT: "right",
                }
                direction = keymap.get(event.key)
                if direction:
                    current = self.bot.cell
                    new_r, new_c = current.row, current.col
                    if direction == "up":
                        new_r -= 1
                    elif direction == "down":
                        new_r += 1
                    elif direction == "left":
                        new_c -= 1
                    elif direction == "right":
                        new_c += 1
                    if self.env.ship.cell_in_bounds(new_r, new_c):
                        target_cell = self.env.ship.get_cell(new_r, new_c)
                        if target_cell.open:
                            return self.env.tick(direction)
        return "ongoing"
