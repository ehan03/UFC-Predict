"""
This module contains the item pipelines for the various scrapers
"""

# standard library imports

# third party imports
import pandas as pd

# local imports
from src.databases.sqlite_facade import SQLiteFacade
from src.scrapers.ufc_scrapy.items import (
    TapologyBoutItem,
    UFCStatsBoutOverallItem,
    UFCStatsBoutRoundItem,
    UFCStatsFighterItem,
)


class UFCStatsFightersPipeline:
    """
    Item pipeline for UFCStats fighter data
    """

    def __init__(self) -> None:
        """
        Initialize the pipeline class
        """

        self.scrape_type = None
        self.rows = []  # for bulk insert
        self.sqlite_facade = SQLiteFacade()

    def open_spider(self, spider):
        """
        Open the spider
        """

        assert spider.name == "ufcstats_spider"
        self.sqlite_facade.create_table("UFCSTATS_FIGHTERS")
        self.scrape_type = spider.scrape_type

    def process_item(self, item, spider):
        """
        Process UFCStatsFighterItem objects
        """

        if isinstance(item, UFCStatsFighterItem):
            if self.scrape_type == "all":
                self.rows.append(item)
            elif self.scrape_type == "most_recent":
                self.sqlite_facade.cur.execute(
                    """
                    INSERT INTO UFCSTATS_FIGHTERS (
                        FIGHTER_ID, 
                        FIGHTER_NAME, 
                        HEIGHT_INCHES, 
                        REACH_INCHES, 
                        FIGHTING_STANCE, 
                        DATE_OF_BIRTH
                    )
                        VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT (FIGHTER_ID) DO UPDATE SET
                            FIGHTER_NAME = excluded.FIGHTER_NAME,
                            HEIGHT_INCHES = excluded.HEIGHT_INCHES,
                            REACH_INCHES = excluded.REACH_INCHES,
                            FIGHTING_STANCE = excluded.FIGHTING_STANCE,
                            DATE_OF_BIRTH = excluded.DATE_OF_BIRTH;
                    """,
                    (
                        item["FIGHTER_ID"],
                        item["FIGHTER_NAME"],
                        item["HEIGHT_INCHES"],
                        item["REACH_INCHES"],
                        item["FIGHTING_STANCE"],
                        item["DATE_OF_BIRTH"],
                    ),
                )
                self.sqlite_facade.conn.commit()

        return item

    def close_spider(self, spider):
        """
        Inserts the scraped data into the database and closes the spider
        """

        if self.rows and self.scrape_type == "all":
            fighters_df = pd.DataFrame(self.rows)

            # Sort by name
            fighters_df["first name"] = fighters_df["FIGHTER_NAME"].apply(
                lambda x: x.split()[0]
            )
            fighters_df["last name"] = fighters_df["FIGHTER_NAME"].apply(
                lambda x: x.split()[-1]
            )
            fighters_df = fighters_df.sort_values(by=["last name", "first name"])
            fighters_df = fighters_df.drop(columns=["first name", "last name"])

            # Truncate table
            self.sqlite_facade.truncate_table("UFCSTATS_FIGHTERS")

            # Insert into database
            self.sqlite_facade.insert_into_table(fighters_df, "UFCSTATS_FIGHTERS")

        self.sqlite_facade.close_connection()


class UFCStatsBoutsOverallPipeline:
    """
    Item pipeline for UFCStats overall bout data
    """

    def __init__(self) -> None:
        """
        Initialize the pipeline class
        """

        self.scrape_type = None
        self.rows = []  # for bulk insert
        self.sqlite_facade = SQLiteFacade()

    def open_spider(self, spider):
        """
        Open the spider
        """

        assert spider.name == "ufcstats_spider"
        self.sqlite_facade.create_table("UFCSTATS_BOUTS_OVERALL")
        self.scrape_type = spider.scrape_type

    def process_item(self, item, spider):
        """
        Process UFCStatsBoutOverallItem objects
        """

        if isinstance(item, UFCStatsBoutOverallItem):
            self.rows.append(item)

        return item

    def close_spider(self, spider):
        """
        Inserts the scraped data into the database and closes the spider
        """

        if self.rows:
            bouts_overall_df = pd.DataFrame(self.rows)
            bouts_overall_df = bouts_overall_df.sort_values(
                by=["DATE", "EVENT_ID", "BOUT_ORDINAL"]
            )
            bouts_overall_df = bouts_overall_df.drop(columns=["BOUT_ORDINAL"])

            if self.scrape_type == "all":
                # Truncate table
                self.sqlite_facade.truncate_table("UFCSTATS_BOUTS_OVERALL")

                # Insert into database
                self.sqlite_facade.insert_into_table(
                    bouts_overall_df, "UFCSTATS_BOUTS_OVERALL"
                )
            elif self.scrape_type == "most_recent":
                # Check if the event already exists in the database
                assert len(bouts_overall_df["EVENT_ID"].unique()) == 1

                most_recent_event_id = bouts_overall_df["EVENT_ID"].unique()[0]
                temp = pd.read_sql_query(
                    """
                    SELECT
                        EVENT_ID
                    FROM
                        UFCSTATS_BOUTS_OVERALL
                    WHERE
                        EVENT_ID = (?);
                    """,
                    self.sqlite_facade.conn,
                    params=[most_recent_event_id],
                )

                if temp.empty:
                    # Insert into database
                    self.sqlite_facade.insert_into_table(
                        bouts_overall_df, "UFCSTATS_BOUTS_OVERALL"
                    )

        self.sqlite_facade.close_connection()


