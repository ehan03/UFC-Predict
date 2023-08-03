# standard library imports
import os
import sqlite3

# third party imports
import pandas as pd

# local imports
from src.scrapers.ufc_scrapy.items import BoutItem, FighterItem


class FightersSQLitePipeline:
    def open_spider(self, spider):
        self.rows = []
        self.conn = sqlite3.connect(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "ufc.db"),
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self.cur = self.conn.cursor()

        # Create FIGHTERS table
        self.cur.execute(
            """
            CREATE TABLE IF NOT EXISTS FIGHTERS (
                FIGHTER_ID TEXT PRIMARY KEY,
                FIGHTER_NAME TEXT,
                WINS INTEGER,
                LOSSES INTEGER,
                DRAWS INTEGER,
                NO_CONTESTS INTEGER,
                HEIGHT_INCHES REAL,
                REACH_INCHES REAL,
                FIGHTING_STANCE TEXT,
                DATE_OF_BIRTH DATE
            )
            """
        )

        # Truncate FIGHTERS table
        self.cur.execute("DELETE FROM FIGHTERS")
        self.conn.commit()

    def process_item(self, item, spider):
        if isinstance(item, FighterItem):
            self.rows.append(item)
        return item

    def close_spider(self, spider):
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

            # Insert into database
            fighters_df.to_sql("FIGHTERS", self.conn, if_exists="append", index=False)

        self.conn.commit()
        self.conn.close()


class BoutsSQLitePipeline:
    def open_spider(self, spider):
        self.rows = []
        self.conn = sqlite3.connect(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "ufc.db"),
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self.cur = self.conn.cursor()

        stats_base_names = [
            "KNOCKDOWNS",
            "TOTAL_STRIKES",
            "TAKEDOWNS",
            "SUBMISSION_ATTEMPTS",
            "REVERSALS",
            "CONTROL_TIME_MINUTES",
            "SIGNIFICANT_STRIKES",
            "SIGNIFICANT_STRIKES_HEAD",
            "SIGNIFICANT_STRIKES_BODY",
            "SIGNIFICANT_STRIKES_LEG",
            "SIGNIFICANT_STRIKES_DISTANCE",
            "SIGNIFICANT_STRIKES_CLINCH",
            "SIGNIFICANT_STRIKES_GROUND",
        ]

        overall_stats_names = []
        for stat in stats_base_names:
            for corner in ["RED", "BLUE"]:
                if stat == "CONTROL_TIME_MINUTES":
                    overall_stats_names.append(f"{corner}_{stat} REAL")
                elif stat in {
                    "KNOCKDOWNS",
                    "SUBMISSION_ATTEMPTS",
                    "REVERSALS",
                }:
                    overall_stats_names.append(f"{corner}_{stat} INTEGER")
                else:
                    for type in ["LANDED", "ATTEMPTED"]:
                        overall_stats_names.append(f"{corner}_{stat}_{type} INTEGER")

        round_by_round_stats_names = []
        for round in range(1, 6):
            for stat in stats_base_names:
                for corner in ["RED", "BLUE"]:
                    if stat == "CONTROL_TIME_MINUTES":
                        round_by_round_stats_names.append(
                            f"{corner}_{stat}_ROUND_{round} REAL"
                        )
                    elif stat in {
                        "KNOCKDOWNS",
                        "SUBMISSION_ATTEMPTS",
                        "REVERSALS",
                    }:
                        round_by_round_stats_names.append(
                            f"{corner}_{stat}_ROUND_{round} INTEGER"
                        )
                    else:
                        for type in ["LANDED", "ATTEMPTED"]:
                            round_by_round_stats_names.append(
                                f"{corner}_{stat}_{type}_ROUND_{round} INTEGER"
                            )

        # Create BOUTS_OVERALL table
        self.cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS BOUTS_OVERALL (
                BOUT_ID TEXT PRIMARY KEY,
                EVENT_ID TEXT,
                EVENT_NAME TEXT,
                DATE DATE,
                LOCATION TEXT,
                RED_FIGHTER_ID TEXT,
                BLUE_FIGHTER_ID TEXT,
                RED_FIGHTER_NAME TEXT,
                BLUE_FIGHTER_NAME TEXT,
                RED_OUTCOME TEXT,
                BLUE_OUTCOME TEXT,
                BOUT_TYPE TEXT,
                OUTCOME_METHOD TEXT,
                OUTCOME_METHOD_DETAILS TEXT,
                END_ROUND INTEGER,
                END_ROUND_TIME_MINUTES REAL,
                BOUT_TIME_FORMAT TEXT,
                TOTAL_TIME_MINUTES REAL,
                {", ".join(overall_stats_names)}
            )
            """
        )

        # Create BOUTS_BY_ROUND table
        self.cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS BOUTS_BY_ROUND (
                BOUT_ID TEXT PRIMARY KEY,
                {", ".join(round_by_round_stats_names)}
            )
            """
        )

        # Truncate tables
        self.cur.execute("DELETE FROM BOUTS_OVERALL")
        self.cur.execute("DELETE FROM BOUTS_BY_ROUND")
        self.conn.commit()

    def process_item(self, item, spider):
        if isinstance(item, BoutItem):
            self.rows.append(item)
        return item

    def close_spider(self, spider):
        if self.rows:
            bouts_df = pd.DataFrame(self.rows)

            # Sort by date and bout ordinal within each event
            bouts_df = bouts_df.sort_values(by=["DATE", "EVENT_NAME", "BOUT_ORDINAL"])
            bouts_df = bouts_df.drop(columns=["BOUT_ORDINAL"])

            # Split into different tables/views
            round_suffixes = [f"_ROUND_{i}" for i in range(1, 6)]
            by_round_columns = [
                col
                for col in bouts_df.columns
                if any([col.endswith(suffix) for suffix in round_suffixes])
            ]
            bouts_overall_df = bouts_df.drop(columns=by_round_columns)
            bouts_by_round_df = bouts_df[["BOUT_ID"] + by_round_columns]

            # Insert into database
            bouts_overall_df.to_sql(
                "BOUTS_OVERALL", self.conn, if_exists="append", index=False
            )
            bouts_by_round_df.to_sql(
                "BOUTS_BY_ROUND", self.conn, if_exists="append", index=False
            )

        self.conn.commit()
        self.conn.close()
