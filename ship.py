import random
from cell import Cell

class Ship:
    def __init__(self, dimension=40):
        self.dimension = dimension
        self.initial_cell = None
        # 2D list of cell objects
        self.grid = [
            [Cell(row, col) for col in range(dimension)]
            for row in range(dimension)
        ]
        self.set_cell_neighbors()

    def cell_in_bounds(self, row, col):
        return 0 <= row < self.dimension and 0 <= col < self.dimension

    def set_cell_neighbors(self):
        """Set valid neighbors for each cell in the grid"""
        for row in self.grid:
            for cell in row:
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = cell.row + dr, cell.col + dc
                    if self.cell_in_bounds(nr, nc):
                        cell.neighbors.append(self.get_cell(nr, nc))

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

    def generate_maze(self):
        # --- Phase 1: Open up the ship ---
        # pick random initial open cell within inner area of the grid
        start_row = random.randint(1, self.dimension - 2)
        start_col = random.randint(1, self.dimension - 2)
        cell = self.get_cell(start_row, start_col)
        cell.open_cell()
        self.initial_cell = cell

        while True:
            # randomly open cells with one open neighbor until no more candidates
            candidates = self.get_blocked_cells_with_one_open_neighbor()
            if not candidates:
                break
            random.choice(candidates).open_cell()

        open_count = sum(cell.is_open() for row in self.grid for cell in row)
        total = self.dimension * self.dimension
        percent_open = open_count / total * 100
        print(f"Sanity Check: {percent_open:.2f}% of the ship is open before performing dead-end openings")

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