class UFCStatsBoutsByRoundPipeline:
    """
    Item pipeline for UFCStats bout data by round
    """

    def __init__(self) -> None:
        """
        Initialize the pipeline class
        """

        self.scrape_type = None
        self.rows = []  # for bulk insert
        self.sqlite_facade = SQLiteFacade()

    def open_spider(self, spider):
        """
        Open the spider
        """

        assert spider.name == "ufcstats_spider"
        self.sqlite_facade.create_table("UFCSTATS_BOUTS_BY_ROUND")
        self.scrape_type = spider.scrape_type

    def process_item(self, item, spider):
        """
        Process UFCStatsBoutRoundItem objects
        """

        if isinstance(item, UFCStatsBoutRoundItem):
            self.rows.append(item)

        return item

    def close_spider(self, spider):
        """
        Inserts the scraped data into the database and closes the spider
        """

        if self.rows:
            bouts_by_round_df = pd.DataFrame(self.rows)
            bouts_by_round_df = bouts_by_round_df.sort_values(
                by=["DATE", "EVENT_ID", "BOUT_ORDINAL", "ROUND"]
            )
            bouts_by_round_df = bouts_by_round_df.drop(
                columns=["DATE", "EVENT_ID", "BOUT_ORDINAL"]
            )

            if self.scrape_type == "all":
                # Truncate table
                self.sqlite_facade.truncate_table("UFCSTATS_BOUTS_BY_ROUND")

                # Insert into database
                self.sqlite_facade.insert_into_table(
                    bouts_by_round_df, "UFCSTATS_BOUTS_BY_ROUND"
                )
            elif self.scrape_type == "most_recent":
                # Check if bouts already exist in the database
                filler = ", ".join(
                    ["?" for _ in range(len(bouts_by_round_df["BOUT_ID"]))]
                )
                temp = pd.read_sql_query(
                    f"""
                    SELECT
                        BOUT_ID
                    FROM
                        UFCSTATS_BOUTS_BY_ROUND
                    WHERE
                        BOUT_ID IN ({filler});
                    """,
                    self.sqlite_facade.conn,
                    params=bouts_by_round_df["BOUT_ID"].tolist(),
                )

                if temp.empty:
                    # Insert into database
                    self.sqlite_facade.insert_into_table(
                        bouts_by_round_df, "UFCSTATS_BOUTS_BY_ROUND"
                    )

        self.sqlite_facade.close_connection()


class TapologyBoutsPipeline:
    """
    Item pipeline for Tapology bout data
    """

    def __init__(self) -> None:
        """
        Initialize the pipeline class
        """

        self.scrape_type = None
        self.rows = []  # for bulk insert
        self.sqlite_facade = SQLiteFacade()

    def open_spider(self, spider):
        """
        Open the spider
        """

        assert spider.name == "tapology_spider"
        self.sqlite_facade.create_table("TAPOLOGY_BOUTS")
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

        if self.rows:
            bouts_df = pd.DataFrame(self.rows)
            bouts_df = bouts_df.sort_values(by=["DATE", "EVENT_ID", "BOUT_ORDINAL"])
            bouts_df = bouts_df.drop(columns=["BOUT_ORDINAL"])

            if self.scrape_type == "most_recent":
                # Check if the event already exists in the database
                assert len(bouts_df["EVENT_ID"].unique()) == 1

                most_recent_event_id = bouts_df["EVENT_ID"].unique()[0]
                temp = pd.read_sql_query(
                    """
                    SELECT
                        EVENT_ID
                    FROM
                        TAPOLOGY_BOUTS
                    WHERE
                        EVENT_ID = (?);
                    """,
                    self.sqlite_facade.conn,
                    params=[most_recent_event_id],
                )

                if temp.empty:
                    # Insert into database
                    self.sqlite_facade.insert_into_table(bouts_df, "TAPOLOGY_BOUTS")
            else:
                # Insert into database
                self.sqlite_facade.insert_into_table(bouts_df, "TAPOLOGY_BOUTS")

        self.sqlite_facade.close_connection()


class UFCRankingsPipeline:
    """
    Item pipeline for UFC rankings data
    """


class UFCStatsUpcomingEventPipeline:
    """
    Item pipeline for upcoming event data from UFCStats
    """
