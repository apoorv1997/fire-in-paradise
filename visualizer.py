import pygame

class Visualizer:
    def __init__(self, ship, cell_size=30, env=None):
        self.ship = ship
        self.cell_size = cell_size
        self.width = ship.dimension * cell_size
        self.height = ship.dimension * cell_size
        self.env = env
        # If an environment is passed, get the bot from it.
        self.bot = env.bot if env is not None else None

        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Ship Grid Visualization")

        # load emoji-compatible font (tries several common emoji fonts)
        self.emoji_font = pygame.font.Font(
            pygame.font.match_font("segoeuiemoji, noto color emoji, apple color emoji"),
            self.cell_size
        )
        # Default emoji for robot (we will use literals for fire and button below)
        self.robot_emoji = "🤖"

    def draw_grid(self, bot_active=False):
        """Draws the ship grid and overlays fire, button, and robot emojis as appropriate."""
        self.screen.fill((0, 0, 0))  # Fill screen with black

        for row in range(self.ship.dimension):
            for col in range(self.ship.dimension):
                cell = self.ship.get_cell(row, col)
                # White for open cells, black for blocked
                color = (255, 255, 255) if cell.open else (0, 0, 0)
                rect = pygame.Rect(col * self.cell_size, row * self.cell_size, self.cell_size, self.cell_size)
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, (200, 200, 200), rect, 1)  # Light gray grid lines

                # Draw fire emoji if the cell is burning.
                if self.ship.get_cell(row, col).on_fire:
                    emoji_surface = self.emoji_font.render("🔥", True, (255, 255, 255))
                    emoji_width, emoji_height = emoji_surface.get_size()
                    emoji_x = col * self.cell_size + (self.cell_size - emoji_width) // 2
                    emoji_y = row * self.cell_size + (self.cell_size - emoji_height) // 2
                    self.screen.blit(emoji_surface, (emoji_x, emoji_y))
                # Otherwise, if this is the button cell (and not on fire), draw the button emoji.
                elif self.env is not None and cell == self.env.button_cell:
                    emoji_surface = self.emoji_font.render("🔵", True, (255, 255, 255))
                    emoji_width, emoji_height = emoji_surface.get_size()
                    emoji_x = col * self.cell_size + (self.cell_size - emoji_width) // 2
                    emoji_y = row * self.cell_size + (self.cell_size - emoji_height) // 2
                    self.screen.blit(emoji_surface, (emoji_x, emoji_y))

                # Finally, if the bot is on this cell, draw the robot emoji on top.
                if bot_active and self.bot is not None and self.bot.row == row and self.bot.col == col:
                    emoji_surface = self.emoji_font.render(self.robot_emoji, True, (255, 255, 255))
                    emoji_width, emoji_height = emoji_surface.get_size()
                    emoji_x = col * self.cell_size + (self.cell_size - emoji_width) // 2
                    emoji_y = row * self.cell_size + (self.cell_size - emoji_height) // 2
                    self.screen.blit(emoji_surface, (emoji_x, emoji_y))

        pygame.display.flip()

    def draw_static_grid(self):
        """Displays a static representation of the ship grid."""
        self.draw_grid(bot_active=False)  # Draw grid without the bot

        # Keep the window open until closed.
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
        pygame.display.quit()
    
    def draw_grid_with_interactive_robot(self):
        """Interactive loop where each arrow key press triggers a simulation tick and redraws the grid."""
        running = True
        clock = pygame.time.Clock()

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                # elif event.type == pygame.KEYDOWN and self.env is not None:
                #     direction = None
                #     if event.key == pygame.K_UP:
                #         direction = "up"
                #     elif event.key == pygame.K_DOWN:
                #         direction = "down"
                #     elif event.key == pygame.K_LEFT:
                #         direction = "left"
                #     elif event.key == pygame.K_RIGHT:
                #         direction = "right"

                    # if direction is not None:
                        # Call a simulation tick whenever an arrow key is pressed.
                result = self.env.tick()
                if result == "failure":
                    print("Simulation failure!")
                    running = False
                    break
                elif result == "success":
                    print("Simulation success!")
                    running = False
                    break
                elif result == "ongoing":
                    print("Simulation ongoing...")

                self.draw_grid(bot_active=True)
                clock.tick(1)  # Limit frame rate to 10 FPS

        pygame.quit()
