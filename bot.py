class Bot:
    def __init__(self, ship, row, col):
        self.ship = ship
        self.row = row
        self.col = col

    def move(self, direction):
        """Moves the bot in the specified direction if the cell is open."""
        new_row, new_col = self.row, self.col

        if direction == "up":
            new_row -= 1
        elif direction == "down":
            new_row += 1
        elif direction == "left":
            new_col -= 1
        elif direction == "right":
            new_col += 1
        else:
            return

        # Only move if within bounds and the target cell is open
        if self.ship.cell_in_bounds(new_row, new_col):
            target_cell = self.ship.get_cell(new_row, new_col)
            if target_cell.open:
                self.row, self.col = new_row, new_col
