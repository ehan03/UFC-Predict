"""
This module contains the create statements for the database tables.
"""

CREATE_UFCSTATS_FIGHTERS_TABLE = """
                                CREATE TABLE IF NOT EXISTS UFCSTATS_FIGHTERS (
                                    FIGHTER_ID TEXT PRIMARY KEY,
                                    FIGHTER_NAME TEXT,
                                    HEIGHT_INCHES REAL,
                                    REACH_INCHES REAL,
                                    FIGHTING_STANCE TEXT,
                                    DATE_OF_BIRTH DATE
                                );
                                """

CREATE_UFCSTATS_BOUTS_OVERALL_TABLE = """
                                CREATE TABLE IF NOT EXISTS UFCSTATS_BOUTS_OVERALL (
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
                                    RED_KNOCKDOWNS INTEGER,
                                    BLUE_KNOCKDOWNS INTEGER,
                                    RED_TOTAL_STRIKES_LANDED INTEGER,
                                    RED_TOTAL_STRIKES_ATTEMPTED INTEGER,
                                    BLUE_TOTAL_STRIKES_LANDED INTEGER,
                                    BLUE_TOTAL_STRIKES_ATTEMPTED INTEGER,
                                    RED_TAKEDOWNS_LANDED INTEGER,
                                    RED_TAKEDOWNS_ATTEMPTED INTEGER,
                                    BLUE_TAKEDOWNS_LANDED INTEGER,
                                    BLUE_TAKEDOWNS_ATTEMPTED INTEGER,
                                    RED_SUBMISSION_ATTEMPTS INTEGER,
                                    BLUE_SUBMISSION_ATTEMPTS INTEGER,
                                    RED_REVERSALS INTEGER,
                                    BLUE_REVERSALS INTEGER,
                                    RED_CONTROL_TIME_MINUTES REAL,
                                    BLUE_CONTROL_TIME_MINUTES REAL,
                                    RED_SIGNIFICANT_STRIKES_LANDED INTEGER,
                                    RED_SIGNIFICANT_STRIKES_ATTEMPTED INTEGER,
                                    BLUE_SIGNIFICANT_STRIKES_LANDED INTEGER,
                                    BLUE_SIGNIFICANT_STRIKES_ATTEMPTED INTEGER,
                                    RED_SIGNIFICANT_STRIKES_HEAD_LANDED INTEGER,
                                    RED_SIGNIFICANT_STRIKES_HEAD_ATTEMPTED INTEGER,
                                    BLUE_SIGNIFICANT_STRIKES_HEAD_LANDED INTEGER,
                                    BLUE_SIGNIFICANT_STRIKES_HEAD_ATTEMPTED INTEGER,
                                    RED_SIGNIFICANT_STRIKES_BODY_LANDED INTEGER,
                                    RED_SIGNIFICANT_STRIKES_BODY_ATTEMPTED INTEGER,
                                    BLUE_SIGNIFICANT_STRIKES_BODY_LANDED INTEGER,
                                    BLUE_SIGNIFICANT_STRIKES_BODY_ATTEMPTED INTEGER,
                                    RED_SIGNIFICANT_STRIKES_LEG_LANDED INTEGER,
                                    RED_SIGNIFICANT_STRIKES_LEG_ATTEMPTED INTEGER,
                                    BLUE_SIGNIFICANT_STRIKES_LEG_LANDED INTEGER,
                                    BLUE_SIGNIFICANT_STRIKES_LEG_ATTEMPTED INTEGER,
                                    RED_SIGNIFICANT_STRIKES_DISTANCE_LANDED INTEGER,
                                    RED_SIGNIFICANT_STRIKES_DISTANCE_ATTEMPTED INTEGER,
                                    BLUE_SIGNIFICANT_STRIKES_DISTANCE_LANDED INTEGER,
                                    BLUE_SIGNIFICANT_STRIKES_DISTANCE_ATTEMPTED INTEGER,
                                    RED_SIGNIFICANT_STRIKES_CLINCH_LANDED INTEGER,
                                    RED_SIGNIFICANT_STRIKES_CLINCH_ATTEMPTED INTEGER,
                                    BLUE_SIGNIFICANT_STRIKES_CLINCH_LANDED INTEGER,
                                    BLUE_SIGNIFICANT_STRIKES_CLINCH_ATTEMPTED INTEGER,
                                    RED_SIGNIFICANT_STRIKES_GROUND_LANDED INTEGER,
                                    RED_SIGNIFICANT_STRIKES_GROUND_ATTEMPTED INTEGER,
                                    BLUE_SIGNIFICANT_STRIKES_GROUND_LANDED INTEGER,
                                    BLUE_SIGNIFICANT_STRIKES_GROUND_ATTEMPTED INTEGER
                                );
                                """

