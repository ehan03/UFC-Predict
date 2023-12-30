"""
This module contains the item pipelines for the various scrapers
"""

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
    CREATE_UFCSTATS_BOUTS_BY_ROUND_TABLE,
    CREATE_UFCSTATS_BOUTS_OVERALL_TABLE,
    CREATE_UFCSTATS_FIGHTERS_TABLE,
)
from src.scrapers.ufc_scrapy.items import (
    FightOddsIOBoutItem,
    FightOddsIOFighterItem,
    UFCStatsBoutOverallItem,
    UFCStatsBoutRoundItem,
    UFCStatsFighterItem,
)


class UFCStatsResultsPipeline:
    """
    Item pipeline for UFC Stats historical bouts and fighters data
    """

    def __init__(self) -> None:
        """
        Initialize pipeline object
        """

        self.scrape_type = None

        self.fighters = []
        self.bouts_overall = []
        self.bouts_by_round = []

        self.conn = sqlite3.connect(
            os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "data", "results.db"
            ),
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self.cur = self.conn.cursor()
        self.cur.execute(CREATE_UFCSTATS_FIGHTERS_TABLE)
        self.cur.execute(CREATE_UFCSTATS_BOUTS_OVERALL_TABLE)
        self.cur.execute(CREATE_UFCSTATS_BOUTS_BY_ROUND_TABLE)

    def open_spider(self, spider):
        """
        Open the spider
        """

        assert spider.name == "ufcstats_spider"
        self.scrape_type = spider.scrape_type

    def process_item(self, item, spider):
        """
        Process item objects
        """

        if isinstance(item, UFCStatsFighterItem):
            self.fighters.append(dict(item))
        elif isinstance(item, UFCStatsBoutOverallItem):
            self.bouts_overall.append(dict(item))
        elif isinstance(item, UFCStatsBoutRoundItem):
            self.bouts_by_round.append(dict(item))

        return item

    def close_spider(self, spider):
        """
        Insert the scraped data into the database and close the spider
        """

        if self.scrape_type == "all":
            self.cur.execute("DELETE FROM UFCSTATS_FIGHTERS")
            self.cur.execute("DELETE FROM UFCSTATS_BOUTS_OVERALL")
            self.cur.execute("DELETE FROM UFCSTATS_BOUTS_BY_ROUND")

        fighters_df = pd.DataFrame(self.fighters)
        bouts_overall_df = pd.DataFrame(self.bouts_overall).sort_values(
            by=["DATE", "BOUT_ORDINAL"]
        )
        bout_ids = bouts_overall_df["BOUT_ID"].values.tolist()
        bouts_by_round_df = pd.DataFrame(self.bouts_by_round).sort_values(
            by=["BOUT_ID", "ROUND"],
            key=lambda x: x
            if x.name != "BOUT_ID"
            else x.map(lambda e: bout_ids.index(e)),
        )

        if self.scrape_type == "most_recent":
            fighter_ids = fighters_df["FIGHTER_ID"].values.tolist()
            self.cur.executemany(
                "DELETE FROM UFCSTATS_FIGHTERS WHERE FIGHTER_ID = ?;",
                [(e,) for e in fighter_ids],
            )
            self.cur.executemany(
                "DELETE FROM UFCSTATS_BOUTS_OVERALL WHERE BOUT_ID = ?;",
                [(e,) for e in bout_ids],
            )
            self.cur.executemany(
                "DELETE FROM UFCSTATS_BOUTS_BY_ROUND WHERE BOUT_ID = ?;",
                [(e,) for e in bout_ids],
            )

        fighters_df.to_sql(
            "UFCSTATS_FIGHTERS",
            self.conn,
            if_exists="append",
            index=False,
        )
        bouts_overall_df.to_sql(
            "UFCSTATS_BOUTS_OVERALL",
            self.conn,
            if_exists="append",
            index=False,
        )
        bouts_by_round_df.to_sql(
            "UFCSTATS_BOUTS_BY_ROUND",
            self.conn,
            if_exists="append",
            index=False,
        )

        self.conn.commit()
        self.conn.close()


class FightOddsIOFightersDuplicatesPipeline:
    """
    Item pipeline for filtering out duplicate fighter items when
    scraping FightOdds.io
    """

    def __init__(self) -> None:
        """
        Initialize pipeline object
        """

        self.fighter_slugs_seen = set()

    def open_spider(self, spider):
        """
        Open the spider
        """

        assert spider.name == "fightoddsio_spider"

    def process_item(self, item, spider):
        if isinstance(item, FightOddsIOFighterItem):
            adapter = ItemAdapter(item)
            if adapter["FIGHTER_SLUG"] in self.fighter_slugs_seen:
                raise DropItem("Duplicate fighter")
            else:
                self.fighter_slugs_seen.add(adapter["FIGHTER_SLUG"])

        return item


class FightOddsIOResultsPipeline:
    """
    Item pipeline for FightOdds.io historical bouts and fighters data
    """

    def __init__(self) -> None:
        """
        Initialize pipeline object
        """

        self.scrape_type = None

        self.fighters = []
        self.bouts = []

        self.conn = sqlite3.connect(
            os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "data", "results.db"
            ),
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self.cur = self.conn.cursor()
        self.cur.execute(CREATE_FIGHTODDSIO_FIGHTERS_TABLE)
        self.cur.execute(CREATE_FIGHTODDSIO_BOUTS_TABLE)

    def open_spider(self, spider):
        """
        Open the spider
        """

        assert spider.name == "fightoddsio_spider"
        self.scrape_type = spider.scrape_type

    def process_item(self, item, spider):
        """
        Process item objects
        """

        if isinstance(item, FightOddsIOFighterItem):
            self.fighters.append(dict(item))
        elif isinstance(item, FightOddsIOBoutItem):
            self.bouts.append(dict(item))

        return item

    def close_spider(self, spider):
        """
        Insert the scraped data into the database and close the spider
        """

        if self.scrape_type == "all":
            self.cur.execute("DELETE FROM FIGHTODDSIO_FIGHTERS")
            self.cur.execute("DELETE FROM FIGHTODDSIO_BOUTS")

        fighters_df = pd.DataFrame(self.fighters)
        bouts_df = pd.DataFrame(self.bouts).sort_values(by=["DATE", "BOUT_ORDINAL"])

        if self.scrape_type == "most_recent":
            fighter_slugs = fighters_df["FIGHTER_SLUG"].values.tolist()
            self.cur.executemany(
                "DELETE FROM FIGHTODDSIO_FIGHTERS WHERE FIGHTER_SLUG = ?;",
                [(e,) for e in fighter_slugs],
            )
            bout_slugs = bouts_df["BOUT_SLUG"].values.tolist()
            self.cur.executemany(
                "DELETE FROM FIGHTODDSIO_BOUTS WHERE BOUT_SLUG = ?;",
                [(e,) for e in bout_slugs],
            )

        fighters_df.to_sql(
            "FIGHTODDSIO_FIGHTERS",
            self.conn,
            if_exists="append",
            index=False,
        )
        bouts_df.to_sql(
            "FIGHTODDSIO_BOUTS",
            self.conn,
            if_exists="append",
            index=False,
        )

        self.conn.commit()
        self.conn.close()
