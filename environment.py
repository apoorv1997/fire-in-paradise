from collections import deque
import random
import matplotlib.pyplot as plt
import heapq
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
        bot_cell, self.button_cell, self.fire_cell = random.sample(open_cells, 3)
        print(bot_cell,self.fire_cell)
        self.fire_cell.ignite()
        self.bot = Bot(ship, bot_cell.row, bot_cell.col)
        self.queue = deque()
        # pre calculate path after env creation
        self.path = self.bfs_shortest_path()

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

    def bfs_shortest_path(self):
        rows, cols = self.ship.dimension, self.ship.dimension
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Up, Down, Left, Right
        bot_pos = (self.bot.row, self.bot.col)
        button_pos = (self.button_cell.row, self.button_cell.col)
        queue = deque([(bot_pos, [])])  # Store (current position, path taken)
        visited = set()
        visited.add(bot_pos)
        
        while queue:
            (x, y), path = queue.popleft()
            
            if (x, y) == button_pos:
                return path  # Return the shortest path
            
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < rows and 0 <= ny < cols and self.ship.get_cell(nx, ny).is_open() and (nx, ny) not in visited:
                    queue.append(((nx, ny), path + [(nx, ny)]))
                    visited.add((nx, ny))
        
        return None
    

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

        if self.path:
            next_pos = self.path.pop(0)
        self.bot.move(next_pos[0], next_pos[1])
        print(f"Bot moved to: ({next_pos[0]}, {next_pos[1]})")

        self.update_fire()

        if self.ship.get_cell(self.bot.row, self.bot.col).is_on_fire():
            print(f"Bot caught on fire after move at: ({self.bot.row}, {self.bot.col})")
            return "failure"
        if self.ship.get_cell(self.bot.row, self.bot.col) is self.button_cell:
            # Button pressed: fire is instantly extinguished
            for cell in self.ship.get_on_fire_cells():
                cell.extinguish()
            return "success"
        
        print("Simulation ongoing...")
        return "ongoing"


    def tick_using_a(self):
        """Returns:
            A string indicating the simulation status:
            - "ongoing" if the simulation should continue,
            - "success" if the bot has reached the button (and the fire is extinguished),
            - "failure" if the bot is caught by the fire.
        """
        m, n = self.bot.row, self.bot.col
        goal = (self.button_cell.row, self.button_cell.col)

        open_set = [(0, (m, n))]
        heapq.heappush(open_set, (0, (m, n)))

        came_from = {}
        g_score = { (m, n): 0 }
        f_score = { (m, n): self.heuristic((m, n), goal) }

        dx = [-1, 0, 1, 0]
        dy = [0, 1, 0, -1]

        rows, cols = self.ship.dimension, self.ship.dimension

        path = []
        while open_set:
            current = heapq.heappop(open_set)[1]

            if current == goal:
                # Reconstruct path and move bot
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()

            for i in range(4):
                neighbor = (current[0] + dx[i], current[1] + dy[i])
                if 0 <= neighbor[0] < rows and 0 <= neighbor[1] < cols and self.ship.get_cell(neighbor[0], neighbor[1]).is_open() and not self.ship.get_cell(neighbor[0], neighbor[1]).is_on_fire():
                    tentative_g_score = g_score[current] + 1
                    if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g_score
                        f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, goal)
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))

        # Update the fire after the bot has moved
        print(f"open set: ({open_set})")
        if path:
            next_pos = path.pop(0)
            if next_pos[0] == self.bot.row and next_pos[1] == self.bot.col:
                print(f"path to take: ({path})")
                next_pos = path.pop(0)
        self.bot.move(next_pos[0], next_pos[1])
        print(f"Bot moved to: ({next_pos[0]}, {next_pos[1]})")
        self.update_fire()

        if self.ship.get_cell(self.bot.row, self.bot.col) is self.button_cell:
            # Button pressed: fire is instantly extinguished
            for cell in self.ship.get_on_fire_cells():
                cell.extinguish()
            return "success"
        # Check if the bot is on fire after the fire update
        if self.ship.get_cell(self.bot.row, self.bot.col).is_on_fire():
            print(f"Bot caught on fire after move at: ({self.bot.row}, {self.bot.col})")
            return "failure"

        print("Simulation ongoing...")
        return "ongoing"
    
    def a_star_bot3(self):
        """Returns:
            A string indicating the simulation status:
            - "ongoing" if the simulation should continue,
            - "success" if the bot has reached the button (and the fire is extinguished),
            - "failure" if the bot is caught by the fire.
        """
        m, n = self.bot.row, self.bot.col
        goal = (self.button_cell.row, self.button_cell.col)

        open_set = [(0, (m, n))]
        heapq.heappush(open_set, (0, (m, n)))

        came_from = {}
        g_score = { (m, n): 0 }
        f_score = { (m, n): self.heuristic((m, n), goal) }

        dx = [-1, 0, 1, 0]
        dy = [0, 1, 0, -1]

        rows, cols = self.ship.dimension, self.ship.dimension

        path = []
        while open_set:
            current = heapq.heappop(open_set)[1]

            if current == goal:
                # Reconstruct path and move bot
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()

            for i in range(4):
                neighbor = (current[0] + dx[i], current[1] + dy[i])
                if 0 <= neighbor[0] < rows and 0 <= neighbor[1] < cols and self.ship.get_cell(neighbor[0], neighbor[1]).is_open() and not self.ship.get_cell(neighbor[0], neighbor[1]).is_on_fire() and self.ship.get_cell(neighbor[0], neighbor[1]).count_burning_neighbors() == 0:
                    tentative_g_score = g_score[current] + 1
                    if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g_score
                        f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, goal)
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))

        # Update the fire after the bot has moved
        print(f"open set: ({open_set})")
        if path:
            next_pos = path.pop(0)
            if next_pos[0] == self.bot.row and next_pos[1] == self.bot.col:
                print(f"path to take: ({path})")
                next_pos = path.pop(0)
                
            self.bot.move(next_pos[0], next_pos[1])
            print(f"Bot moved to: ({next_pos[0]}, {next_pos[1]})")
        self.update_fire()

        if self.ship.get_cell(self.bot.row, self.bot.col) is self.button_cell:
            # Button pressed: fire is instantly extinguished
            for cell in self.ship.get_on_fire_cells():
                cell.extinguish()
            return "success"
        # Check if the bot is on fire after the fire update
        if self.ship.get_cell(self.bot.row, self.bot.col).is_on_fire():
            print(f"Bot caught on fire after move at: ({self.bot.row}, {self.bot.col})")
            return "failure"

        print("Simulation ongoing...")
        return "ongoing"
    

    def a_star_more_risk(self):
        """Returns:
            A string indicating the simulation status:
            - "ongoing" if the simulation should continue,
            - "success" if the bot has reached the button (and the fire is extinguished),
            - "failure" if the bot is caught by the fire.
        """
        m, n = self.bot.row, self.bot.col
        goal = (self.button_cell.row, self.button_cell.col)

        open_set = [(0, (m, n))]
        heapq.heappush(open_set, (0, (m, n)))

        came_from = {}
        g_score = { (m, n): 0 }
        f_score = { (m, n): self.heuristic((m, n), goal) }

        dx = [-1, 0, 1, 0]
        dy = [0, 1, 0, -1]

        rows, cols = self.ship.dimension, self.ship.dimension

        path = []

        fire_time = self.predict_fire_spread([(self.fire_cell.row, self.fire_cell.col)])
        arrival_time = 0
        while open_set:
            current = heapq.heappop(open_set)[1]

            if current == goal:
                # Reconstruct path and move bot
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
            
            print(f"current: {current}")
            for i in range(4):
                neighbor = (current[0] + dx[i], current[1] + dy[i])
                if 0 <= neighbor[0] < rows and 0 <= neighbor[1] < cols and self.ship.get_cell(neighbor[0], neighbor[1]).is_open() and not self.ship.get_cell(neighbor[0], neighbor[1]).is_on_fire() and self.ship.get_cell(neighbor[0], neighbor[1]).count_burning_neighbors() == 0:
                    tentative_g_score = g_score[current] + 1
                    arrival_time+=1
                    fire_arrival = fire_time[neighbor[0]][neighbor[1]]
                    if arrival_time >= fire_arrival:
                        continue
                    if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g_score
                        f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, goal) + (fire_arrival - arrival_time)
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))

        # Update the fire after the bot has moved
        print(f"open set: ({open_set})")
        if path:
            next_pos = path.pop(0)
            if next_pos[0] == self.bot.row and next_pos[1] == self.bot.col:
                print(f"path to take: ({path})")
                next_pos = path.pop(0)
                
            self.bot.move(next_pos[0], next_pos[1])
            print(f"Bot moved to: ({next_pos[0]}, {next_pos[1]})")
        self.update_fire()

        if self.ship.get_cell(self.bot.row, self.bot.col) is self.button_cell:
            # Button pressed: fire is instantly extinguished
            for cell in self.ship.get_on_fire_cells():
                cell.extinguish()
            return "success"
        # Check if the bot is on fire after the fire update
        if self.ship.get_cell(self.bot.row, self.bot.col).is_on_fire():
            print(f"Bot caught on fire after move at: ({self.bot.row}, {self.bot.col})")
            return "failure"

        print("Simulation ongoing...")
        return "ongoing"
    

    def predict_fire_spread(self, fire_starts):
        fire_time = [[float('inf')] * self.ship.dimension for _ in range(self.ship.dimension)]
        queue = deque()
        
        for x, y in fire_starts:
            fire_time[x][y] = 0
            queue.append((x, y, 0))
        
        while queue:
            x, y, t = queue.popleft()
            for cell in self.ship.get_cell(x,y).neighbors:
                nx, ny = cell.row, cell.col
                if not self.ship.get_cell(nx,ny).is_open() and fire_time[nx][ny] == float('inf'):
                    fire_time[nx][ny] = t + 1
                    queue.append((nx, ny, t + 1))
        
        plt.imshow(fire_time, cmap='coolwarm', interpolation='nearest')
        plt.colorbar(label='Fire Arrival Time / Path')
        plt.title('Fire Spread and Bot Path')
        plt.show()
        return fire_time

    @staticmethod
    def heuristic(a, b):
        """Calculate the Manhattan distance heuristic."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])