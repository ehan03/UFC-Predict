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
        process = CrawlerProcess(
            {
                "BOT_NAME": "ufc_scrapy",
                "SPIDER_MODULES": ["ufc_scrapy.spiders"],
                "NEWSPIDER_MODULE": "ufc_scrapy.spiders",
                "ROBOTSTXT_OBEY": False,
                "CONCURRENT_REQUESTS_PER_DOMAIN": 10,
                "CONCURRENT_REQUESTS": 10,
                "DOWNLOADER_MIDDLEWARES": {
                    "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
                    "scrapy_user_agents.middlewares.RandomUserAgentMiddleware": 400,
                },
                "REQUEST_FINGERPRINTER_IMPLEMENTATION": "2.7",
                "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
                "FEED_EXPORT_ENCODING": "utf-8",
                "DEPTH_PRIORITY": 1,
                "SCHEDULER_DISK_QUEUE": "scrapy.squeues.PickleFifoDiskQueue",
                "SCHEDULER_MEMORY_QUEUE": "scrapy.squeues.FifoMemoryQueue",
                "RETRY_TIMES": 5,
                "LOG_LEVEL": "INFO",
            }
        )
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
