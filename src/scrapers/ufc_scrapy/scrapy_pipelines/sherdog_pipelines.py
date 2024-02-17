# standard library imports
import os
import sqlite3

# third party imports
import pandas as pd

# local imports
from src.databases.create_statements import (
    CREATE_SHERDOG_BOUT_HISTORY_TABLE,
    CREATE_SHERDOG_BOUTS_TABLE,
    CREATE_SHERDOG_FIGHTERS_TABLE,
)
from src.scrapers.ufc_scrapy.items import (
    SherdogBoutItem,
    SherdogFighterItem,
    SherdogUpcomingBoutItem,
)


class SherdogFightersPipeline:
    """
    Item pipeline for Sherdog fighter data
    """

    def __init__(self) -> None:
        """
        Initialize pipeline object
        """

        self.scrape_type = None

        self.fighters = []
        self.conn = sqlite3.connect(
            os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "data", "ufc_main.db"
            ),
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self.cur = self.conn.cursor()
        self.cur.execute(CREATE_SHERDOG_FIGHTERS_TABLE)

    def open_spider(self, spider):
        """
        Open the spider
        """

        assert spider.name in ["sherdog_results_spider", "sherdog_upcoming_spider"]
        if spider.name == "sherdog_results_spider":
            self.scrape_type = spider.scrape_type

    def process_item(self, item, spider):
        """
        Process item objects
        """

        if isinstance(item, SherdogFighterItem):
            self.fighters.append(dict(item))

        return item

    def close_spider(self, spider):
        """
        Insert the scraped data into the database and close the spider
        """

        fighters_df = pd.DataFrame(self.fighters)

        if self.scrape_type == "all":
            self.cur.execute("DELETE FROM SHERDOG_FIGHTERS")
        else:
            fighter_ids = fighters_df["FIGHTER_ID"].values.tolist()
            old_ids = []
            for fighter_id in fighter_ids:
                res = self.cur.execute(
                    "SELECT FIGHTER_ID FROM SHERDOG_FIGHTERS WHERE FIGHTER_ID = ?;",
                    (fighter_id,),
                ).fetchall()
                if res:
                    old_ids.append(fighter_id)
            fighters_df = fighters_df[~fighters_df["FIGHTER_ID"].isin(old_ids)]

        if fighters_df.shape[0]:
            fighters_df.to_sql(
                "SHERDOG_FIGHTERS",
                self.conn,
                if_exists="append",
                index=False,
            )

        self.conn.commit()
        self.conn.close()


class SherdogCompletedBoutsPipeline:
    """
    Item pipeline for Sherdog historical bout data
    """

    def __init__(self) -> None:
        """
        Initialize pipeline object
        """

        self.scrape_type = None

        self.bouts = []
        self.conn = sqlite3.connect(
            os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "data", "ufc_main.db"
            ),
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self.cur = self.conn.cursor()
        self.cur.execute(CREATE_SHERDOG_BOUTS_TABLE)

    def open_spider(self, spider):
        """
        Open the spider
        """

        assert spider.name == "sherdog_results_spider"
        self.scrape_type = spider.scrape_type

    def process_item(self, item, spider):
        """
        Process item objects
        """

        if isinstance(item, SherdogBoutItem):
            self.bouts.append(dict(item))

        return item

    def close_spider(self, spider):
        """
        Insert the scraped data into the database and close the spider
        """

        bouts_df = pd.DataFrame(self.bouts).sort_values(
            by=["DATE", "EVENT_ID", "BOUT_ORDINAL"]
        )
        if self.scrape_type == "all":
            self.cur.execute("DELETE FROM SHERDOG_BOUTS")

        flag = True
        if self.scrape_type == "most_recent":
            most_recent_event_id = bouts_df["EVENT_ID"].values[0]
            res = self.cur.execute(
                "SELECT EVENT_ID FROM SHERDOG_BOUTS WHERE EVENT_ID = ?;",
                (most_recent_event_id,),
            ).fetchall()
            flag = len(res) == 0

        if flag:
            bouts_df.to_sql(
                "SHERDOG_BOUTS",
                self.conn,
                if_exists="append",
                index=False,
            )

        self.conn.commit()
        self.conn.close()


class SherdogFighterBoutHistoryPipeline:
    """
    Item pipeline for Sherdog historical bout data beyond those in the UFC
    """

    def __init__(self) -> None:
        """
        Initialize pipeline object
        """

        self.bout_history = []
        self.conn = sqlite3.connect(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "..",
                "data",
                "sherdog_bout_history.db",
            ),
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self.cur = self.conn.cursor()
        self.cur.execute(CREATE_SHERDOG_BOUT_HISTORY_TABLE)


# class SherdogUpcomingBoutsPipeline:
#     """
#     Item pipeline for Sherdog upcoming bout data
#     """

#     def __init__(self) -> None:
#         """
#         Initialize pipeline object
#         """

#         self.upcoming_bouts = []
#         self.conn = sqlite3.connect(
#             os.path.join(
#                 os.path.dirname(__file__), "..", "..", "..", "data", "ufc_main.db"
#             ),
#             detect_types=sqlite3.PARSE_DECLTYPES,
#         )
#         self.cur = self.conn.cursor()
#         self.cur.execute(CREATE_SHERDOG_UPCOMING_TABLE)

#     def open_spider(self, spider):
#         """
#         Open the spider
#         """

#         assert spider.name == "sherdog_upcoming_spider"

#     def process_item(self, item, spider):
#         """
#         Process item objects
#         """

#         if isinstance(item, SherdogUpcomingBoutItem):
#             self.upcoming_bouts.append(dict(item))

#         return item

#     def close_spider(self, spider):
#         """
#         Insert the scraped data into the database and close the spider
#         """

#         upcoming_bouts_df = pd.DataFrame(self.upcoming_bouts)
#         event_id = upcoming_bouts_df["EVENT_ID"].values[0]
#         self.cur.execute(
#             "DELETE FROM SHERDOG_UPCOMING WHERE EVENT_ID = ?;", (event_id,)
#         )

#         upcoming_bouts_df.to_sql(
#             "SHERDOG_UPCOMING",
#             self.conn,
#             if_exists="append",
#             index=False,
#         )

#         self.conn.commit()
#         self.conn.close()
