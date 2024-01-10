# standard library imports
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scrapers"))

# third party imports
from scrapy.crawler import CrawlerProcess

# local imports
from src.fighter_matching import FighterMatcher
from src.scrapers.ufc_scrapy.spiders.ufc_scrapers import (
    FightOddsIOUpcomingEventSpider,
    UFCStatsUpcomingEventSpider,
)


class UpcomingEventPipeline:
    """
    Class for handling upcoming UFC events
    """

    def get_upcoming_event(self):
        """
        Get upcoming event data from UFC Stats and FightOdds.io
        """

        process = CrawlerProcess(settings={"LOG_LEVEL": "INFO"})
        process.crawl(UFCStatsUpcomingEventSpider)
        process.crawl(FightOddsIOUpcomingEventSpider)
        process.start()

    def update_ufcstats_fightoddsio_linkage(self):
        """
        Update linkage between UFCStats and FightOdds.io
        """

        fighter_matcher = FighterMatcher(matching_type="upcoming")
        fighter_matcher()

    def get_predictions(self):
        pass

    def get_wagers(self):
        pass

    def __call__(self):
        """
        Run the pipeline
        """

        self.get_upcoming_event()
        self.update_ufcstats_fightoddsio_linkage()
