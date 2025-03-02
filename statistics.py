import matplotlib.pyplot as plt
import numpy as np
import random
from ship import Ship
from environment import Environment
from botcontroller import BotController

class StatisticsRunner:
    """
    StatisticsRunner repeatedly generates test environments and runs full simulations
    for each bot strategy and for many values of the flammability parameter (q).

    For each (strategy, q) combination, it runs a number of trials and records the fraction
    of trials in which the bot successfully reaches the button (and thereby extinguishes the fire)
    before getting caught.
    """
    def __init__(self, strategies, q_values, trials, ship_dimension=20):
        """
        strategies: list of bot strategy numbers to test (e.g., [1, 2, 3, 4])
        q_values: list or array of flammability parameter values (between 0 and 1)
        trials: number of simulation runs per (strategy, q) combination
        ship_dimension: grid dimension for the ship (smaller for faster simulation)
        """
        self.strategies = strategies
        self.q_values = q_values
        self.trials = trials
        self.ship_dimension = ship_dimension
        # To store results: a dict mapping strategy -> list of success frequencies (for each q)
        self.results = {strategy: [] for strategy in strategies}

    def run_trial(self, strategy, q):
        """
        Run a single simulation trial using the given bot strategy and flammability parameter q.
        Returns True if the bot reaches the button (success) or False if the bot is caught by fire.
        """
        # Create a new ship and generate its maze.
        ship = Ship(self.ship_dimension)
        ship.generate_maze()
        # Initialize the environment with the given flammability parameter.
        env = Environment(ship, q=q)
        # Create a bot controller for the chosen strategy.
        controller = BotController(env.bot, env, strategy)

        # Run simulation until a terminal state is reached.
        result = "ongoing"
        while result == "ongoing":
            # Get the next move from the controller (for non-manual strategies)
            move = controller.get_next_move()
            result = env.tick(move)
        return result == "success"

    def run_experiments(self):
        """
        For each bot strategy and for each q value, perform a number of trials,
        record the fraction of successful trials, and print progress to the console.
        """
        for strategy in self.strategies:
            success_rates = []
            print(f"Running experiments for bot strategy {strategy}...")
            for q in self.q_values:
                successes = 0
                for trial in range(self.trials):
                    if self.run_trial(strategy, q):
                        successes += 1
                success_rate = successes / self.trials
                success_rates.append(success_rate)
                print(f"  q = {q:.2f}: success rate = {success_rate:.3f}")
            self.results[strategy] = success_rates

    def plot_results(self):
        """
        Plot a single graph comparing the performance of all bot strategies.
        X-axis: flammability parameter (q).
        Y-axis: average success frequency.
        The graph is clearly labeled and includes a legend.
        """
        plt.figure(figsize=(10, 6))
        for strategy in self.strategies:
            plt.plot(self.q_values, self.results[strategy], marker='o', label=f'Bot Strategy {strategy}')
        plt.xlabel('Flammability Parameter (q)')
        plt.ylabel('Success Frequency')
        plt.title('Bot Performance vs Flammability Parameter (q)')
        plt.legend()
        plt.grid(True)
        plt.show()

    def run_all(self):
        """
        Convenience method to run experiments and then plot the results.
        """
        self.run_experiments()
        self.plot_results()


if __name__ == '__main__':
    # Define the bot strategies to test (using non-interactive, algorithmic bots)
    strategies = [1, 2, 3, 4]

    q_values = [0, 0.2, 0.4, 0.6, 0.8, 1]
    # Number of trials per (strategy, q) combination (increase for smoother graphs)
    trials = 5

    stats_runner = StatisticsRunner(strategies, q_values, trials, ship_dimension=40)
    stats_runner.run_all()
