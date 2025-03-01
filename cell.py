import json

class Cell:
    def __init__(self, row: int, col: int):
        self.neighbors = []
        self.row = row
        self.col = col
        self.open = False
        self.on_fire = False

    def count_open_neighbors(self):
        """Return the number of open (non-blocked) neighbors for a cell."""
        return sum(neighbor.open for neighbor in self.neighbors)

    def count_blocked_neighbors(self):
        """Return the number of blocked neighbors for a cell"""
        return sum(not neighbor.open for neighbor in self.neighbors)

    def count_burning_neighbors(self):
        """Return the number of burning neighbors for a cell"""
        return sum(neighbor.on_fire for neighbor in self.neighbors)

    def get_closed_neighbors(self):
        """Return a list of closed neighbors"""
        return [neighbor for neighbor in self.neighbors if not neighbor.open]

    def is_dead_end(self):
        """Return True if the cell is open and has exactly one open neighbor"""
        return self.open and self.count_open_neighbors() == 1

    def is_frontier(self):
        """Return True if the cell is not open and has exactly one blocked neighbor (is available to be opened)"""
        return not self.open and self.count_open_neighbors() == 1

    def open_cell(self):
        self.open = True

    def is_open(self):
        return self.open

    def is_on_fire(self):
        return self.on_fire

    def ignite(self):
        self.on_fire = True

    def extinguish(self):
        self.on_fire = False

    def __repr__(self):
        # Return string representation of the cell
        return '⬜' if self.open else '⬛'

    def to_Json(self):
        return {
            'row': self.row,
            'col': self.col,
            'open': self.open,
            'on_fire': self.on_fire
        }
class CellEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Cell):
            return obj.to_Json()
        return json.JSONEncoder.default(self, obj)