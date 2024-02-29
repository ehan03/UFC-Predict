# standard library imports
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scrapers"))

# third party imports
from scrapy.crawler import CrawlerProcess

# local imports
from src.scrapers.ufc_scrapy.spiders.fightmatrix_spiders import FightMatrixResultsSpider
from src.scrapers.ufc_scrapy.spiders.fightoddsio_spiders import FightOddsIOResultsSpider
from src.scrapers.ufc_scrapy.spiders.sherdog_spiders import SherdogResultsSpider
from src.scrapers.ufc_scrapy.spiders.ufcstats_spiders import UFCStatsResultsSpider


class ResultsPipeline:
    """
    Class for handling UFC event results
    """

    def __init__(self):
        """
        Initialize ResultsPipeline class
        """

        self.scrape_type = "most_recent"

    def get_results(self):
        """
        Get historical data from UFC Stats and FightOdds.io
        """

        process = CrawlerProcess(settings={"LOG_LEVEL": "INFO"})
        process.crawl(UFCStatsResultsSpider, scrape_type=self.scrape_type)
        process.crawl(FightOddsIOResultsSpider, scrape_type=self.scrape_type)
        process.crawl(SherdogResultsSpider, scrape_type=self.scrape_type)
        process.crawl(FightMatrixResultsSpider, scrape_type=self.scrape_type)
        process.start()

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
        # self.update_pnl()
