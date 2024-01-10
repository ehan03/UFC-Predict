# standard library imports
import os
import sqlite3

# third party imports
import pandas as pd
from thefuzz import process

# local imports
from src.databases.create_statements import CREATE_FIGHTER_LINKAGE_TABLE
from src.databases.matcher_queries import (
    CLEAN_UP_QUERY_COMPLETED_BOUTS,
    CLEAN_UP_QUERY_UPCOMING_BOUTS,
    MATCHING_QUERY_COMPLETED_BOUTS_LOOSE,
    MATCHING_QUERY_COMPLETED_BOUTS_STRICT,
    MATCHING_QUERY_UPCOMING_BOUTS,
    PRELIMINARY_WIDE_MATCHING_QUERY,
    UNKNOWN_FIGHTODDSIO_COMPLETED_BOUTS,
    UNKNOWN_FIGHTODDSIO_UPCOMING_BOUTS,
    UNKNOWN_UFCSTATS_COMPLETED_BOUTS,
    UNKNOWN_UFCSTATS_UPCOMING_BOUTS,
)


class FighterMatcher:
    """
    Class for matching fighters between UFC Stats and FightOdds.io.
    This is necessary since the two sources use different names for the same
    fighter and have missing or conflicting data fields, making the process
    less straightforward than one may think.
    """

    def __init__(self, matching_type: str) -> None:
        """
        Initialize FighterMatcher class
        """

        assert matching_type in ["reset_all", "completed", "upcoming"]
        self.matching_type = matching_type
        self.conn = sqlite3.connect(
            os.path.join(os.path.dirname(__file__), "..", "..", "data", "ufc.db"),
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self.cur = self.conn.cursor()
        self.cur.execute(CREATE_FIGHTER_LINKAGE_TABLE)

    def match_for_upcoming_bouts(self) -> None:
        """
        Match debuting fighters in upcoming bouts
        """

        match_upcoming_df = pd.read_sql(
            MATCHING_QUERY_UPCOMING_BOUTS, self.conn
        ).drop_duplicates()
        match_upcoming_df.to_sql(
            "FIGHTER_LINKAGE", self.conn, if_exists="append", index=False
        )
        match_clean_up_df = pd.read_sql(CLEAN_UP_QUERY_UPCOMING_BOUTS, self.conn)
        match_clean_up_df.to_sql(
            "FIGHTER_LINKAGE", self.conn, if_exists="append", index=False
        )

        unknown_ufcstats = pd.read_sql(UNKNOWN_UFCSTATS_UPCOMING_BOUTS, self.conn)
        if unknown_ufcstats.shape[0]:
            unknown_fightoddsio = pd.read_sql(
                UNKNOWN_FIGHTODDSIO_UPCOMING_BOUTS, self.conn
            )
            assert unknown_ufcstats.shape[0] == unknown_fightoddsio.shape[0]

            unknown_ufcstats[
                "FIGHTER_NAME_CLOSE"
            ] = unknown_ufcstats.FIGHTER_NAME.copy().apply(
                lambda x: process.extractOne(
                    x, unknown_fightoddsio.FIGHTER_NAME.copy()
                )[0]
            )
            fuzzy_match_df = unknown_ufcstats.merge(
                unknown_fightoddsio,
                how="inner",
                left_on="FIGHTER_NAME_CLOSE",
                right_on="FIGHTER_NAME",
            )[["UFCSTATS_FIGHTER_ID", "FIGHTODDSIO_FIGHTER_SLUG"]]
            fuzzy_match_df.to_sql(
                "FIGHTER_LINKAGE", self.conn, if_exists="append", index=False
            )

    def match_for_completed_bouts(self) -> None:
        """
        Match unmatched fighters from historical bouts
        """

        match_strict_df = pd.read_sql(MATCHING_QUERY_COMPLETED_BOUTS_STRICT, self.conn)
        match_strict_df.to_sql(
            "FIGHTER_LINKAGE", self.conn, if_exists="append", index=False
        )  # the strict version is to safeguard against edge cases (for example the early tournament events)

        while True:
            match_loose_df = pd.read_sql(
                MATCHING_QUERY_COMPLETED_BOUTS_LOOSE, self.conn
            ).drop_duplicates()

            if match_loose_df.shape[0] == 0:
                break

            match_loose_df.to_sql(
                "FIGHTER_LINKAGE", self.conn, if_exists="append", index=False
            )
        match_clean_up_df = pd.read_sql(CLEAN_UP_QUERY_COMPLETED_BOUTS, self.conn)
        match_clean_up_df.to_sql(
            "FIGHTER_LINKAGE", self.conn, if_exists="append", index=False
        )

        unknown_ufcstats = pd.read_sql(UNKNOWN_UFCSTATS_COMPLETED_BOUTS, self.conn)
        if unknown_ufcstats.shape[0]:
            unknown_fightoddsio = pd.read_sql(
                UNKNOWN_FIGHTODDSIO_COMPLETED_BOUTS, self.conn
            )
            assert unknown_ufcstats.shape[0] == unknown_fightoddsio.shape[0]

            unknown_ufcstats[
                "FIGHTER_NAME_CLOSE"
            ] = unknown_ufcstats.FIGHTER_NAME.copy().apply(
                lambda x: process.extractOne(
                    x, unknown_fightoddsio.FIGHTER_NAME.copy()
                )[0]
            )
            fuzzy_match_df = unknown_ufcstats.merge(
                unknown_fightoddsio,
                how="inner",
                left_on="FIGHTER_NAME_CLOSE",
                right_on="FIGHTER_NAME",
            )[["UFCSTATS_FIGHTER_ID", "FIGHTODDSIO_FIGHTER_SLUG"]]
            fuzzy_match_df.to_sql(
                "FIGHTER_LINKAGE", self.conn, if_exists="append", index=False
            )

    def __call__(self) -> None:
        """
        Run fighter matching algorithm
        """

        if self.matching_type == "reset_all":
            self.cur.execute("DELETE FROM FIGHTER_LINKAGE")
            match_wide_df = pd.read_sql(PRELIMINARY_WIDE_MATCHING_QUERY, self.conn)
            match_wide_df.to_sql(
                "FIGHTER_LINKAGE", self.conn, if_exists="append", index=False
            )
            self.match_for_completed_bouts()
            self.match_for_upcoming_bouts()
        elif self.matching_type == "completed":
            self.match_for_completed_bouts()
        elif self.matching_type == "upcoming":
            self.match_for_upcoming_bouts()

        self.conn.commit()
        self.conn.close()
