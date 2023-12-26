"""
This module contains the item pipelines for the various scrapers
"""

# standard library imports

# third party imports
import pandas as pd

# local imports
from src.scrapers.ufc_scrapy.items import (
    FightMatrixFighterItem,
    FightMatrixRankingItem,
    FightOddsIOBoutItem,
    TapologyBoutItem,
    TapologyFighterItem,
    UFCStatsBoutOverallItem,
    UFCStatsBoutRoundItem,
    UFCStatsFighterItem,
)


class UFCStatsFightersPipeline:
    """
    Item pipeline for UFC Stats fighters data
    """

    def __init__(self) -> None:
        """
        Initialize pipeline object
        """

        self.scrape_type = None
        self.rows = []

    def open_spider(self, spider):
        """
        Open the spider
        """

        assert spider.name == "ufcstats_spider"
        self.scrape_type = spider.scrape_type

    def process_item(self, item, spider):
        """
        Process UFCStatsFighterItem objects
        """

        if isinstance(item, UFCStatsFighterItem):
            self.rows.append(item)

        return item

    def close_spider(self, spider):
        """
        Upsert the scraped data into the database and close the spider
        """


class UFCStatsBoutsPipeline:
    """
    Item pipeline for UFC Stats bout data, including overall and by round
    """

    def __init__(self) -> None:
        """
        Initialize the pipeline class
        """

        self.scrape_type = None
        self.rows_overall = []
        self.rows_by_round = []

    def open_spider(self, spider):
        """
        Open the spider
        """

        assert spider.name == "ufcstats_spider"
        self.scrape_type = spider.scrape_type

    def process_item(self, item, spider):
        """
        Process UFCStatsBoutOverallItem and UFCStatsBoutRoundItem objects
        """

        if isinstance(item, UFCStatsBoutOverallItem):
            self.rows_overall.append(item)
        elif isinstance(item, UFCStatsBoutRoundItem):
            self.rows_by_round.append(item)

        return item

    def close_spider(self, spider):
        """
        Upsert the scraped data into the database and close the spider
        """


class TapologyFightersPipeline:
    """
    Item pipeline for Tapology fighter data
    """


class TapologyBoutsPipeline:
    """
    Item pipeline for Tapology bout data
    """

    def __init__(self) -> None:
        """
        Initialize the pipeline class
        """

        self.scrape_type = None
        self.rows = []

    def open_spider(self, spider):
        """
        Open the spider
        """

        assert spider.name == "tapology_spider"
        self.scrape_type = spider.scrape_type

    def process_item(self, item, spider):
        """
        Process TapologyBoutItem objects
        """

        if isinstance(item, TapologyBoutItem):
            self.rows.append(item)

        return item

    def close_spider(self, spider):
        """
        Inserts the scraped data into the database and closes the spider
        """


class FightMatrixFightersPipeline:
    """
    Item pipeline for Fight Matrix fighter data
    """


class FightMatrixRankingsPipeline:
    """
    Item pipeline for Fight Matrix rankings data
    """


class UFCStatsUpcomingEventPipeline:
    """
    Item pipeline for upcoming event data from UFCStats
    """


class TapologyUpcomingEventPipeline:
    """
    Item pipeline for upcoming event data from Tapology
    """


class FightOddsUpcomingEventPipeline:
    """
    Item pipeline for upcoming event betting odds data from Fight Odds
    """
