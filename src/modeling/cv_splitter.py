# standard library imports

# third party imports
import pandas as pd

# local imports


class CustomGroupTimeSeriesSplit:
    """
    By-year expanding time series splitter because
    scikit-learn is not enough
    """

    def __init__(self, n_splits: int) -> None:
        """
        Initializes splitter class
        """
        if n_splits <= 0:
            raise ValueError("n_splits must be a positive integer")

        self.n_splits = n_splits

    def get_splits(self, df_dates: pd.DataFrame):
        """
        Create splits
        """

        year_groups = df_dates.groupby(df_dates.DATE.dt.year).groups
        year_groups_sorted = [indices for _, indices in sorted(year_groups.items())]

        assert self.n_splits < len(year_groups_sorted)

        train = []
        for indices in year_groups_sorted[: -self.n_splits]:
            train += indices
        test = year_groups_sorted[-self.n_splits]
        splits = [(train, test)]

        for i in range(self.n_splits - 1, 0, -1):
            train += year_groups_sorted[-(i + 1)]
            test = year_groups_sorted[-i]
            splits.append((train, test))

        return splits
