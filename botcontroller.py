import functools
import math
import pygame
import random
import heapq
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


    def a_star(self, start, goal, blocked):
        """Wrapper for the cached A* function that handles objects to hashable conversion"""
        # Convert objects to hashable types for caching
        blocked_hash = frozenset((cell.row, cell.col) for cell in blocked)
        path_coords = self._cached_a_star(start.row, start.col, goal.row, goal.col, blocked_hash)

        # Convert coordinates back to cell objects
        return [self.env.ship.get_cell(row, col) for row, col in path_coords]


    @functools.lru_cache(maxsize=128)
    def _cached_a_star(self, start_row, start_col, goal_row, goal_col, blocked_hash):
        """Cached version of A* that works with hashable parameters"""
        start = self.env.ship.get_cell(start_row, start_col)
        goal = self.env.ship.get_cell(goal_row, goal_col)
        # Convert the blocked hash back to a set of cells
        blocked = {self.env.ship.get_cell(r, c) for r, c in blocked_hash}

        # A* implementation
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
                # Return coordinates instead of cell objects for the cache
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
        return tuple()  # Empty path


    # === Strategy 4: Expectimax === #
    def plan_path_bot4(self):
        """
        Uses iterative deepening Expectimax search to decide the next move.
        Returns a one-element list containing the best next cell so that
        get_next_move() can convert it into a move direction.
        """
        best_move = self.expectimax_decision(max_depth=5, num_samples=5)
        if best_move is None:
            return []
        return [best_move]

    def expectimax_decision(self, max_depth=5, num_samples=5):
        """
        Iterative deepening expectimax decision that returns the best next cell.
        At each increasing depth, we search over all valid moves from the current cell.
        """
        current_state = (self.bot.cell,
                         frozenset(self.env.ship.get_on_fire_cells()),
                         0)  # state: (bot_cell, fire_set, time)
        best_move = None
        # Iteratively deepen from depth 1 to max_depth.
        for depth in range(1, max_depth + 1):
            best_value = -math.inf
            candidate_move = None
            for neighbor in self.bot.cell.neighbors:
                if not neighbor.is_open():
                    continue
                new_state = (neighbor, current_state[1], current_state[2] + 1)
                value = self.expectimax(new_state, depth, is_bot_turn=False, num_samples=num_samples)
                if value > best_value:
                    best_value = value
                    candidate_move = neighbor
            # Update best move as deeper searches complete.
            if candidate_move is not None:
                best_move = candidate_move
        return best_move

    def expectimax(self, state, depth, is_bot_turn, num_samples):
        """
        Recursive Expectimax search.
        - For the bot (maximizer), it considers all valid moves.
        - For the fire (chance node), it averages over a number of random fire spread samples.
        """
        bot, fire_set, t = state
        if self.is_terminal(state) or depth == 0:
            return self.evaluate(state)
        if is_bot_turn:
            best_val = -math.inf
            for neighbor in bot.neighbors:
                if not neighbor.is_open():
                    continue
                new_state = (neighbor, fire_set, t + 1)
                val = self.expectimax(new_state, depth, False, num_samples)
                best_val = max(best_val, val)
            return best_val
        else:
            total = 0
            for _ in range(num_samples):
                new_fire_set = self.simulate_fire(fire_set)
                new_state = (bot, new_fire_set, t)
                total += self.expectimax(new_state, depth - 1, True, num_samples)
            return total / num_samples

    def is_terminal(self, state):
        """
        A state is terminal if the bot has reached the button (win)
        or if the bot’s cell is on fire (loss).
        """
        bot, fire_set, t = state
        return (bot == self.env.button_cell) or (bot in fire_set)

    def evaluate(self, state):
        """
        Evaluation function for non-terminal states.
        If the bot has reached the button or is on fire, returns a high reward or penalty.
        Otherwise, if a safe A* path exists (blocking cells that are on fire),
        its length is used to compute the evaluation. This rewards states with a safe (even if longer)
        path to the button. If no safe path exists, falls back to a Manhattan distance heuristic.
        """
        bot, fire_set, t = state
        if bot == self.env.button_cell:
            return 10000 - t  # Big reward for reaching the button quickly.
        if bot in fire_set:
            return -10000    # Big penalty for being caught by the fire.

        manhattan = abs(bot.row - self.env.button_cell.row) + abs(bot.col - self.env.button_cell.col)
        return - (manhattan * 20) - t

    def simulate_fire(self, fire_set):
        """
        Simulates one step of fire spread.
        For each open neighbor of a burning cell, the chance of catching fire is:
            p = 1 - (1 - q)^(# burning neighbors)
        Returns the new set of burning cells as a frozenset.
        """
        new_fire_set = set(fire_set)
        candidate_cells = set()
        for cell in fire_set:
            for neighbor in cell.neighbors:
                if neighbor.is_open() and neighbor not in new_fire_set:
                    candidate_cells.add(neighbor)
        for cell in candidate_cells:
            burning_neighbors = sum(1 for n in cell.neighbors if n in fire_set)
            if burning_neighbors > 0:
                p = 1 - (1 - self.env.q) ** burning_neighbors
                if random.random() < p:
                    new_fire_set.add(cell)
        return frozenset(new_fire_set)

    def predict_fire_spread(self):
        """
        Predicts the arrival time of fire for each cell using single-source BFS.
        Uses cached results if available.
        """
        fire_times = {cell: float('inf') for row in self.env.ship.grid for cell in row}
        queue = deque()
        initial_fire = self.env.initial_fire_cell
        fire_times[initial_fire] = 0
        queue.append(initial_fire)

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

    # === End Strategy 4: Expectimax === #

    # === Strategy 5: More Risk-Aware A* Planning === #
    def plan_path_bot5(self):
        """
        Risk-aware A* planning strategy (Bot 5) that considers predicted fire spread.
        Returns a list of (row, col) tuples representing the path from the bot's current cell to the button.
        """
        start = (self.bot.cell.row, self.bot.cell.col)
        goal = (self.env.button_cell.row, self.env.button_cell.col)
        rows = self.env.ship.dimension
        cols = self.env.ship.dimension

        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.heuristic(start, goal)}
        dx = [-1, 0, 1, 0]
        dy = [0, 1, 0, -1]
        path = []
        # Predict fire spread using the initial fire cell
        fire_time = self.predict_fire_spread_risk([(self.env.initial_fire_cell.row, self.env.initial_fire_cell.col)])
        arrival_time = 0

        while open_set:
            current = heapq.heappop(open_set)[1]
            if current == goal:
                # Reconstruct path from goal to start
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                break

            for i in range(4):
                neighbor = (current[0] + dx[i], current[1] + dy[i])
                if 0 <= neighbor[0] < rows and 0 <= neighbor[1] < cols:
                    cell = self.env.ship.get_cell(neighbor[0], neighbor[1])
                    # Only consider cells that are open, not currently on fire, and with no burning neighbors
                    if cell.is_open() and (not cell.is_on_fire()) and cell.count_burning_neighbors() == 0:
                        tentative_g_score = g_score[current] + 1
                        arrival_time += 1
                        fire_arrival = fire_time[neighbor[0]][neighbor[1]]
                        if arrival_time >= fire_arrival:
                            continue
                        if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                            came_from[neighbor] = current
                            g_score[neighbor] = tentative_g_score
                            new_f = tentative_g_score + self.heuristic(neighbor, goal) + (fire_arrival - arrival_time)
                            f_score[neighbor] = new_f
                            heapq.heappush(open_set, (new_f, neighbor))
        return path

    def predict_fire_spread_risk(self, fire_starts):
        """
        Predicts the arrival time of fire for each cell (as a grid matrix) using a BFS.
        Args:
            fire_starts: A list of (row, col) tuples for initial fire positions.
        Returns:
            A 2D list (matrix) where each entry [i][j] is the predicted time of fire arrival.
        """
        dimension = self.env.ship.dimension
        fire_time = [[float('inf')] * dimension for _ in range(dimension)]
        queue = deque()

        for x, y in fire_starts:
            fire_time[x][y] = 0
            queue.append((x, y, 0))

        while queue:
            x, y, t = queue.popleft()
            for neighbor in self.env.ship.get_cell(x, y).neighbors:
                nx, ny = neighbor.row, neighbor.col
                # Use open cells as valid for fire spread
                if neighbor.is_open() and fire_time[nx][ny] == float('inf'):
                    fire_time[nx][ny] = t + 1
                    queue.append((nx, ny, t + 1))
        return fire_time

    @staticmethod
    def heuristic(a, b):
        """Calculate the Manhattan distance heuristic between two (row, col) points."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    # === End New Strategy 5 === #

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
        elif self.strategy == 5:
            # Use the new risk-aware A* planning strategy.
            path = self.plan_path_bot5()
            if not path:
                return self.get_random_valid_move()
            next_pos = path[0]
            # If the first cell in the path is the current cell, choose the following cell (if available)
            if next_pos[0] == self.bot.cell.row and next_pos[1] == self.bot.cell.col and len(path) > 1:
                next_pos = path[1]
            return self.get_direction_from_positions(self.bot.cell, self.env.ship.get_cell(next_pos[0], next_pos[1]))
        else:
            return None

    def make_action(self):
        """
        For manual (strategy 0): map arrow-keys to directions.
        For algorithm modes: use the precomputed or re-planned move.
        Returns "ongoing", "success", "failure", or "quit" based on the state of the simulation after the action.
        """
        if self.strategy != 0:
            direction = self.get_next_move()
            return self.env.tick(direction)
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
        return "ongoing"
