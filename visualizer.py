import os
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

        # Load image assets for fire and robot emojis.
        assets_path = os.path.join(os.path.dirname(__file__), 'assets')
        self.fire_image = pygame.image.load(os.path.join(assets_path, "fire.png")).convert_alpha()
        self.robot_image = pygame.image.load(os.path.join(assets_path, "walle.png")).convert_alpha()

        # Scale images to size relative to cell size
        desired_size = int(self.cell_size * 0.6)
        self.fire_image = pygame.transform.smoothscale(self.fire_image, (desired_size, desired_size))
        self.robot_image = pygame.transform.smoothscale(self.robot_image, (desired_size, desired_size))

    def draw_grid(self):
        """Draws the ship grid and overlays the fire, the button, and (if active) the robot"""
        if not pygame.display.get_init() or self.screen is None:
            # Reinitialize the display surface based on saved dimensions.
            self.screen = pygame.display.set_mode((self.width, self.height))
        self.screen.fill((0, 0, 0))

        for row in range(self.ship.dimension):
            for col in range(self.ship.dimension):
                cell = self.ship.get_cell(row, col)
                rect = pygame.Rect(col * self.cell_size, row * self.cell_size, self.cell_size, self.cell_size)
                bg_color = (255, 255, 255) if cell.open else (0, 0, 0)  # white if open, black if blocked
                pygame.draw.rect(self.screen, bg_color, rect)  # draw cell fill color
                pygame.draw.rect(self.screen, (200, 200, 200), rect, 1)  # draw cell border

                if self.env is not None and cell == self.env.button_cell:  # color button cell blue
                    pygame.draw.rect(self.screen, (0, 0, 255), rect)
                    pygame.draw.rect(self.screen, (200, 200, 200), rect, 1)

                if cell.on_fire:
                    # Draw fire image if cell is on fire.
                    # mage is aligned to top-right of the cell so it is still seen if robot enters the cell
                    ew, eh = self.fire_image.get_size()  # get image dimensions
                    ex = col * self.cell_size + self.cell_size - ew  # x position
                    ey = row * self.cell_size  # y position
                    self.screen.blit(self.fire_image, (ex, ey))  # draw fire image

                # Draw robot image if the bot is active and on this cell
                if self.bot is not None and self.bot.cell.row == row and self.bot.cell.col == col:
                    ew, eh = self.robot_image.get_size()
                    ex = col * self.cell_size + (self.cell_size - ew) // 2  # center x
                    ey = row * self.cell_size + (self.cell_size - eh) // 2  # center y
                    self.screen.blit(self.robot_image, (ex, ey))  # draw robot image

        pygame.display.flip()  # update display

    def draw_static_grid(self):
        """
        Display static representation of ship grid,
        overlaying robot's path (blue dots) and every cell that was ignited (fire image)
        """
        self.draw_grid()
        if self.env is not None:
            # Overlay ignited cells
            red_fire_image = self.fire_image.copy()

            for cell in self.ship.history_fire_cells:
                row, col = cell.row, cell.col
                cell_obj = self.ship.get_cell(row, col)
                if not cell_obj.on_fire:
                    ew, eh = red_fire_image.get_size()
                    ex = col * self.cell_size + (self.cell_size - ew) // 2
                    ey = row * self.cell_size + (self.cell_size - eh) // 2
                    self.screen.blit(red_fire_image, (ex, ey))
            # Draw robot's path as small blue circles
            for cell in self.env.bot_path:
                center = (cell.col * self.cell_size + self.cell_size // 2,
                          cell.row * self.cell_size + self.cell_size // 2)
                pygame.draw.circle(self.screen, (0, 0, 255), center, self.cell_size // 8)
            # Draw robot's final position
            if self.env.bot:
                row, col = self.env.bot.cell.row, self.env.bot.cell.col
                ew, eh = self.robot_image.get_size()
                ex = col * self.cell_size + (self.cell_size - ew) // 2
                ey = row * self.cell_size + (self.cell_size - eh) // 2
                self.screen.blit(self.robot_image, (ex, ey))
        pygame.display.flip()  # update display

        while True:
            # wait for user to close the window
            event = pygame.event.wait()
            if event.type == pygame.QUIT:
                break
        pygame.quit()

    def draw_grid_with_algorithmic_robot(self, controller, realtime, tick_interval):
        """
        Runs simulation in algorithmic mode
        """
        running = True
        clock = pygame.time.Clock()
        simulation_result = "ongoing"

        while running and simulation_result == "ongoing":
            # Bot takes action, updating ship environment as needed before updating the grid
            simulation_result = controller.make_action()
            self.draw_grid()
            if realtime:
                clock.tick(1 / tick_interval)
            for event in pygame.event.get():
                # Check for quit event.
                if event.type == pygame.QUIT:
                    running = False

        if simulation_result == "failure":
            print("Robot failed!")
        elif simulation_result == "success":
            print("Robot succeeded!")

        # Display static terminal state
        self.draw_static_grid()

    def draw_grid_with_interactive_robot(self, controller):
        """
        Runs simulation in manual mode
        """
        running = True
        clock = pygame.time.Clock()
        simulation_result = "ongoing"
        while running and simulation_result == "ongoing":
            # Wait for user input to move the bot, updating the ship environment as needed before updating the grid
            simulation_result = controller.make_action()
            self.draw_grid()
            clock.tick(30)
        if simulation_result == "failure":
            print("Robot failed!")
        elif simulation_result == "success":
            print("Robot succeeded!")
        # Display static terminal state.
        self.draw_static_grid()
