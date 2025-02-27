import pygame

class Visualizer:
    def __init__(self, ship, cell_size=30, env=None):
        self.ship = ship
        self.cell_size = cell_size
        self.width = ship.dimension * cell_size
        self.height = ship.dimension * cell_size
        self.env = env
        self.bot = env.bot if env is not None else None

        # Initializing the pygame window
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Ship Grid Visualization")

        # Set a working font for rendering emojis as well as emoji size
        emoji_font_size = int(self.cell_size * 0.6)
        self.emoji_font = pygame.font.Font(
            pygame.font.match_font("segoeuiemoji, noto color emoji, apple color emoji"),
            emoji_font_size
        )
        self.robot_emoji = "🤖"

    def draw_grid(self, bot_active=False):
        """Draws the ship grid and overlays the fire, the button, and (if active) the robot"""
        self.screen.fill((0, 0, 0))

        for row in range(self.ship.dimension):
            for col in range(self.ship.dimension):
                cell = self.ship.get_cell(row, col)
                rect = pygame.Rect(col * self.cell_size, row * self.cell_size, self.cell_size, self.cell_size)
                bg_color = (255, 255, 255) if cell.open else (0, 0, 0) # white if open, black if blocked
                pygame.draw.rect(self.screen, bg_color, rect) # draw cell fill color
                pygame.draw.rect(self.screen, (200, 200, 200), rect, 1) # draw cell border

                if self.env is not None and cell == self.env.button_cell: # color button cell blue
                    pygame.draw.rect(self.screen, (0, 0, 255), rect)
                    pygame.draw.rect(self.screen, (200, 200, 200), rect, 1)

                if cell.on_fire:
                    # draw fire emoji if cell is on fire
                    emoji_surface = self.emoji_font.render("🔥", True, (255, 255, 255))
                    # This offsets the emoji so that it can still be seen when the robot is on top of it
                    ew, eh = emoji_surface.get_size() # get emoji size
                    ex = col * self.cell_size + self.cell_size - ew # x position
                    ey = row * self.cell_size # y position
                    self.screen.blit(emoji_surface, (ex, ey)) # draw emoji

                # Draw the robot emoji if the bot is active and on this cell
                if bot_active and self.bot is not None and self.bot.cell.row == row and self.bot.cell.col == col:
                    emoji_surface = self.emoji_font.render(self.robot_emoji, True, (255, 255, 255))
                    ew, eh = emoji_surface.get_size()
                    ex = col * self.cell_size + (self.cell_size - ew) // 2 # center x
                    ey = row * self.cell_size + (self.cell_size - eh) // 2 # center y
                    self.screen.blit(emoji_surface, (ex, ey))
        pygame.display.flip() # update the display

    def draw_static_grid(self):
        """
        Displays a static representation of the ship grid,
        overlaying robot's path (blue dots) and every cell that was ignited (red fire emoji)
        """
        self.draw_grid(bot_active=False)
        if self.env is not None:
            # Overlay ignited cells
            for cell in self.env.history_fire:
                row, col = cell.row, cell.col
                cell_obj = self.ship.get_cell(row, col)
                if not cell_obj.on_fire:
                    # overlay fire emoji if cell is on fire
                    emoji_surface = self.emoji_font.render("🔥", True, (255, 0, 0))
                    ew, eh = emoji_surface.get_size()
                    ex = col * self.cell_size + (self.cell_size - ew) // 2
                    ey = row * self.cell_size + (self.cell_size - eh) // 2
                    self.screen.blit(emoji_surface, (ex, ey))
            # Draw robot's path as small blue circles
            for cell in self.env.bot_path:
                center = (cell.col * self.cell_size + self.cell_size // 2, cell.row * self.cell_size + self.cell_size // 2)
                pygame.draw.circle(self.screen, (0, 0, 255), center, self.cell_size // 8)
            # Draw robot's final pos
            if self.env.bot:
                row, col = self.env.bot.cell.row, self.env.bot.cell.col
                emoji_surface = self.emoji_font.render(self.robot_emoji, True, (255, 255, 255))
                ew, eh = emoji_surface.get_size()
                ex = col * self.cell_size + (self.cell_size - ew) // 2
                ey = row * self.cell_size + (self.cell_size - eh) // 2
                self.screen.blit(emoji_surface, (ex, ey))
        pygame.display.flip() # update the display

        while True:
            # wait for user to close the window
            event = pygame.event.wait()
            if event.type == pygame.QUIT:
                break
        pygame.quit()

    def draw_grid_with_algorithmic_robot(self, controller, realtime, tick_interval):
        """
        Runs the simulation in algorithmic mode
        """
        running = True
        clock = pygame.time.Clock()
        simulation_result = "ongoing"

        while running and simulation_result == "ongoing":
            # bot takes action, updating the ship environment as needed before updating the grid
            simulation_result = controller.make_action()
            self.draw_grid(bot_active=True)
            if realtime:
                clock.tick(1 / tick_interval)
            for event in pygame.event.get():
                # check for quit event
                if event.type == pygame.QUIT:
                    running = False

        if simulation_result == "failure":
            print("Robot failed!")
        elif simulation_result == "success":
            print("Robot succeeded!")

        # display static terminal state
        self.draw_static_grid()

    def draw_grid_with_interactive_robot(self, controller):
        """
        Runs simulation in manual mode
        """
        running = True
        clock = pygame.time.Clock()
        simulation_result = "ongoing"
        while running and simulation_result == "ongoing":
            # wait for user input to move the bot, updating the ship environment as needed before updating the grid
            simulation_result = controller.make_action()
            self.draw_grid(bot_active=True)
            clock.tick(30)
        if simulation_result == "failure":
            print("Robot failed!")
        elif simulation_result == "success":
            print("Robot succeeded!")
        # display static terminal state
        self.draw_static_grid()
