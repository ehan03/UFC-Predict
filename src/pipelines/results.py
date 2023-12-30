# standard library imports
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scrapers"))

# third party imports
from scrapy.crawler import CrawlerProcess

# local imports
from src.scrapers.ufc_scrapy.spiders.ufc_scrapers import (
    FightOddsIOSpider,
    UFCStatsSpider,
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
        Get historical data from UFCStats and FightOddsIO
        """

        process = CrawlerProcess(settings={"LOG_LEVEL": "INFO"})
        process.crawl(UFCStatsSpider, scrape_type=self.scrape_type)
        process.crawl(FightOddsIOSpider, scrape_type=self.scrape_type)
        process.start()

    def update_ufcstats_fightoddsio_linkage(self):
        """
        Update linkage between UFCStats and FightOddsIO
        """

        pass

    def update_pnl(self):
        """
        Update PnL on bets
        """

        pass

    def update_features(self):
        """
        Update features for models
        """

        pass

    def __call__(self):
        """
        Run the pipeline
        """

        self.get_results()
