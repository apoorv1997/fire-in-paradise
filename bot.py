class Bot:
    def __init__(self, cell, ship):
        self.ship = ship
        self.cell = cell

    def move(self, direction):
        """Moves the bot in the chosen direction if valid"""
        new_row, new_col = self.cell.row, self.cell.col

        if direction == "up":
            new_row -= 1
        elif direction == "down":
            new_row += 1
        elif direction == "left":
            new_col -= 1
        elif direction == "right":
            new_col += 1
        else:
            raise ValueError("Invalid chosen direction")

        if self.ship.cell_in_bounds(new_row, new_col):
            target_cell = self.ship.get_cell(new_row, new_col)
            if target_cell.open:
                self.cell = target_cell
                return
        raise ValueError("Invalid move made")
