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
    CREATE_FIGHTODDSIO_UPCOMING_TABLE,
    CREATE_UFCSTATS_BOUTS_BY_ROUND_TABLE,
    CREATE_UFCSTATS_BOUTS_OVERALL_TABLE,
    CREATE_UFCSTATS_FIGHTERS_TABLE,
    CREATE_UFCSTATS_UPCOMING_TABLE,
)
from src.scrapers.ufc_scrapy.items import (
    FightOddsIOBoutItem,
    FightOddsIOFighterItem,
    FightOddsIOUpcomingBoutItem,
    UFCStatsBoutOverallItem,
    UFCStatsBoutRoundItem,
    UFCStatsFighterItem,
    UFCStatsUpcomingBoutItem,
)


class UFCStatsFightersPipeline:
    """
    Item pipeline for UFC Stats fighter data
    """

    def __init__(self) -> None:
        """
        Initialize pipeline object
        """

        self.scrape_type = None

        self.fighters = []
        self.conn = sqlite3.connect(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "ufc.db"),
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self.cur = self.conn.cursor()
        self.cur.execute(CREATE_UFCSTATS_FIGHTERS_TABLE)

    def open_spider(self, spider):
        """
        Open the spider
        """

        assert spider.name in ["ufcstats_results_spider", "ufcstats_upcoming_spider"]
        if spider.name == "ufcstats_results_spider":
            self.scrape_type = spider.scrape_type

    def process_item(self, item, spider):
        """
        Process item objects
        """

        if isinstance(item, UFCStatsFighterItem):
            self.fighters.append(dict(item))

        return item

    def close_spider(self, spider):
        """
        Insert the scraped data into the database and close the spider
        """

        fighters_df = pd.DataFrame(self.fighters)

        if self.scrape_type == "all":
            self.cur.execute("DELETE FROM UFCSTATS_FIGHTERS")
        else:
            fighter_ids = fighters_df["FIGHTER_ID"].values.tolist()
            old_ids = []
            for fighter_id in fighter_ids:
                res = self.cur.execute(
                    "SELECT FIGHTER_ID FROM UFCSTATS_FIGHTERS WHERE FIGHTER_ID = ?;",
                    (fighter_id,),
                ).fetchall()
                if res:
                    old_ids.append(fighter_id)
            fighters_df = fighters_df[~fighters_df["FIGHTER_ID"].isin(old_ids)]

        if fighters_df.shape[0]:
            fighters_df.to_sql(
                "UFCSTATS_FIGHTERS",
                self.conn,
                if_exists="append",
                index=False,
            )

        self.conn.commit()
        self.conn.close()


