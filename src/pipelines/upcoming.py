# standard library imports

# third party imports

# local imports
from src.pipelines.base import Pipeline


class UpcomingPipeline(Pipeline):
    """
    Pipeline for upcoming UFC events
    """

    def scrape_upcoming_event(self):
        pass

    def scrape_betting_odds(self):
        pass

    def scrape_latest_rankings(self):
        pass

    def predict_upcoming_event(self):
        pass

    def make_bets(self):
        pass

    def __call__(self):
        pass
