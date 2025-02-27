class Bot:
    def __init__(self, ship, row, col):
        self.ship = ship
        self.row = row
        self.col = col

    def move(self, row, col):
        """Moves the bot in the specified direction if the cell is open."""
        new_row, new_col = self.row, self.col

        # Only move if within bounds and the target cell is open
        if self.ship.cell_in_bounds(new_row, new_col):
            target_cell = self.ship.get_cell(new_row, new_col)
            if target_cell.open:
                self.row, self.col = new_row, new_col
