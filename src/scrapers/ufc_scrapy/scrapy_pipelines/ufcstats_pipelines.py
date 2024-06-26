# standard library imports
import os
import sqlite3

# third party imports
import pandas as pd

# local imports
from src.databases.create_statements import (
    CREATE_UFCSTATS_BOUTS_BY_ROUND_TABLE,
    CREATE_UFCSTATS_BOUTS_OVERALL_TABLE,
    CREATE_UFCSTATS_FIGHTERS_TABLE,
    CREATE_UFCSTATS_UPCOMING_TABLE,
)
from src.scrapers.ufc_scrapy.items import (
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
            os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "..", "data", "ufcstats.db"
            ),
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self.cur = self.conn.cursor()
        self.cur.execute(CREATE_UFCSTATS_FIGHTERS_TABLE)

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
                    """
                    SELECT 
                      FIGHTER_ID 
                    FROM 
                      UFCSTATS_FIGHTERS 
                    WHERE 
                      FIGHTER_ID = ?;
                    """,
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
            os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "..", "data", "ufcstats.db"
            ),
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self.cur = self.conn.cursor()
        self.cur.execute(CREATE_UFCSTATS_BOUTS_OVERALL_TABLE)
        self.cur.execute(CREATE_UFCSTATS_BOUTS_BY_ROUND_TABLE)

        self.bout_ids_to_flip = [
            "ca93e3f69fa3d725",
            "b4d624bdc27dff83",
            "aefca2869c87eb11",
            "0ea087a71863184d",
            "b091e021e61f1950",
            "5e52b0bf9719f0ae",
            "840863604b38a33f",
            "adddc6e46da5ca19",
            "20628fd4e19a97e4",
            "1a21263dc5d866b6",
            "504b540805598fa5",
            "be72958d9715757d",
            "19f615a7a5cfd304",
            "c4fa93a4f37a6ca7",
            "c99370e3e54bd5fd",
            "d7f9a09021a9a13c",
            "24e14c4824144c64",
        ]

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

        bouts_overall_df = (
            pd.DataFrame(self.bouts_overall)
            .sort_values(by=["DATE", "EVENT_ID", "BOUT_ORDINAL"])
            .reset_index(drop=True)
        )
        bout_ids = bouts_overall_df["BOUT_ID"].values.tolist()
        bouts_by_round_df = (
            pd.DataFrame(self.bouts_by_round)
            .sort_values(
                by=["BOUT_ID", "ROUND"],
                key=lambda x: (
                    x if x.name != "BOUT_ID" else x.map(lambda e: bout_ids.index(e))
                ),
            )
            .reset_index(drop=True)
        )

        flag = True
        if self.scrape_type == "all":
            self.cur.execute(
                """
                DELETE FROM 
                  UFCSTATS_BOUTS_OVERALL;
                """
            )
            self.cur.execute(
                """
                DELETE FROM 
                  UFCSTATS_BOUTS_BY_ROUND;
                """
            )

            swap_map_overall = {
                "RED_FIGHTER_ID": "BLUE_FIGHTER_ID",
                "BLUE_FIGHTER_ID": "RED_FIGHTER_ID",
                "RED_OUTCOME": "BLUE_OUTCOME",
                "BLUE_OUTCOME": "RED_OUTCOME",
            }

            bouts_overall_df.update(
                bouts_overall_df.loc[
                    bouts_overall_df["BOUT_ID"].isin(self.bout_ids_to_flip)
                ].rename(columns=swap_map_overall)
            )

            swap_map_by_round = {
                "RED_KNOCKDOWNS": "BLUE_KNOCKDOWNS",
                "BLUE_KNOCKDOWNS": "RED_KNOCKDOWNS",
                "RED_TOTAL_STRIKES_LANDED": "BLUE_TOTAL_STRIKES_LANDED",
                "BLUE_TOTAL_STRIKES_LANDED": "RED_TOTAL_STRIKES_LANDED",
                "RED_TOTAL_STRIKES_ATTEMPTED": "BLUE_TOTAL_STRIKES_ATTEMPTED",
                "BLUE_TOTAL_STRIKES_ATTEMPTED": "RED_TOTAL_STRIKES_ATTEMPTED",
                "RED_TAKEDOWNS_LANDED": "BLUE_TAKEDOWNS_LANDED",
                "BLUE_TAKEDOWNS_LANDED": "RED_TAKEDOWNS_LANDED",
                "RED_TAKEDOWNS_ATTEMPTED": "BLUE_TAKEDOWNS_ATTEMPTED",
                "BLUE_TAKEDOWNS_ATTEMPTED": "RED_TAKEDOWNS_ATTEMPTED",
                "RED_SUBMISSION_ATTEMPTS": "BLUE_SUBMISSION_ATTEMPTS",
                "BLUE_SUBMISSION_ATTEMPTS": "RED_SUBMISSION_ATTEMPTS",
                "RED_REVERSALS": "BLUE_REVERSALS",
                "BLUE_REVERSALS": "RED_REVERSALS",
                "RED_CONTROL_TIME_SECONDS": "BLUE_CONTROL_TIME_SECONDS",
                "BLUE_CONTROL_TIME_SECONDS": "RED_CONTROL_TIME_SECONDS",
                "RED_SIGNIFICANT_STRIKES_LANDED": "BLUE_SIGNIFICANT_STRIKES_LANDED",
                "BLUE_SIGNIFICANT_STRIKES_LANDED": "RED_SIGNIFICANT_STRIKES_LANDED",
                "RED_SIGNIFICANT_STRIKES_ATTEMPTED": "BLUE_SIGNIFICANT_STRIKES_ATTEMPTED",
                "BLUE_SIGNIFICANT_STRIKES_ATTEMPTED": "RED_SIGNIFICANT_STRIKES_ATTEMPTED",
                "RED_SIGNIFICANT_STRIKES_HEAD_LANDED": "BLUE_SIGNIFICANT_STRIKES_HEAD_LANDED",
                "BLUE_SIGNIFICANT_STRIKES_HEAD_LANDED": "RED_SIGNIFICANT_STRIKES_HEAD_LANDED",
                "RED_SIGNIFICANT_STRIKES_HEAD_ATTEMPTED": "BLUE_SIGNIFICANT_STRIKES_HEAD_ATTEMPTED",
                "BLUE_SIGNIFICANT_STRIKES_HEAD_ATTEMPTED": "RED_SIGNIFICANT_STRIKES_HEAD_ATTEMPTED",
                "RED_SIGNIFICANT_STRIKES_BODY_LANDED": "BLUE_SIGNIFICANT_STRIKES_BODY_LANDED",
                "BLUE_SIGNIFICANT_STRIKES_BODY_LANDED": "RED_SIGNIFICANT_STRIKES_BODY_LANDED",
                "RED_SIGNIFICANT_STRIKES_BODY_ATTEMPTED": "BLUE_SIGNIFICANT_STRIKES_BODY_ATTEMPTED",
                "BLUE_SIGNIFICANT_STRIKES_BODY_ATTEMPTED": "RED_SIGNIFICANT_STRIKES_BODY_ATTEMPTED",
                "RED_SIGNIFICANT_STRIKES_LEG_LANDED": "BLUE_SIGNIFICANT_STRIKES_LEG_LANDED",
                "BLUE_SIGNIFICANT_STRIKES_LEG_LANDED": "RED_SIGNIFICANT_STRIKES_LEG_LANDED",
                "RED_SIGNIFICANT_STRIKES_LEG_ATTEMPTED": "BLUE_SIGNIFICANT_STRIKES_LEG_ATTEMPTED",
                "BLUE_SIGNIFICANT_STRIKES_LEG_ATTEMPTED": "RED_SIGNIFICANT_STRIKES_LEG_ATTEMPTED",
                "RED_SIGNIFICANT_STRIKES_DISTANCE_LANDED": "BLUE_SIGNIFICANT_STRIKES_DISTANCE_LANDED",
                "BLUE_SIGNIFICANT_STRIKES_DISTANCE_LANDED": "RED_SIGNIFICANT_STRIKES_DISTANCE_LANDED",
                "RED_SIGNIFICANT_STRIKES_DISTANCE_ATTEMPTED": "BLUE_SIGNIFICANT_STRIKES_DISTANCE_ATTEMPTED",
                "BLUE_SIGNIFICANT_STRIKES_DISTANCE_ATTEMPTED": "RED_SIGNIFICANT_STRIKES_DISTANCE_ATTEMPTED",
                "RED_SIGNIFICANT_STRIKES_CLINCH_LANDED": "BLUE_SIGNIFICANT_STRIKES_CLINCH_LANDED",
                "BLUE_SIGNIFICANT_STRIKES_CLINCH_LANDED": "RED_SIGNIFICANT_STRIKES_CLINCH_LANDED",
                "RED_SIGNIFICANT_STRIKES_CLINCH_ATTEMPTED": "BLUE_SIGNIFICANT_STRIKES_CLINCH_ATTEMPTED",
                "BLUE_SIGNIFICANT_STRIKES_CLINCH_ATTEMPTED": "RED_SIGNIFICANT_STRIKES_CLINCH_ATTEMPTED",
                "RED_SIGNIFICANT_STRIKES_GROUND_LANDED": "BLUE_SIGNIFICANT_STRIKES_GROUND_LANDED",
                "BLUE_SIGNIFICANT_STRIKES_GROUND_LANDED": "RED_SIGNIFICANT_STRIKES_GROUND_LANDED",
                "RED_SIGNIFICANT_STRIKES_GROUND_ATTEMPTED": "BLUE_SIGNIFICANT_STRIKES_GROUND_ATTEMPTED",
                "BLUE_SIGNIFICANT_STRIKES_GROUND_ATTEMPTED": "RED_SIGNIFICANT_STRIKES_GROUND_ATTEMPTED",
            }

            bouts_by_round_df.update(
                bouts_by_round_df.loc[
                    bouts_by_round_df["BOUT_ID"].isin(self.bout_ids_to_flip)
                ].rename(columns=swap_map_by_round)
            )
        else:
            most_recent_event_id = bouts_overall_df["EVENT_ID"].iloc[0]
            res = self.cur.execute(
                """
                SELECT 
                  EVENT_ID 
                FROM 
                  UFCSTATS_BOUTS_OVERALL 
                WHERE 
                  EVENT_ID = ?;
                """,
                (most_recent_event_id,),
            ).fetchall()
            flag = len(res) == 0

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
            os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "..", "data", "ufcstats.db"
            ),
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
        event_id = upcoming_bouts_df["EVENT_ID"].iloc[0]
        self.cur.execute(
            """
            DELETE FROM 
              UFCSTATS_UPCOMING 
            WHERE 
              EVENT_ID = ?;
            """,
            (event_id,),
        )

        upcoming_bouts_df.to_sql(
            "UFCSTATS_UPCOMING",
            self.conn,
            if_exists="append",
            index=False,
        )

        self.conn.commit()
        self.conn.close()
