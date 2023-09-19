# standard library imports
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scrapers"))

# third party imports
from scrapy.crawler import CrawlerProcess

# local imports
from src.pipelines.base import Pipeline
from src.scrapers.ufc_scrapy.spiders.ufc_scrapers import TapologySpider, UFCStatsSpider


class ResultsPipeline(Pipeline):
    """
    Pipeline for scraping event outcomes, computing PnL, and storing results
    """

    def scrape_ufcstats_tapology_results(self):
        """
        Scrape results from UFCStats and Tapology
        """

        process = CrawlerProcess({"LOG_LEVEL": "INFO"})
        process.crawl(UFCStatsSpider, scrape_type="most_recent")
        process.crawl(TapologySpider, scrape_type="most_recent")
        process.start()

    def compute_pnl(self):
        """
        Compute PnL
        """

        pass

    def __call__(self):
        """
        Run pipeline
        """

        self.scrape_ufcstats_tapology_results()
        self.compute_pnl()
