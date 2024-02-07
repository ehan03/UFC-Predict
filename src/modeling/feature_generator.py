# standard library imports

# third party imports
import pandas as pd

# local imports


class FeatureGenerator:
    """
    Class for generating relevant features and outputting
    an 'ML-ready' dataset
    """

    def __init__(self, mode: str) -> None:
        """
        Initializes FeatureGenerator class
        """

        if mode not in ["train", "predict"]:
            raise ValueError(f"{mode} is not a valid mode")

        self.mode = mode

    def create_event_meta_features(self):
        pass

    def create_fighter_attribute_features(self):
        pass

    def create_bout_stats_features(self):
        pass

    def create_red_blue_diff_features(
        self, red_df: pd.DataFrame, blue_df: pd.DataFrame
    ):
        pass
