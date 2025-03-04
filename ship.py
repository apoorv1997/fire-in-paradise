import random
from cell import Cell

class Ship:
    def __init__(self, dimension=40):
        self.dimension = dimension
        self.initial_cell = None
        self.on_fire_cells = set()
        self.history_fire_cells = set()
        # 2D list of cell objects
        self.grid = [
            [Cell(row, col) for col in range(dimension)]
            for row in range(dimension)
        ]
        self.set_cell_neighbors()
        self.generate_maze()

    def cell_in_bounds(self, row, col):
        return 0 <= row < self.dimension and 0 <= col < self.dimension

    def distance(self, cell1, cell2):
        # Manhattan distance
        return abs(cell1.row - cell2.row) + abs(cell1.col - cell2.col)

    def set_cell_neighbors(self):
        """Set valid neighbors for each cell in the grid"""
        for row in self.grid:
            for cell in row:
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = cell.row + dr, cell.col + dc
                    if self.cell_in_bounds(nr, nc):
                        cell.neighbors.append(self.get_cell(nr, nc))

    def all_cells(self):
        """Return list of all cells"""
        return [cell for row in self.grid for cell in row]

    def get_cell(self, row, col):
        if self.cell_in_bounds(row, col):
            return self.grid[row][col]
        raise ValueError("Invalid cell coordinates")

    def get_open_cells(self):
        """Return list of open cells"""
        return [cell for row in self.grid for cell in row if cell.open]

    def get_on_fire_cells(self):
        """Return list of cells that are on fire"""
        return [cell for cell in self.get_open_cells() if cell.on_fire]

    def get_blocked_cells_with_one_open_neighbor(self):
        """Return list of openable cells"""
        candidates = []
        for row in self.grid:
            for cell in row:
                if cell.is_frontier():
                    candidates.append(cell)
        return candidates

    def get_dead_end_cells(self):
        """Return list of open cells that have exactly one open neighbor"""
        dead_ends = []
        for row in self.grid:
            for cell in row:
                if cell.is_dead_end():
                    dead_ends.append(cell)
        return dead_ends

    def ignite_cell(self, cell):
        """Ignite a cell and update the on-fire set"""
        cell.on_fire = True
        self.on_fire_cells.add(cell)

    def extinguish_cell(self, cell):
        """Extinguish a cell and update the on-fire set"""
        cell.on_fire = False
        self.history_fire_cells.add(cell)
        self.on_fire_cells.remove(cell)

    def generate_maze(self):
        # --- Phase 1: Open up the ship ---
        # pick random initial open cell within inner area of the grid
        start_row = random.randint(1, self.dimension - 2)
        start_col = random.randint(1, self.dimension - 2)
        start_cell = self.get_cell(start_row, start_col)
        start_cell.open_cell()
        self.initial_cell = start_cell

        # Initialize frontier with closed neighbors of the starting cell
        frontier = set(start_cell.get_closed_neighbors())
        while frontier:
            cell = random.choice(list(frontier))
            if cell.is_frontier():
                cell.open_cell()
            frontier.remove(cell)
            # Update frontier: add neighbors of the opened cell that are now frontier candidates.
            for neighbor in cell.get_closed_neighbors():
                if neighbor.is_frontier():
                    frontier.add(neighbor)

        open_count = sum(cell.is_open() for row in self.grid for cell in row)
        total = self.dimension * self.dimension
        percent_open = open_count / total * 100
        # print(f"Sanity Check: {percent_open:.2f}% of the ship is open before performing dead-end openings")

        # --- Phase 2: Open dead ends ---
        dead_end_cells = self.get_dead_end_cells()
        initial_dead_end_count = len(dead_end_cells)
        # randomly open half of the dead ends
        while len(dead_end_cells) > initial_dead_end_count // 2:
            cell = random.choice(dead_end_cells)
            closed_neighbors = cell.get_closed_neighbors()
            if closed_neighbors:
                random.choice(closed_neighbors).open_cell()
            dead_end_cells = self.get_dead_end_cells()
