# standard library imports
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scrapers"))

# third party imports
from scrapy.crawler import CrawlerProcess

# local imports
from src.fighter_matching import FighterMatcher
from src.scrapers.ufc_scrapy.spiders.ufc_scrapers import (
    FightOddsIOResultsSpider,
    UFCStatsResultsSpider,
)


class ResultsPipeline:
    """
    Class for handling UFC event results
    """

    def __init__(self, scrape_type):
        """
        Initialize ResultsPipeline class
        """

        assert scrape_type in {"all", "most_recent"}
        self.scrape_type = scrape_type

    def get_results(self):
        """
        Get historical data from UFC Stats and FightOdds.io
        """

        process = CrawlerProcess(settings={"LOG_LEVEL": "INFO"})
        process.crawl(UFCStatsResultsSpider, scrape_type=self.scrape_type)
        process.crawl(FightOddsIOResultsSpider, scrape_type=self.scrape_type)
        process.start()

    def update_ufcstats_fightoddsio_linkage(self):
        """
        Update linkage between UFCStats and FightOdds.io
        """

        if self.scrape_type == "all":
            fighter_matcher = FighterMatcher(matching_type="reset_all")
        else:
            fighter_matcher = FighterMatcher(matching_type="completed")

        fighter_matcher()

    def update_fighter_elo_scores(self):
        """
        Update fighter ELOs
        """

        pass

    def update_pnl(self):
        """
        Update PnL on bets
        """

        pass

    def __call__(self):
        """
        Run the pipeline
        """

        self.get_results()
        self.update_ufcstats_fightoddsio_linkage()
