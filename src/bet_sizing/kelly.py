# standard library imports
import itertools

# third party imports
import cvxpy as cp
import numpy as np

# local imports


class SimultaneousKelly:
    """
    Simultaneous Kelly bet sizing strategy for multiple bouts
    including a risk free asset
    """

    def __init__(
        self,
        red_probs: np.ndarray,
        blue_probs: np.ndarray,
        red_odds: np.ndarray,
        blue_odds: np.ndarray,
        current_bankroll: float,
        fraction: float = 0.15,
        min_bet: float = 0.10,
    ):
        """
        Initialize the SimultaneousKelly object
        """

        self.red_probs = red_probs
        self.blue_probs = blue_probs
        self.red_odds = red_odds
        self.blue_odds = blue_odds
        self.current_bankroll = current_bankroll
        self.fraction = fraction
        self.min_bet = min_bet

        self.n = red_probs.shape[0]
        self.variations = np.array(list(itertools.product([1, 0], repeat=self.n)))

    def convert_american_to_decimal(self, odds: np.ndarray) -> np.ndarray:
        """
        Convert American odds to decimal odds
        """

        return np.where(odds > 0, odds / 100 + 1, -100 / odds + 1)

    def create_returns_matrix(self) -> np.ndarray:
        """
        Create returns matrix R
        """

        red_odds_decimal = self.convert_american_to_decimal(self.red_odds)
        blue_odds_decimal = self.convert_american_to_decimal(self.blue_odds)

        returns_matrix = np.zeros(shape=(self.variations.shape[0], 2 * self.n + 1))
        returns_matrix[:, -1] = 1
        for j in range(self.n):
            returns_matrix[:, 2 * j] = np.where(
                self.variations[:, j] == 1, red_odds_decimal[j], 0
            )
            returns_matrix[:, 2 * j + 1] = np.where(
                self.variations[:, j] == 0, blue_odds_decimal[j], 0
            )

        return returns_matrix

    def create_probabilities_vector(self) -> np.ndarray:
        """
        Create probabilities vector p, contains probability combinations
        for all possible overall event outcomes
        """

        prob_vector = np.ones(shape=(1, self.variations.shape[0]))
        for j in range(self.n):
            prob_vector[0, :] = np.where(
                self.variations[:, j] == 1,
                prob_vector * self.red_probs[j],
                prob_vector * self.blue_probs[j],
            )

        return prob_vector

    def calculate_optimal_wagers(self) -> np.ndarray:
        """
        Calculate optimal fractions
        """

        R = self.create_returns_matrix()
        p = self.create_probabilities_vector()
        b = cp.Variable(2 * self.n + 1)

        objective = cp.Maximize(p @ cp.log(R @ b))
        constraints = [
            b >= 0,
            cp.sum(b) <= self.fraction,
        ]
        problem = cp.Problem(objective, constraints)
        problem.solve()

        return b.value

    def __call__(self) -> np.ndarray:
        """
        Calculate optimal wager amounts in dollars
        """

        fractions = self.calculate_optimal_wagers()
        wagers = fractions[:-1] * self.current_bankroll
        wagers_rounded = np.round(wagers, 2)

        return np.where(wagers_rounded < self.min_bet, 0, wagers_rounded)
