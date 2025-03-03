import matplotlib.pyplot as plt
import numpy as np
import random
import copy  # for deep copying the environment
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
        trials: number of simulation runs per q value (each trial is run on the same ship/env for all strategies)
        ship_dimension: grid dimension for the ship (smaller for faster simulation)
        """
        self.strategies = strategies
        self.q_values = q_values
        self.trials = trials
        self.ship_dimension = ship_dimension
        # To store results: a dict mapping strategy -> list of success frequencies (for each q)
        self.results = {strategy: [] for strategy in strategies}

    def run_experiments(self):
        """
        For each flammability parameter q value, perform a number of trials.
        In each trial, generate one ship and environment and run all strategies on copies of it.
        Record the fraction of successful trials for each strategy and print progress to the console.
        """
        for q in self.q_values:
            # Initialize success count for each strategy for the current q.
            strategy_successes = {strategy: 0 for strategy in self.strategies}
            print(f"Running experiments for q = {q:.2f}...")
            for trial in range(self.trials):
                # Create a new ship and generate its maze.
                ship = Ship(self.ship_dimension)
                # Initialize the environment with the given flammability parameter.
                env = Environment(ship, q=q)
                # Run each strategy on same environment so they all see the same start state.
                for strategy in self.strategies:
                    controller = BotController(env.bot, env, strategy)
                    result = "ongoing"
                    while result == "ongoing":
                        result = controller.make_action()
                    if result == "success":
                        strategy_successes[strategy] += 1
                    env.reset()

            # Record and print success rate for each strategy at this q.
            for strategy in self.strategies:
                success_rate = strategy_successes[strategy] / self.trials
                self.results[strategy].append(success_rate)
                print(f"  Strategy {strategy}: success rate = {success_rate:.3f}")

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
        plt.title(f'Bot Performance vs Flammability Parameter (q) for Ship Dim={self.ship_dimension} and {self.trials} Trials per q')
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
    # Number of trials per q value (each trial is run on the same ship/env for all strategies)
    trials = 500

    stats_runner = StatisticsRunner(strategies, q_values, trials, ship_dimension=40)
    stats_runner.run_all()
