import random
from cell import Cell

class Ship:
    def __init__(self, dimension=40):
        self.dimension = dimension
        self.initial_cell = None
        # Create a 2D grid (list of lists) of Cell objects.
        self.grid = [
            [Cell(row, col) for col in range(dimension)]
            for row in range(dimension)
        ]
        self.set_cell_neighbors()


    def cell_in_bounds(self, row, col):
        return 0 <= row < self.dimension and 0 <= col < self.dimension


    def get_dimension(self):
        return self.dimension
    
    def set_cell_neighbors(self):
        """Set valid neighbors for each cell in the grid."""
        for row in self.grid:
            for cell in row:
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]: # up, down, left, right directions
                    nr, nc = cell.row + dr, cell.col + dc         # new cell coordinates
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


    # TODO can be more efficient - don't check every cell for candidacy/dead-end status every time
    def generate_maze(self):
        # --- Phase 1: Opening up the ship ---
        # TODO Do we actually have to avoid the outer boundary?
        # Start by opening a random cell in the interior (avoid the outer boundary)
        start_row = random.randint(1, self.dimension - 2)
        start_col = random.randint(1, self.dimension - 2)
        cell = self.get_cell(start_row, start_col)
        cell.open_cell()
        self.initial_cell = cell

        # Iteratively open blocked cells with exactly one open neighbor
        candidates = self.get_blocked_cells_with_one_open_neighbor()
        while candidates:
            cell = random.choice(candidates)
            cell.open_cell()
            candidates = self.get_blocked_cells_with_one_open_neighbor()

        # Sanity Check: Before opening dead ends, about 60% of the ship should be open
        open_count = sum(cell.is_open() for row in self.grid for cell in row)
        total = self.dimension * self.dimension
        percent_open = open_count / total * 100
        print(f"Sanity Check: {percent_open:.2f}% of the ship is open before performing dead-end openings")

        # --- Phase 2: Open dead ends ---
        dead_end_cells = self.get_dead_end_cells()
        initial_count_dead_ends = len(dead_end_cells)
        # Open one additional neighbor for approximately half of the dead-end cells
        while len(dead_end_cells) > initial_count_dead_ends // 2:
            cell = random.choice(dead_end_cells)
            random.choice(cell.get_closed_neighbors()).open_cell()
            dead_end_cells = self.get_dead_end_cells()


    def display(self):
        """Display the ship grid on the console."""
        for row in self.grid:
            print("".join(str(cell) for cell in row))