CREATE_UFCSTATS_BOUTS_BY_ROUND_TABLE = """
                                CREATE TABLE IF NOT EXISTS UFCSTATS_BOUTS_BY_ROUND (
                                    BOUT_ID TEXT,
                                    ROUND INTEGER,
                                    RED_KNOCKDOWNS INTEGER,
                                    BLUE_KNOCKDOWNS INTEGER,
                                    RED_TOTAL_STRIKES_LANDED INTEGER,
                                    RED_TOTAL_STRIKES_ATTEMPTED INTEGER,
                                    BLUE_TOTAL_STRIKES_LANDED INTEGER,
                                    BLUE_TOTAL_STRIKES_ATTEMPTED INTEGER,
                                    RED_TAKEDOWNS_LANDED INTEGER,
                                    RED_TAKEDOWNS_ATTEMPTED INTEGER,
                                    BLUE_TAKEDOWNS_LANDED INTEGER,
                                    BLUE_TAKEDOWNS_ATTEMPTED INTEGER,
                                    RED_SUBMISSION_ATTEMPTS INTEGER,
                                    BLUE_SUBMISSION_ATTEMPTS INTEGER,
                                    RED_REVERSALS INTEGER,
                                    BLUE_REVERSALS INTEGER,
                                    RED_CONTROL_TIME_MINUTES REAL,
                                    BLUE_CONTROL_TIME_MINUTES REAL,
                                    RED_SIGNIFICANT_STRIKES_LANDED INTEGER,
                                    RED_SIGNIFICANT_STRIKES_ATTEMPTED INTEGER,
                                    BLUE_SIGNIFICANT_STRIKES_LANDED INTEGER,
                                    BLUE_SIGNIFICANT_STRIKES_ATTEMPTED INTEGER,
                                    RED_SIGNIFICANT_STRIKES_HEAD_LANDED INTEGER,
                                    RED_SIGNIFICANT_STRIKES_HEAD_ATTEMPTED INTEGER,
                                    BLUE_SIGNIFICANT_STRIKES_HEAD_LANDED INTEGER,
                                    BLUE_SIGNIFICANT_STRIKES_HEAD_ATTEMPTED INTEGER,
                                    RED_SIGNIFICANT_STRIKES_BODY_LANDED INTEGER,
                                    RED_SIGNIFICANT_STRIKES_BODY_ATTEMPTED INTEGER,
                                    BLUE_SIGNIFICANT_STRIKES_BODY_LANDED INTEGER,
                                    BLUE_SIGNIFICANT_STRIKES_BODY_ATTEMPTED INTEGER,
                                    RED_SIGNIFICANT_STRIKES_LEG_LANDED INTEGER,
                                    RED_SIGNIFICANT_STRIKES_LEG_ATTEMPTED INTEGER,
                                    BLUE_SIGNIFICANT_STRIKES_LEG_LANDED INTEGER,
                                    BLUE_SIGNIFICANT_STRIKES_LEG_ATTEMPTED INTEGER,
                                    RED_SIGNIFICANT_STRIKES_DISTANCE_LANDED INTEGER,
                                    RED_SIGNIFICANT_STRIKES_DISTANCE_ATTEMPTED INTEGER,
                                    BLUE_SIGNIFICANT_STRIKES_DISTANCE_LANDED INTEGER,
                                    BLUE_SIGNIFICANT_STRIKES_DISTANCE_ATTEMPTED INTEGER,
                                    RED_SIGNIFICANT_STRIKES_CLINCH_LANDED INTEGER,
                                    RED_SIGNIFICANT_STRIKES_CLINCH_ATTEMPTED INTEGER,
                                    BLUE_SIGNIFICANT_STRIKES_CLINCH_LANDED INTEGER,
                                    BLUE_SIGNIFICANT_STRIKES_CLINCH_ATTEMPTED INTEGER,
                                    RED_SIGNIFICANT_STRIKES_GROUND_LANDED INTEGER,
                                    RED_SIGNIFICANT_STRIKES_GROUND_ATTEMPTED INTEGER,
                                    BLUE_SIGNIFICANT_STRIKES_GROUND_LANDED INTEGER,
                                    BLUE_SIGNIFICANT_STRIKES_GROUND_ATTEMPTED INTEGER
                                );
                                """

CREATE_TAPOLOGY_BOUTS_TABLE = """
                                CREATE TABLE IF NOT EXISTS TAPOLOGY_BOUTS (
                                    BOUT_ID INTEGER PRIMARY KEY,
                                    EVENT_ID INTEGER,
                                    EVENT_NAME TEXT,
                                    DATE DATE,
                                    REGION TEXT,
                                    LOCATION TEXT,
                                    VENUE TEXT,
                                    BOUT_CARD_TYPE TEXT,
                                    FIGHTER_1_ID TEXT,
                                    FIGHTER_2_ID TEXT,
                                    FIGHTER_1_NAME TEXT,
                                    FIGHTER_2_NAME TEXT,
                                    FIGHTER_1_RECORD_AT_BOUT TEXT,
                                    FIGHTER_2_RECORD_AT_BOUT TEXT,
                                    FIGHTER_1_NATIONALITY TEXT,
                                    FIGHTER_2_NATIONALITY TEXT,
                                    FIGHTER_1_HEIGHT_INCHES REAL,
                                    FIGHTER_2_HEIGHT_INCHES REAL,
                                    FIGHTER_1_REACH_INCHES REAL,
                                    FIGHTER_2_REACH_INCHES REAL,
                                    FIGHTER_1_GYM TEXT,
                                    FIGHTER_2_GYM TEXT
                                );
                                """

create_statement_map = {
    "UFCSTATS_FIGHTERS": CREATE_UFCSTATS_FIGHTERS_TABLE,
    "UFCSTATS_BOUTS_OVERALL": CREATE_UFCSTATS_BOUTS_OVERALL_TABLE,
    "UFCSTATS_BOUTS_BY_ROUND": CREATE_UFCSTATS_BOUTS_BY_ROUND_TABLE,
    "TAPOLOGY_BOUTS": CREATE_TAPOLOGY_BOUTS_TABLE,
}


def get_create_statement(table_name: str) -> str:
    """
    Get the create statement for the specified table
    """

    return create_statement_map[table_name]
