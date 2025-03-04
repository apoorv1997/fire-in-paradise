import functools
import math
import pygame
import random
import heapq


class BotController:
    def __init__(self, bot, env, strategy):
        self.bot = bot
        self.env = env
        self.strategy = strategy
        if strategy == 1:
            self.path = self.plan_path_bot1() # Used for Bot 1 (preplanned path)

        # Bot 4 re-planning frequency
        self.replan_interval = 2  # re-plan every 2 moves
        self.cached_path = []     # path to use when not re-planning
        self.moves_since_replan = 0

        # Cache (used in strategy 4)
        if self.strategy == 4:
            # Cache for fire probabilities
            self.fire_probs_cache = {}
            # Cache for risk-aware A* path results
            self.risk_path_cache = {}

    def plan_path_bot1(self):
        """Plan a path from the bot to the button, ignoring future fire spread."""
        start, goal = self.bot.cell, self.env.button_cell
        blocked = {self.env.initial_fire_cell}
        return self.a_star(start, goal, blocked)

    def plan_path_bot2(self):
        """Plan a path from the bot to the button, blocking cells that are on fire."""
        start, goal = self.bot.cell, self.env.button_cell
        blocked = {cell for cell in self.env.ship.get_on_fire_cells()}
        return self.a_star(start, goal, blocked)

    def plan_path_bot3(self):
        """Plan a path from the bot to the button, blocking cells that are on fire and their neighbors if viable"""
        burning_cells = self.env.ship.get_on_fire_cells()
        blocked_strict = {cell for cell in burning_cells} | {
            n for cell in burning_cells for n in cell.neighbors if n.is_open()
        }
        start, goal = self.bot.cell, self.env.button_cell
        path = self.a_star(start, goal, blocked_strict)
        if not path: # If no path found, try again with only burning cells blocked
            blocked = {cell for cell in burning_cells}
            path = self.a_star(start, goal, blocked)
        return path

    def plan_path_bot4(self):
        """
        Plan a risk-aware path using A* that minimizes the probability of encountering fire
        """
        start = self.bot.cell
        goal = self.env.button_cell
        if start == goal:
            return []
        max_steps = self.manhattan_distance(start, goal) * 2  # Buffer to account for detours

        ship = self.env.ship
        current_fire_cells = frozenset((cell.row, cell.col) for cell in ship.get_on_fire_cells())
        closed_cells = frozenset((cell.row, cell.col) for cell in ship.all_cells() if not cell.is_open())
        risk_key = (start.row, start.col, goal.row, goal.col, max_steps, self.env.q, current_fire_cells, closed_cells)

        # If computed risk-aware path for this state return it
        if risk_key in self.risk_path_cache:
            return self.risk_path_cache[risk_key]

        fire_probs = self.compute_fire_probabilities(max_steps) # Compute fire probabilities
        path = self.risk_aware_a_star(start, goal, fire_probs, max_steps) # Compute the path
        self.risk_path_cache[risk_key] = path # Cache the result
        return path

    def compute_fire_probabilities(self, max_steps):
        """Computes probability of each cell being on fire for each step up to max_steps"""
        ship = self.env.ship
        current_fire_cells = frozenset((cell.row, cell.col) for cell in ship.get_on_fire_cells())
        closed_cells = frozenset((cell.row, cell.col) for cell in ship.all_cells() if not cell.is_open())
        key = (max_steps, self.env.q, current_fire_cells, closed_cells) # Cache key

        # If computed fire probabilities for this state return them
        if key in self.fire_probs_cache:
            return self.fire_probs_cache[key]

        fire_probs = {}
        # Initialize fire probabilities
        for cell in ship.all_cells():
            fire_probs[cell] = [0.0] * (max_steps + 1)
            if (cell.row, cell.col) in current_fire_cells:
                fire_probs[cell][0] = 1.0

        # Compute fire probabilities
        for s in range(1, max_steps + 1):
            for cell in ship.all_cells():
                # if cell is already on fire, it will remain on fire
                if fire_probs[cell][s-1] >= 1.0:
                    fire_probs[cell][s] = 1.0
                else:
                    # Calculate probability of ignition based on neighbors
                    prob_ignition = 1.0
                    for neighbor in cell.neighbors:
                        if neighbor.is_open():
                            prob_ignition *= (1.0 - self.env.q * fire_probs[neighbor][s-1])
                    prob_ignition = 1.0 - prob_ignition
                    # Update fire probability
                    fire_probs[cell][s] = fire_probs[cell][s-1] + (1.0 - fire_probs[cell][s-1]) * prob_ignition

        self.fire_probs_cache[key] = fire_probs # Cache the result
        return fire_probs

    def risk_aware_a_star(self, start, goal, fire_probs, max_steps):
        """A* search that prioritizes paths with minimal accumulated fire risk (via survival probability)"""
        open_heap = []
        visited = {}
        start_key = (start.row, start.col)
        visited[start_key] = (0.0, 0, None)  # (accumulated_risk, path_length, parent)
        initial_heuristic = self.manhattan_distance(start, goal)
        # Push initial state to open heap
        heapq.heappush(open_heap, (initial_heuristic, start.row, start.col, 0.0, 0))

        while open_heap:
            current_priority, r, c, acc_risk, path_len = heapq.heappop(open_heap) # priority, row, col, accumulated risk, path length
            current_cell = self.env.ship.get_cell(r, c)
            if current_cell == goal:
                # Reconstruct path
                path = []
                current = current_cell
                while True:
                    path.append((current.row, current.col))
                    # visited {} stores (accumulated risk, path length, parent) for cell coordinate tuples
                    parent_info = visited.get((current.row, current.col))
                    if not parent_info or parent_info[2] is None: # No parent
                        break
                    current = parent_info[2]
                path.reverse()
                # Remove start cell from path since we don't want to move there
                if path and path[0] == (start.row, start.col):
                    path = path[1:]
                return path

            # Explore neighbors
            for neighbor in current_cell.get_open_neighbors():
                nr, nc = neighbor.row, neighbor.col
                new_path_len = path_len + 1
                arrival_step = new_path_len if new_path_len <= max_steps else max_steps

                # Get fire probability at arrival time
                p = fire_probs[neighbor][arrival_step]
                if p >= 1.0 - 1e-9:  # Cell will be on fire
                    continue

                # Calculate risk contribution (-log survival probability discussed in report)
                risk_contribution = 0.0 if p <= 0 else -math.log(1 - p)
                new_acc_risk = acc_risk + risk_contribution

                # Calculate priority: weighted risk + path length + heuristic
                risk_weight = 0.8 if self.env.q >= 0.7 else 2
                new_priority = risk_weight * new_acc_risk + new_path_len + (0.7*self.manhattan_distance(neighbor, goal))

                neighbor_key = (nr, nc)
                current_best_risk = visited.get(neighbor_key, (float('inf'), 0, None))[0]
                if new_acc_risk < current_best_risk: # Only add to open heap if this path is better
                    visited[neighbor_key] = (new_acc_risk, new_path_len, current_cell)
                    heapq.heappush(open_heap, (new_priority, nr, nc, new_acc_risk, new_path_len))

        return []  # No path found

    def manhattan_distance(self, a, b):
        """Manhattan distance heuristic between two cells"""
        return abs(a.row - b.row) + abs(a.col - b.col)

    def a_star(self, start, goal, blocked):
        """A* search algorithm wrapper that converts inputs into a blocked hash, allowing for caching"""
        blocked_hash = frozenset((cell.row, cell.col) for cell in blocked)
        path_coords = self._cached_a_star(start.row, start.col, goal.row, goal.col, blocked_hash)
        return [self.env.ship.get_cell(r, c) for r, c in path_coords]

    @functools.lru_cache(maxsize=2000)
    def _cached_a_star(self, start_row, start_col, goal_row, goal_col, blocked_hash):
        """A* search algorithm implementation"""
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
            current_f, _, current = heapq.heappop(open_heap) # f_score, counter for tie-breaking, current cell
            if current == goal: # reconstruct path if goal reached
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                if path and path[0] == start: # remove start cell from path since we don't want to move there
                    path = path[1:]
                return tuple((cell.row, cell.col) for cell in path)
            for neighbor in current.neighbors: # explore neighbors
                if neighbor.is_open() and neighbor not in blocked:
                    tentative_g = g_score[current] + 1 # +1 cost for each step
                    if neighbor not in g_score or tentative_g < g_score[neighbor]:
                        # update path if this is the best path so far
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g
                        f_score = tentative_g + heuristic(neighbor, goal)
                        heapq.heappush(open_heap, (f_score, counter, neighbor))
                        counter += 1
        return tuple()

    def get_direction_from_positions(self, current, next_cell):
        """Get direction from current cell to next cell"""
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
        """Get a random valid move from the current cell"""
        valid_moves = [self.get_direction_from_positions(self.bot.cell, neighbor)
                       for neighbor in self.bot.cell.get_open_neighbors()]
        if valid_moves:
            return random.choice(valid_moves)
        return None

    def get_next_move(self):
        """Get the next move based on the selected strategy"""
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
            # Replan every replan_interval moves, otherwise use cached path
            if self.moves_since_replan >= self.replan_interval or not self.cached_path:
                self.cached_path = self.plan_path_bot4()
                self.moves_since_replan = 0
            if not self.cached_path:
                return self.get_random_valid_move()

            # Try to get a valid next cell from the cached path
            valid_next_cell = None
            while self.cached_path and not valid_next_cell:
                next_rc = self.cached_path[0]
                next_cell = self.env.ship.get_cell(next_rc[0], next_rc[1])

                # Check if next_cell is adjacent to current cell
                if next_cell in self.bot.cell.get_open_neighbors():
                    valid_next_cell = next_cell
                    self.cached_path.pop(0)  # Remove cell from the path, this cell will be moved to
                else:
                    # The path is no longer valid, so re-plan
                    self.cached_path = self.plan_path_bot4()
                    if not self.cached_path:
                        return self.get_random_valid_move()

            if valid_next_cell:
                self.moves_since_replan += 1
                return self.get_direction_from_positions(self.bot.cell, valid_next_cell)
            else:
                return self.get_random_valid_move()
        else:
            return None

    def make_action(self):
        """Make an action based on the selected strategy"""
        if self.strategy != 0: # algorithmic control
            direction = self.get_next_move()
            return self.env.tick(direction)

        # else: manual control
        for event in pygame.event.get():
            # wait for and process user input
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