class UFCStatsCompletedBoutsPipeline:
    """
    Item pipeline for UFC Stats historical bout data
    """

    def __init__(self) -> None:
        """
        Initialize pipeline object
        """

        self.scrape_type = None

        self.bouts_overall = []
        self.bouts_by_round = []
        self.conn = sqlite3.connect(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "ufc.db"),
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self.cur = self.conn.cursor()
        self.cur.execute(CREATE_UFCSTATS_BOUTS_OVERALL_TABLE)
        self.cur.execute(CREATE_UFCSTATS_BOUTS_BY_ROUND_TABLE)

    def open_spider(self, spider):
        """
        Open the spider
        """

        assert spider.name == "ufcstats_results_spider"
        self.scrape_type = spider.scrape_type

    def process_item(self, item, spider):
        """
        Process item objects
        """

        if isinstance(item, UFCStatsBoutOverallItem):
            self.bouts_overall.append(dict(item))
        elif isinstance(item, UFCStatsBoutRoundItem):
            self.bouts_by_round.append(dict(item))

        return item

    def close_spider(self, spider):
        """
        Insert the scraped data into the database and close the spider
        """

        bouts_overall_df = pd.DataFrame(self.bouts_overall).sort_values(
            by=["DATE", "EVENT_ID", "BOUT_ORDINAL"]
        )
        bout_ids = bouts_overall_df["BOUT_ID"].values.tolist()
        bouts_by_round_df = pd.DataFrame(self.bouts_by_round).sort_values(
            by=["BOUT_ID", "ROUND"],
            key=lambda x: x
            if x.name != "BOUT_ID"
            else x.map(lambda e: bout_ids.index(e)),
        )

        if self.scrape_type == "all":
            self.cur.execute("DELETE FROM UFCSTATS_BOUTS_OVERALL")
            self.cur.execute("DELETE FROM UFCSTATS_BOUTS_BY_ROUND")

        flag = True
        if self.scrape_type == "most_recent":
            most_recent_event_id = bouts_overall_df["EVENT_ID"].values[0]
            res = self.cur.execute(
                "SELECT EVENT_ID FROM UFCSTATS_BOUTS_OVERALL WHERE EVENT_ID = ?;",
                (most_recent_event_id,),
            ).fetchall()
            flag = len(res) == 0

            if flag:
                unknown_gender: pd.DataFrame = bouts_overall_df.loc[
                    bouts_overall_df["BOUT_GENDER"].isna(),
                    ["BOUT_ID", "RED_FIGHTER_ID", "BLUE_FIGHTER_ID"],
                ]
                for row in unknown_gender.itertuples():
                    gender = self.cur.execute(
                        "SELECT DISTINCT BOUT_GENDER FROM UFCSTATS_BOUTS_OVERALL WHERE RED_FIGHTER_ID IN (?, ?) OR BLUE_FIGHTER_ID IN (?, ?);",
                        (row.RED_FIGHTER_ID, row.BLUE_FIGHTER_ID),
                    ).fetchone()[0]
                    bouts_overall_df.loc[
                        bouts_overall_df["BOUT_ID"] == row.BOUT_ID, "BOUT_GENDER"
                    ] = gender
        else:
            unknown_gender: pd.DataFrame = bouts_overall_df.loc[
                bouts_overall_df["BOUT_GENDER"].isna(),
                ["BOUT_ID", "RED_FIGHTER_ID", "BLUE_FIGHTER_ID"],
            ]
            for row in unknown_gender.itertuples():
                gender = bouts_overall_df.loc[
                    bouts_overall_df["BOUT_GENDER"].notna()
                    & (
                        bouts_overall_df["RED_FIGHTER_ID"].isin(
                            [row.RED_FIGHTER_ID, row.BLUE_FIGHTER_ID]
                        )
                        | bouts_overall_df["BLUE_FIGHTER_ID"].isin(
                            [row.RED_FIGHTER_ID, row.BLUE_FIGHTER_ID]
                        )
                    ),
                    "BOUT_GENDER",
                ].unique()[0]
                bouts_overall_df.loc[
                    bouts_overall_df["BOUT_ID"] == row.BOUT_ID, "BOUT_GENDER"
                ] = gender

        if flag:
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


