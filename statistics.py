import matplotlib.pyplot as plt
from ship import Ship
from environment import Environment
from botcontroller import BotController
from visualizer import Visualizer


class StatisticsRunner:
    @staticmethod
    def run_success_percent_experiments(strategies, q_values, trials, ship_dimension, winnable_only=False):
        """
        For each flammability parameter q value, perform x trials.
        winnable_only: if True, only run on winnable environments
        In each trial, generate one environment and run all strategies on it
        Overall, this computes the success frequency for each strategy at each q value.
        Returns a tuple (results, saved_envs) where:
          - results is a dict mapping strategy -> list of success frequencies (for each q)
          - saved_envs is a list of environments where strategies 1, 2, or 3 succeeded while strategy 4 did not
        """
        results = {strategy: [] for strategy in strategies}
        saved_envs = []

        for q in q_values:
            strategy_successes = {strategy: 0 for strategy in strategies}
            print(f"Running experiments for q = {q:.2f}...")

            for trial in range(trials):
                ship = Ship(ship_dimension)
                env = Environment(ship, q=q)

                if winnable_only:
                    while not env.is_winnable():
                        ship = Ship(ship_dimension)
                        env = Environment(ship, q=q)

                trial_results = {}
                for strategy in strategies:
                    env.reset()
                    controller = BotController(env.bot, env, strategy)
                    result = "ongoing"
                    while result == "ongoing":
                        result = controller.make_action()
                    trial_results[strategy] = result
                    if result == "success":
                        strategy_successes[strategy] += 1

                # Save the environment for review if any of strategies 1, 2, or 3 succeeded while strategy 4 did not
                if ((trial_results.get(2) == "success" and trial_results.get(4) != "success") or
                        (trial_results.get(3) == "success" and trial_results.get(4) != "success") or
                        (trial_results.get(1) == "success" and trial_results.get(4) != "success")):
                    saved_envs.append(env)

            # Record and print success rate for each strategy at this q.
            for strategy in strategies:
                success_rate = strategy_successes[strategy] / trials
                results[strategy].append(success_rate)
                print(f"  Strategy {strategy}: success rate = {success_rate:.3f}")

        return results, saved_envs

    @staticmethod
    def plot_success_percent_experiment_results(strategies, q_values, trials, ship_dimension, results):
        """
        Plot a single graph visualizing results of running all strategies at each q value.
        """
        plt.figure(figsize=(10, 6))
        for strategy in strategies:
            plt.plot(q_values, results[strategy], marker='o', label=f'Bot Strategy {strategy}')
        plt.xlabel('Flammability Parameter (q)')
        plt.ylabel('Success Frequency')
        plt.title(f'Bot Performance vs Flammability Parameter (q) for Ship Dim={ship_dimension} and {trials} Trials per q')
        plt.legend()
        plt.grid(True)
        plt.show()


    @staticmethod
    def run_winnability_experiment(q_values, trials_per_q, ship_dimension, tries=2):
        """
        For each flammability parameter q, run trials_per_q trials and record the fraction of
        simulations that are winnable (i.e. at least one strategy wins).
        tries is the number of chances to give each strategy to win to account for randomness.
        """
        win_frequencies = []
        for q in q_values:
            wins = 0
            print(f"Testing q = {q:.2f}...")
            for t in range(trials_per_q):
                env = Environment(Ship(ship_dimension), q=q)
                if env.is_winnable(tries=tries):
                    wins += 1
            frequency = wins / trials_per_q
            print(f"Winnable: {frequency:.3f}")
            win_frequencies.append(frequency)

        # Plot the results
        plt.figure(figsize=(10, 6))
        plt.plot(q_values, win_frequencies, marker='o', label='Winnability Frequency')
        plt.xlabel('Flammability Parameter (q)')
        plt.ylabel('Fraction of Winnable Simulations')
        plt.title(f'Simulation Winnability vs Flammability Parameter for Ship Dim={ship_dimension} and {trials_per_q} Trials per q and {tries} Tries per Strategy')
        plt.grid(True)
        plt.legend()
        plt.show()
        return win_frequencies


if __name__ == '__main__':
    # Define the bot strategies to test (using non-interactive, algorithmic bots)
    strategies = [1, 2, 3, 4]

    # Define the range of flammability parameter values to test
    q_values = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]

    # Number of trials per q value (each trial is run on the same ship/env for all strategies)
    trials = 5

    # Ship grid dimension
    ship_dimension = 30

    results, saved_envs = StatisticsRunner.run_success_percent_experiments(strategies, q_values, trials, ship_dimension)
    StatisticsRunner.plot_success_percent_experiment_results(strategies, q_values, trials, ship_dimension, results)

    # For any saved environments of interest, display the grid and test the performance of strategy 4
    if saved_envs:
        for test_env in saved_envs:
            print(test_env.q)
            test_env.reset()
            controller = BotController(test_env.bot, test_env, 4)
            viz = Visualizer(test_env.ship, 20, test_env)
            viz.draw_grid_with_algorithmic_robot(controller, True, 0.3)

    # Winnability experiment
    StatisticsRunner.run_winnability_experiment(q_values, trials, ship_dimension)
