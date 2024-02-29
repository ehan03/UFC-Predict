# standard library imports
import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta, timezone

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scrapers"))

# third party imports
from scrapy.crawler import CrawlerProcess

# local imports
from src.scrapers.ufc_scrapy.spiders.fightmatrix_spiders import (
    FightMatrixRankingsSpider,
)


class RankingsPipeline:
    """
    Class for handling most recent FightMatrix rankings
    """

    def __init__(self):
        """
        Initialize RankingsPipeline class
        """

        self.scrape_type = "most_recent"
        self.conn = sqlite3.connect(
            os.path.join(
                os.path.dirname(__file__), "..", "..", "data", "fightmatrix.db"
            ),
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self.cur = self.conn.cursor()
        self.date_today = datetime.now(timezone.utc).date()

    def first_sunday_of_month(self):
        """
        Get the first Sunday of current month
        """

        first_day_of_month = self.date_today.replace(day=1)
        offset = (6 - first_day_of_month.weekday()) % 7
        first_sunday = (first_day_of_month + timedelta(days=offset)).strftime(
            "%Y-%m-%d"
        )

        return first_sunday

    def get_rankings(self):
        """
        Get most recent FightMatrix rankings
        """

        process = CrawlerProcess(settings={"LOG_LEVEL": "INFO"})
        process.crawl(FightMatrixRankingsSpider, scrape_type=self.scrape_type)
        process.start()

    def __call__(self):
        """
        Run the pipeline
        """

        first_sunday = self.first_sunday_of_month()
        date_today_string = self.date_today.strftime("%Y-%m-%d")
        res = self.cur.execute(
            """
            SELECT
              ISSUE_DATE
            FROM
              FIGHTMATRIX_RANKINGS
            WHERE
              ISSUE_DATE = ?;
            """,
            (first_sunday,),
        ).fetchall()

        if (
            time.strptime(date_today_string, "%Y-%m-%d")
            > time.strptime(first_sunday, "%Y-%m-%d")
            and not res
        ):
            self.get_rankings()
