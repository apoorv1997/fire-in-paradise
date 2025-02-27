import pygame
import random
from heapq import heappush, heappop
import itertools

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
        start, goal = self.bot_cell, self.env.button_cell
        blocked = {cell for cell in self.env.ship.get_on_fire_cells()}
        return self.a_star(start, goal, blocked)

    def plan_path_bot3(self):
        """
        Re-plan each timestep while trying to avoid cells on fire and their adjacent open cells.
        If no path exists with stricter blocking, fall back to only blocking burning cells
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
        """
        A* search with random tiebreaking when encountering equal f-scores
        """
        # Initialize open set with tuple containing f_score (0 initially) and start node
        open_set = [(0, start)]  # (f_score, node)

        # Dictionary to track most efficient previous step for each node
        came_from = {}

        # Dictionary to store cost of cheapest path from start to each node
        g_score = {start: 0}

        # Define the heuristic function: Manhattan distance between two nodes.
        def heuristic(a, b):
            return abs(a.row - b.row) + abs(a.col - b.col)

        # Continue searching while there are available nodes
        while open_set:
            # find min f_score in open set
            min_f = open_set[0][0]
            # all indices that have same min f_score
            min_indices = [i for i, (f, _) in enumerate(open_set) if f == min_f]
            # Randomly choose index among those with the same f_score to break ties
            chosen_idx = random.choice(min_indices)
            # Pop selected node from the open set
            current_f, current = open_set.pop(chosen_idx)

            # Check if the goal has been reached
            if current == goal:
                # Reconstruct path by traversing came_from dictionary
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()  # Reverse path to get correct order from start to goal
                # Remove starting node from the path if present
                if path and path[0] == start:
                    path = path[1:]
                return path

            # Iterate through all neighboring nodes of current node
            for neighbor in current.neighbors:
                # Process only open neighbors not in the blocked set
                if neighbor.is_open() and neighbor not in blocked:
                    # Calculate tentative g_score for neighbor
                    tentative_g = g_score[current] + 1

                    # If path to neighbor better than any previous one, update
                    if neighbor not in g_score or tentative_g < g_score[neighbor]:
                        came_from[neighbor] = current  # Record the current node as the best predecessor
                        g_score[neighbor] = tentative_g  # Update g_score for neighbor
                        # Calculate f_score as sum of g_score and heuristic estimate to the goal
                        f_score = tentative_g + heuristic(neighbor, goal)
                        open_set.append((f_score, neighbor))
                        # Keep the open_set sorted by f_score so that the smallest f_score is at the beginning
                        open_set.sort(key=lambda x: x[0])  # Sort only by f_score

        # If goal never reached, return an empty path
        return []


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
        valid_moves = [self.get_direction_from_positions(self.bot.cell, neighbor) for neighbor in self.bot.cell.get_open_neighbors()]
        if valid_moves:
            return random.choice(valid_moves)
        return None


    def get_next_move(self):
        """
        Return the next move direction according to the selected strategy. If no path, return a random valid move
        even if adjacent cell is on fire
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
        else:
            return None

    def make_action(self):
        """
        For manual (strategy 0): map arrow-keys to directions
        For algorithm modes: use precomputed or re-planned move
        Returns "ongoing", "success", "failure", or "quit" based on state of simulation after action
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
            # if not manual mode, get next move from chosen strategy and tick environment with that action
            direction = self.get_next_move()
            return self.env.tick(direction)
        return "ongoing"
