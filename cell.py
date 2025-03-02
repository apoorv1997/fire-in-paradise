class Cell:
    def __init__(self, row: int, col: int):
        self.neighbors = []
        self.row = row
        self.col = col
        self.open = False
        self.on_fire = False

    def reset_cell(self):
        self.open = False
        self.on_fire = False

    def count_open_neighbors(self):
        """Return number of open neighbors for a cell"""
        return sum(neighbor.open for neighbor in self.neighbors)

    def count_blocked_neighbors(self):
        """Return number of blocked neighbors for a cell"""
        return sum(not neighbor.open for neighbor in self.neighbors)

    def count_burning_neighbors(self):
        """Return number of burning neighbors for a cell"""
        return sum(neighbor.on_fire for neighbor in self.neighbors)

    def get_closed_neighbors(self):
        """Return list of closed neighbors"""
        return [neighbor for neighbor in self.neighbors if not neighbor.open]

    def get_open_neighbors(self):
        """Return list of open neighbors"""
        return [neighbor for neighbor in self.neighbors if neighbor.open]

    def is_dead_end(self):
        """Return True if the cell is open and has exactly one open neighbor"""
        return self.open and self.count_open_neighbors() == 1

    def is_frontier(self):
        """Return True if the cell is not open and has exactly one open neighbor"""
        return not self.open and self.count_open_neighbors() == 1

    def get_viable_adjacent_cells(self):
        """Return list of open neighbors that are not on fire"""
        return [neighbor for neighbor in self.neighbors if neighbor.open and not neighbor.on_fire]

    def get_viable_adjacent_cells_with_no_burning_neighbors(self):
        """Return list of open neighbors that have no burning neighbors"""
        return [neighbor for neighbor in self.neighbors if neighbor.open and not neighbor.on_fire and neighbor.count_burning_neighbors() == 0]

    def open_cell(self):
        self.open = True

    def is_open(self):
        return self.open

    def is_on_fire(self):
        return self.on_fire

    def __repr__(self):
        return '⬜' if self.open else '⬛'
