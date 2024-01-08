# standard library imports
import os
import sqlite3

# third party imports
import pandas as pd

# local imports
from src.databases.create_statements import CREATE_FIGHTER_LINKAGE_TABLE


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

        assert matching_type in ["all", "new"]
        self.matching_type = matching_type
        self.conn = sqlite3.connect(
            os.path.join(os.path.dirname(__file__), "..", "..", "data", "ufc.db"),
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self.cur = self.conn.cursor()
        self.cur.execute(CREATE_FIGHTER_LINKAGE_TABLE)

    def __call__(self) -> None:
        """
        Run fighter matching algorithm
        """

        if self.matching_type == "all":
            self.cur.execute("DELETE FROM FIGHTER_LINKAGE")

        self.conn.commit()
        self.conn.close()
