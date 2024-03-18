# standard library imports
import os
import sqlite3

# third party imports
import pandas as pd

# local imports
from src.databases.create_statements import (
    CREATE_FIGHTMATRIX_BOUTS_TABLE,
    CREATE_FIGHTMATRIX_FIGHTERS_TABLE,
    CREATE_FIGHTMATRIX_RANKINGS_TABLE,
)
from src.scrapers.ufc_scrapy.items import (
    FightMatrixBoutItem,
    FightMatrixFighterItem,
    FightMatrixRankingItem,
)


class FightMatrixFightersPipeline:
    """
    Item pipeline for FightMatrix fighters data
    """

    def __init__(self) -> None:
        """
        Initialize pipeline object
        """

        self.scrape_type = None

        self.fighters = []
        self.conn = sqlite3.connect(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "..",
                "..",
                "data",
                "fightmatrix.db",
            ),
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self.cur = self.conn.cursor()
        self.cur.execute(CREATE_FIGHTMATRIX_FIGHTERS_TABLE)

    def open_spider(self, spider):
        """
        Open the spider
        """

        assert spider.name == "fightmatrix_results_spider"
        self.scrape_type = spider.scrape_type

    def process_item(self, item, spider):
        """
        Process item objects
        """

        if isinstance(item, FightMatrixFighterItem):
            self.fighters.append(dict(item))

        return item

    def close_spider(self, spider):
        """
        Close the spider
        """

        fighters_df = pd.DataFrame(self.fighters)

        if self.scrape_type == "all":
            self.cur.execute(
                """
                DELETE FROM 
                  FIGHTMATRIX_FIGHTERS;
                """
            )
        else:
            fighter_ids = fighters_df["FIGHTER_ID"].values.tolist()
            old_ids = []
            for fighter_id in fighter_ids:
                res = self.cur.execute(
                    """
                    SELECT 
                      FIGHTER_ID 
                    FROM 
                      FIGHTMATRIX_FIGHTERS 
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
                "FIGHTMATRIX_FIGHTERS",
                self.conn,
                if_exists="append",
                index=False,
            )

        self.conn.commit()
        self.conn.close()


class FightMatrixBoutsPipeline:
    """
    Item pipeline for FightMatrix bouts data
    """

    def __init__(self) -> None:
        """
        Initialize pipeline object
        """

        self.bouts = []
        self.conn = sqlite3.connect(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "..",
                "..",
                "data",
                "fightmatrix.db",
            ),
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self.cur = self.conn.cursor()
        self.cur.execute(CREATE_FIGHTMATRIX_BOUTS_TABLE)

    def open_spider(self, spider):
        """
        Open the spider
        """

        assert spider.name == "fightmatrix_results_spider"
        self.scrape_type = spider.scrape_type

    def process_item(self, item, spider):
        """
        Process item objects
        """

        if isinstance(item, FightMatrixBoutItem):
            self.bouts.append(dict(item))

        return item

    def close_spider(self, spider):
        """
        Close the spider
        """

        bouts_df = pd.DataFrame(self.bouts).sort_values(
            by=["DATE", "EVENT_ID", "BOUT_ORDINAL"]
        )

        flag = True
        if self.scrape_type == "all":
            self.cur.execute(
                """
                DELETE FROM 
                  FIGHTMATRIX_BOUTS;
                """
            )
        else:
            most_recent_event_id = int(bouts_df["EVENT_ID"].iloc[0])
            res = self.cur.execute(
                """
                SELECT 
                  EVENT_ID 
                FROM 
                  FIGHTMATRIX_BOUTS 
                WHERE 
                  EVENT_ID = ?;
                """,
                (most_recent_event_id,),
            ).fetchall()
            flag = len(res) == 0

        if flag:
            bouts_df.to_sql(
                "FIGHTMATRIX_BOUTS",
                self.conn,
                if_exists="append",
                index=False,
            )

        self.conn.commit()
        self.conn.close()


class FightMatrixRankingsPipeline:
    """
    Item pipeline for FightMatrix rankings data
    """

    def __init__(self) -> None:
        """
        Initialize pipeline object
        """

        self.scrape_type = None

        self.rankings = []
        self.conn = sqlite3.connect(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "..",
                "..",
                "data",
                "fightmatrix.db",
            ),
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self.cur = self.conn.cursor()
        self.cur.execute(CREATE_FIGHTMATRIX_RANKINGS_TABLE)

    def open_spider(self, spider):
        """
        Open the spider
        """

        assert spider.name == "fightmatrix_rankings_spider"
        self.scrape_type = spider.scrape_type

    def process_item(self, item, spider):
        """
        Process item objects
        """

        if isinstance(item, FightMatrixRankingItem):
            self.rankings.append(dict(item))

        return item

    def close_spider(self, spider):
        """
        Close the spider
        """

        rankings_df = (
            pd.DataFrame(self.rankings)
            .drop_duplicates()
            .sort_values(by=["ISSUE_DATE", "WEIGHT_CLASS", "RANK"])
        )
        fighters_df = pd.read_sql(
            """
            SELECT
              FIGHTER_ID,
              UFC_DEBUT_DATE
            FROM
              FIGHTMATRIX_FIGHTERS;
            """,
            self.conn,
        )

        flag = True
        if self.scrape_type == "all":
            self.cur.execute(
                """
                DELETE FROM 
                  FIGHTMATRIX_RANKINGS;
                """
            )
        elif self.scrape_type == "most_recent":
            most_recent_issue_date = rankings_df["ISSUE_DATE"].iloc[0]
            res = self.cur.execute(
                """
                SELECT 
                  ISSUE_DATE 
                FROM 
                  FIGHTMATRIX_RANKINGS 
                WHERE 
                  ISSUE_DATE = ?;
                """,
                (most_recent_issue_date,),
            ).fetchall()
            flag = len(res) == 0

        if flag:
            rankings_df = rankings_df.merge(
                fighters_df,
                how="inner",
                on="FIGHTER_ID",
            )

            rankings_df_filtered = rankings_df.loc[
                pd.to_datetime(rankings_df["ISSUE_DATE"])
                >= pd.to_datetime(rankings_df["UFC_DEBUT_DATE"])
            ]
            rankings_df_filtered = rankings_df_filtered.drop(columns=["UFC_DEBUT_DATE"])

            rankings_df_filtered.to_sql(
                "FIGHTMATRIX_RANKINGS",
                self.conn,
                if_exists="append",
                index=False,
            )

        self.conn.commit()
        self.conn.close()