class UFCStatsUpcomingBoutsPipeline:
    """
    Item pipeline for UFC Stats upcoming bout data
    """

    def __init__(self) -> None:
        """
        Initialize pipeline object
        """

        self.upcoming_bouts = []
        self.conn = sqlite3.connect(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "ufc.db"),
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self.cur = self.conn.cursor()
        self.cur.execute(CREATE_UFCSTATS_UPCOMING_TABLE)

    def open_spider(self, spider):
        """
        Open the spider
        """

        assert spider.name == "ufcstats_upcoming_spider"

    def process_item(self, item, spider):
        """
        Process item objects
        """

        if isinstance(item, UFCStatsUpcomingBoutItem):
            self.upcoming_bouts.append(dict(item))

        return item

    def close_spider(self, spider):
        """
        Insert the scraped data into the database and close the spider
        """

        upcoming_bouts_df = pd.DataFrame(self.upcoming_bouts).sort_values(
            by=["BOUT_ORDINAL"]
        )
        event_id = upcoming_bouts_df["EVENT_ID"].values[0]
        self.cur.execute(
            "DELETE FROM UFCSTATS_UPCOMING WHERE EVENT_ID = ?;", (event_id,)
        )

        unknown_gender: pd.DataFrame = upcoming_bouts_df.loc[
            upcoming_bouts_df["BOUT_GENDER"].isna(),
            ["BOUT_ID", "RED_FIGHTER_ID", "BLUE_FIGHTER_ID"],
        ]
        for row in unknown_gender.itertuples():
            gender = self.cur.execute(
                "SELECT DISTINCT BOUT_GENDER FROM UFCSTATS_BOUTS_OVERALL WHERE RED_FIGHTER_ID IN (?, ?) OR BLUE_FIGHTER_ID IN (?, ?);",
                (row.RED_FIGHTER_ID, row.BLUE_FIGHTER_ID),
            ).fetchone()[0]
            upcoming_bouts_df.loc[
                upcoming_bouts_df["BOUT_ID"] == row.BOUT_ID, "BOUT_GENDER"
            ] = gender

        upcoming_bouts_df.to_sql(
            "UFCSTATS_UPCOMING",
            self.conn,
            if_exists="append",
            index=False,
        )

        self.conn.commit()
        self.conn.close()


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
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "ufc.db"),
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self.cur = self.conn.cursor()
        self.cur.execute(CREATE_FIGHTODDSIO_FIGHTERS_TABLE)

    def open_spider(self, spider):
        """
        Open the spider
        """

        assert spider.name in [
            "fightoddsio_results_spider",
            "fightoddsio_upcoming_spider",
        ]
        if spider.name == "fightoddsio_results_spider":
            self.scrape_type = spider.scrape_type

    def process_item(self, item, spider):
        if isinstance(item, FightOddsIOFighterItem):
            adapter = ItemAdapter(item)
            if adapter["FIGHTER_SLUG"] in self.fighter_slugs_seen:
                raise DropItem("Duplicate fighter")
            else:
                self.fighter_slugs_seen.add(adapter["FIGHTER_SLUG"])
                self.fighters.append(dict(item))

        return item

    def close_spider(self, spider):
        """
        Insert the scraped data into the database and close the spider
        """

        fighters_df = pd.DataFrame(self.fighters)

        if self.scrape_type == "all":
            self.cur.execute("DELETE FROM FIGHTODDSIO_FIGHTERS")
        else:
            fighter_slugs = fighters_df["FIGHTER_SLUG"].values.tolist()
            old_slugs = []
            for fighter_slug in fighter_slugs:
                res = self.cur.execute(
                    "SELECT FIGHTER_SLUG FROM FIGHTODDSIO_FIGHTERS WHERE FIGHTER_SLUG = ?;",
                    (fighter_slug,),
                ).fetchall()
                if res:
                    old_slugs.append(fighter_slug)
            fighters_df = fighters_df[~fighters_df["FIGHTER_SLUG"].isin(old_slugs)]

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
        self.conn = sqlite3.connect(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "ufc.db"),
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

        return item

    def close_spider(self, spider):
        """
        Insert the scraped data into the database and close the spider
        """

        bouts_df = pd.DataFrame(self.bouts).sort_values(
            by=["DATE", "EVENT_SLUG", "BOUT_ORDINAL"]
        )

        flag = True
        if self.scrape_type == "most_recent":
            most_recent_event_slug = bouts_df["EVENT_SLUG"].values[0]
            res = self.cur.execute(
                "SELECT EVENT_SLUG FROM FIGHTODDSIO_BOUTS WHERE EVENT_SLUG = ?;",
                (most_recent_event_slug,),
            ).fetchall()
            flag = len(res) == 0

        if flag:
            bouts_df.to_sql(
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
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "ufc.db"),
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
            "DELETE FROM FIGHTODDSIO_UPCOMING WHERE EVENT_SLUG = ?;", (event_slug,)
        )

        upcoming_bouts_df.to_sql(
            "FIGHTODDSIO_UPCOMING",
            self.conn,
            if_exists="append",
            index=False,
        )

        self.conn.commit()
        self.conn.close()
