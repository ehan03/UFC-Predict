# standard library imports
import os
import sqlite3

# third party imports
import pandas as pd
from itemadapter.adapter import ItemAdapter
from scrapy.exceptions import DropItem

# local imports
from src.databases.create_statements import (
    CREATE_FIGHTODDSIO_BOUTS_TABLE,
    CREATE_FIGHTODDSIO_FIGHTERS_TABLE,
    CREATE_FIGHTODDSIO_UPCOMING_TABLE,
)
from src.scrapers.ufc_scrapy.items import (
    FightOddsIOBoutItem,
    FightOddsIOClosingOddsItem,
    FightOddsIOFighterItem,
    FightOddsIOUpcomingBoutItem,
)


class FightOddsIOFightersPipeline:
    """
    Item pipeline for FightOdds.io fighter data
    """

    def __init__(self) -> None:
        """
        Initialize pipeline object
        """

        self.scrape_type = None

        self.fighters = []
        self.fighter_slugs_seen = set()
        self.conn = sqlite3.connect(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "..",
                "..",
                "data",
                "fightoddsio.db",
            ),
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self.cur = self.conn.cursor()
        self.cur.execute(CREATE_FIGHTODDSIO_FIGHTERS_TABLE)

    def open_spider(self, spider):
        """
        Open the spider
        """

        assert spider.name == "fightoddsio_results_spider"
        self.scrape_type = spider.scrape_type

    def process_item(self, item, spider):
        if isinstance(item, FightOddsIOFighterItem):
            adapter = ItemAdapter(item)
            if adapter["FIGHTER_ID"] in self.fighter_slugs_seen:
                raise DropItem("Duplicate fighter")
            else:
                self.fighter_slugs_seen.add(adapter["FIGHTER_ID"])
                self.fighters.append(dict(item))

        return item

    def close_spider(self, spider):
        """
        Insert the scraped data into the database and close the spider
        """

        fighters_df = pd.DataFrame(self.fighters)

        if self.scrape_type == "all":
            self.cur.execute(
                """
                DELETE FROM 
                  FIGHTODDSIO_FIGHTERS;
                """
            )
        else:
            fighter_ids = fighters_df["FIGHTER_ID"].values.tolist()
            old_slugs = []
            for fighter_id in fighter_ids:
                res = self.cur.execute(
                    """
                    SELECT 
                      FIGHTER_ID
                    FROM 
                      FIGHTODDSIO_FIGHTERS 
                    WHERE 
                      FIGHTER_ID = ?;
                    """,
                    (fighter_id,),
                ).fetchall()
                if res:
                    old_slugs.append(fighter_id)
            fighters_df = fighters_df[~fighters_df["FIGHTER_ID"].isin(old_slugs)]

        if fighters_df.shape[0]:
            fighters_df.to_sql(
                "FIGHTODDSIO_FIGHTERS",
                self.conn,
                if_exists="append",
                index=False,
            )

        self.conn.commit()
        self.conn.close()


class FightOddsIOCompletedBoutsPipeline:
    """
    Item pipeline for FightOdds.io historical bout data
    """

    def __init__(self) -> None:
        """
        Initialize pipeline object
        """

        self.scrape_type = None

        self.bouts = []
        self.bout_odds = []
        self.conn = sqlite3.connect(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "..",
                "..",
                "data",
                "fightoddsio.db",
            ),
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self.cur = self.conn.cursor()
        self.cur.execute(CREATE_FIGHTODDSIO_BOUTS_TABLE)

    def open_spider(self, spider):
        """
        Open the spider
        """

        assert spider.name == "fightoddsio_results_spider"
        self.scrape_type = spider.scrape_type

    def process_item(self, item, spider):
        """
        Process item objects
        """

        if isinstance(item, FightOddsIOBoutItem):
            self.bouts.append(dict(item))
        elif isinstance(item, FightOddsIOClosingOddsItem):
            self.bout_odds.append(dict(item))

        return item

    def close_spider(self, spider):
        """
        Insert the scraped data into the database and close the spider
        """

        bouts_df = pd.DataFrame(self.bouts).sort_values(
            by=["DATE", "EVENT_SLUG", "BOUT_ORDINAL"]
        )
        odds_df = pd.DataFrame(self.bout_odds)

        flag = True
        if self.scrape_type == "all":
            self.cur.execute(
                """
                DELETE FROM 
                  FIGHTODDSIO_BOUTS;
                """
            )
        else:
            most_recent_event_slug = bouts_df["EVENT_SLUG"].values[0]
            res = self.cur.execute(
                """
                SELECT 
                  EVENT_SLUG 
                FROM 
                  FIGHTODDSIO_BOUTS 
                WHERE 
                  EVENT_SLUG = ?;
                """,
                (most_recent_event_slug,),
            ).fetchall()
            flag = len(res) == 0

        if flag:
            bouts_with_odds_df = bouts_df.merge(odds_df, how="left", on="BOUT_SLUG")

            bouts_with_odds_df.to_sql(
                "FIGHTODDSIO_BOUTS",
                self.conn,
                if_exists="append",
                index=False,
            )

        self.conn.commit()
        self.conn.close()


class FightOddsIOUpcomingBoutsPipeline:
    """
    Item pipeline for FightOdds.io upcoming bout data
    """

    def __init__(self) -> None:
        """
        Initialize pipeline object
        """

        self.upcoming_bouts = []
        self.conn = sqlite3.connect(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "..",
                "..",
                "data",
                "fightoddsio.db",
            ),
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self.cur = self.conn.cursor()
        self.cur.execute(CREATE_FIGHTODDSIO_UPCOMING_TABLE)

    def open_spider(self, spider):
        """
        Open the spider
        """

        assert spider.name == "fightoddsio_upcoming_spider"

    def process_item(self, item, spider):
        """
        Process item objects
        """

        if isinstance(item, FightOddsIOUpcomingBoutItem):
            self.upcoming_bouts.append(dict(item))

        return item

    def close_spider(self, spider):
        """
        Insert the scraped data into the database and close the spider
        """

        upcoming_bouts_df = pd.DataFrame(self.upcoming_bouts)
        event_slug = upcoming_bouts_df["EVENT_SLUG"].values[0]
        self.cur.execute(
            """
            DELETE FROM 
              FIGHTODDSIO_UPCOMING 
            WHERE 
              EVENT_SLUG = ?;
            """,
            (event_slug,),
        )

        upcoming_bouts_df.to_sql(
            "FIGHTODDSIO_UPCOMING",
            self.conn,
            if_exists="append",
            index=False,
        )

        self.conn.commit()
        self.conn.close()
