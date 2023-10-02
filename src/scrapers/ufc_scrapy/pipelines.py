"""
This module contains the item pipelines for the various scrapers
"""

# standard library imports

# third party imports
import pandas as pd

# local imports
from src.databases.supabase_facade import SupabaseFacade
from src.scrapers.ufc_scrapy.items import (
    TapologyBoutItem,
    UFCRankingsItem,
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
        self.supabase_facade = SupabaseFacade()
        self.rows = []  # for bulk insert

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

        if self.rows:
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

            # Upsert into database
            self.supabase_facade.bulk_upsert(
                "UFCSTATS_FIGHTERS", fighters_df, "FIGHTER_ID"
            )


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
        self.supabase_facade = SupabaseFacade()

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

        if self.rows_overall:
            bouts_overall_df = pd.DataFrame(self.rows_overall)
            bouts_overall_df = bouts_overall_df.sort_values(
                by=["DATE", "EVENT_ID", "BOUT_ORDINAL"]
            )
            bouts_overall_df = bouts_overall_df.drop(columns=["BOUT_ORDINAL"])

            # Upsert into database
            self.supabase_facade.bulk_upsert(
                "UFCSTATS_BOUTS_OVERALL", bouts_overall_df, "BOUT_ID"
            )

        if self.rows_by_round:
            bouts_by_round_df = pd.DataFrame(self.rows_by_round)
            bouts_by_round_df = bouts_by_round_df.sort_values(
                by=["DATE", "EVENT_ID", "BOUT_ORDINAL", "ROUND"]
            )
            bouts_by_round_df = bouts_by_round_df.drop(
                columns=["DATE", "EVENT_ID", "BOUT_ORDINAL"]
            )

            # Upsert into database
            self.supabase_facade.bulk_upsert(
                "UFCSTATS_BOUTS_BY_ROUND", bouts_by_round_df, "BOUT_ROUND_ID"
            )


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
        self.supabase_facade = SupabaseFacade()

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

        if self.rows:
            bouts_df = pd.DataFrame(self.rows)
            bouts_df = bouts_df.sort_values(by=["DATE", "EVENT_ID", "BOUT_ORDINAL"])
            bouts_df = bouts_df.drop(columns=["BOUT_ORDINAL"])

            # Upsert into database
            self.supabase_facade.bulk_upsert("TAPOLOGY_BOUTS", bouts_df, "BOUT_ID")


class UFCRankingsPipeline:
    """
    Item pipeline for UFC rankings data
    """

    def __init__(self) -> None:
        """
        Initialize the pipeline class
        """

        self.rows = []
        self.supabase_facade = SupabaseFacade()

    def open_spider(self, spider):
        """
        Open the spider
        """

        assert spider.name == "ufc_rankings_spider"

    def process_item(self, item, spider):
        """
        Process UFCRankingsItem objects
        """

        if isinstance(item, UFCRankingsItem):
            self.rows.append(item)

        return item

    def close_spider(self, spider):
        """
        Inserts the scraped data into the database and closes the spider
        """

        if self.rows:
            rankings_df = pd.DataFrame(self.rows)
            scrape_date = rankings_df["scrape_date"].unique().tolist()
            assert len(scrape_date) == 1
            scrape_date = scrape_date[0]

            # Check if latest rankings are already in the database
            # We do this to avoid duplicates because primary key is a sequence
            matches = (
                self.supabase_facade.client.table("UFC_RANKINGS")
                .select("*")
                .eq("DATE", scrape_date)
                .execute()
            )

            if not matches.data:
                self.supabase_facade.bulk_insert("UFC_RANKINGS", rankings_df)


class UFCStatsUpcomingEventPipeline:
    """
    Item pipeline for upcoming event data from UFCStats
    """


class TapologyUpcomingEventPipeline:
    """
    Item pipeline for upcoming event data from Tapology
    """
