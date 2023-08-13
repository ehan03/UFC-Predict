# standard library imports
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src", "scrapers"))

# third party imports
from scrapy.crawler import CrawlerProcess

# local imports
from src.scrapers.ufc_scrapy.spiders.ufc_scrapers import UFCStatsSpider


class PipelineRun:
    def __init__(self, pipeline_codes):
        self.pipeline_codes = pipeline_codes
        self.pipeline_map = {
            "scrape_ufc_stats": self.scrape_ufc_stats,
            "scrape_rankings": None,
            "scrape_fighter_extra_info": None,
            "scrape_odds": None,
            "build_model": None,
            "update_betting_results": None,
        }

    def scrape_ufc_stats(self):
        process = CrawlerProcess()
        process.crawl(UFCStatsSpider)
        process.start()

    def __call__(self):
        for pipeline_code in self.pipeline_codes:
            self.pipeline_map[pipeline_code]()


if __name__ == "__main__":
    assert len(sys.argv) > 1, "Please provide at least one pipeline code"
    pipeline_codes = sys.argv[1:]
    pipeline = PipelineRun(pipeline_codes)
    pipeline()
