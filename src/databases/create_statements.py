# standard library imports

# third party imports

# local imports


# All UFC Stats tables
CREATE_UFCSTATS_FIGHTERS_TABLE = """
    CREATE TABLE IF NOT EXISTS UFCSTATS_FIGHTERS (
        FIGHTER_ID TEXT PRIMARY KEY,
        FIGHTER_NAME TEXT,
        FIGHTER_NICKNAME TEXT,
        HEIGHT_INCHES INTEGER,
        REACH_INCHES INTEGER,
        STANCE TEXT,
        DATE_OF_BIRTH DATE
    );
"""

CREATE_UFCSTATS_BOUTS_OVERALL_TABLE = """
    CREATE TABLE IF NOT EXISTS UFCSTATS_BOUTS_OVERALL (
        BOUT_ID TEXT PRIMARY KEY,
        EVENT_ID TEXT NOT NULL,
        EVENT_NAME TEXT,
        DATE DATE,
        LOCATION TEXT,
        BOUT_ORDINAL INTEGER,
        RED_FIGHTER_ID TEXT NOT NULL,
        BLUE_FIGHTER_ID TEXT NOT NULL,
        RED_OUTCOME TEXT,
        BLUE_OUTCOME TEXT,
        WEIGHT_CLASS TEXT,
        BOUT_LONGNAME TEXT,
        BOUT_PERF_BONUS INTEGER,
        OUTCOME_METHOD TEXT,
        OUTCOME_METHOD_DETAILS TEXT,
        END_ROUND INTEGER,
        END_ROUND_TIME_SECONDS INTEGER,
        BOUT_TIME_FORMAT TEXT,
        TOTAL_TIME_SECONDS INTEGER
    );
"""

CREATE_UFCSTATS_BOUTS_BY_ROUND_TABLE = """
    CREATE TABLE IF NOT EXISTS UFCSTATS_BOUTS_BY_ROUND (
        BOUT_ID TEXT NOT NULL,
        ROUND INTEGER,
        TIME_FOUGHT_SECONDS INTEGER,
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
        RED_CONTROL_TIME_SECONDS INTEGER,
        BLUE_CONTROL_TIME_SECONDS INTEGER,
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

CREATE_UFCSTATS_UPCOMING_TABLE = """
    CREATE TABLE IF NOT EXISTS UFCSTATS_UPCOMING (
        BOUT_ID TEXT PRIMARY KEY,
        EVENT_ID TEXT NOT NULL,
        EVENT_NAME TEXT,
        DATE DATE,
        LOCATION TEXT,
        BOUT_ORDINAL INTEGER,
        RED_FIGHTER_ID TEXT NOT NULL,
        BLUE_FIGHTER_ID TEXT NOT NULL,
        WEIGHT_CLASS TEXT,
        BOUT_LONGNAME TEXT
    );
"""

CREATE_BESTFIGHTODDS_HISTORICAL_ODDS_TABLE = """
    CREATE TABLE IF NOT EXISTS BESTFIGHTODDS_HISTORICAL_ODDS (
        UFCSTATS_BOUT_ID TEXT PRIMARY KEY,
        RED_FIGHTER_ODDS REAL,
        BLUE_FIGHTER_ODDS REAL
    );
"""

CREATE_LOCATION_ELEVATIONS_TABLE = """
    CREATE TABLE IF NOT EXISTS LOCATION_ELEVATIONS (
        LOCATION TEXT PRIMARY KEY,
        LATITUDE REAL,
        LONGITUDE REAL,
        ELEVATION_METERS INTEGER
    );
"""


# All FightOddsIO tables
CREATE_FIGHTODDSIO_FIGHTERS_TABLE = """
    CREATE TABLE IF NOT EXISTS FIGHTODDSIO_FIGHTERS (
        FIGHTER_ID INTEGER PRIMARY KEY,
        FIGHTER_NAME TEXT,
        FIGHTER_NICKNAME TEXT,
        HEIGHT_CENTIMETERS REAL,
        REACH_INCHES REAL,
        LEG_REACH_INCHES REAL,
        FIGHTING_STYLE TEXT,
        STANCE TEXT,
        DATE_OF_BIRTH DATE
    );
"""

CREATE_FIGHTODDSIO_BOUTS_TABLE = """
    CREATE TABLE IF NOT EXISTS FIGHTODDSIO_BOUTS (
        BOUT_SLUG TEXT PRIMARY KEY,
        EVENT_SLUG TEXT NOT NULL,
        EVENT_NAME TEXT,
        DATE DATE,
        LOCATION TEXT,
        VENUE TEXT,
        BOUT_ORDINAL INTEGER,
        BOUT_CARD_TYPE TEXT,
        WEIGHT_CLASS TEXT,
        WEIGHT INTEGER,
        FIGHTER_1_ID INTEGER NOT NULL,
        FIGHTER_2_ID INTEGER NOT NULL,
        WINNER_ID INTEGER,
        OUTCOME_METHOD_1 TEXT,
        OUTCOME_METHOD_2 TEXT,
        END_ROUND INTEGER,
        END_ROUND_TIME_SECONDS INTEGER,
        FIGHTER_1_ODDS REAL,
        FIGHTER_2_ODDS REAL
    );
"""

CREATE_FIGHTODDSIO_UPCOMING_TABLE = """
    CREATE TABLE IF NOT EXISTS FIGHTODDSIO_UPCOMING (
        BOUT_SLUG TEXT PRIMARY KEY,
        EVENT_SLUG TEXT NOT NULL,
        EVENT_NAME TEXT,
        DATE DATE,
        LOCATION TEXT,
        VENUE TEXT,
        FIGHTER_1_ID INTEGER NOT NULL,
        FIGHTER_2_ID INTEGER NOT NULL,
        FIGHTER_1_ODDS_DRAFTKINGS INTEGER,
        FIGHTER_2_ODDS_DRAFTKINGS INTEGER
    );
"""

CREATE_FIGHTODDSIO_FIGHTER_LINKAGE_TABLE = """
    CREATE TABLE IF NOT EXISTS FIGHTODDSIO_FIGHTER_LINKAGE (
        UFCSTATS_FIGHTER_ID TEXT PRIMARY KEY,
        FIGHTODDSIO_FIGHTER_ID INTEGER NOT NULL,
        CONSTRAINT FIGHTODDSIO_FIGHTER_SLUG_UNIQUE UNIQUE (FIGHTODDSIO_FIGHTER_ID)
    );
"""


# All Sherdog tables
CREATE_SHERDOG_FIGHTERS_TABLE = """
    CREATE TABLE IF NOT EXISTS SHERDOG_FIGHTERS (
        FIGHTER_ID INTEGER PRIMARY KEY,
        FIGHTER_NAME TEXT,
        FIGHTER_NICKNAME TEXT,
        HEIGHT_INCHES INTEGER,
        DATE_OF_BIRTH DATE,
        NATIONALITY TEXT,
        PRO_DEBUT_DATE DATE
    );
"""

CREATE_SHERDOG_BOUTS_TABLE = """
    CREATE TABLE IF NOT EXISTS SHERDOG_BOUTS (
        EVENT_ID INTEGER NOT NULL,
        EVENT_NAME TEXT,
        DATE DATE,
        LOCATION TEXT,
        VENUE TEXT,
        BOUT_ORDINAL INTEGER,
        FIGHTER_1_ID INTEGER,
        FIGHTER_2_ID INTEGER,
        FIGHTER_1_OUTCOME TEXT,
        FIGHTER_2_OUTCOME TEXT,
        WEIGHT_CLASS TEXT,
        WEIGHT INTEGER,
        OUTCOME_METHOD TEXT,
        OUTCOME_METHOD_DETAILS TEXT,
        END_ROUND INTEGER,
        END_ROUND_TIME_SECONDS INTEGER,
        TOTAL_TIME_SECONDS INTEGER
    );
"""

CREATE_SHERDOG_BOUT_HISTORY_TABLE = """
    CREATE TABLE IF NOT EXISTS SHERDOG_BOUT_HISTORY (
        FIGHTER_ID INTEGER NOT NULL,
        FIGHTER_BOUT_ORDINAL INTEGER,
        EVENT_ID INTEGER NOT NULL,
        EVENT_NAME TEXT NOT NULL,
        DATE DATE,
        OPPONENT_ID INTEGER,
        OPPONENT_NAME TEXT,
        OUTCOME TEXT,
        OUTCOME_METHOD TEXT,
        OUTCOME_METHOD_DETAILS TEXT,
        END_ROUND INTEGER,
        END_ROUND_TIME_SECONDS INTEGER,
        TOTAL_TIME_SECONDS INTEGER
    );
"""

CREATE_SHERDOG_FIGHTER_LINKAGE_TABLE = """
    CREATE TABLE IF NOT EXISTS SHERDOG_FIGHTER_LINKAGE (
        UFCSTATS_FIGHTER_ID TEXT PRIMARY KEY,
        SHERDOG_FIGHTER_ID INTEGER NOT NULL,
        CONSTRAINT SHERDOG_FIGHTER_ID_UNIQUE UNIQUE (SHERDOG_FIGHTER_ID)
    );
"""


# All FightMatrix tables
CREATE_FIGHTMATRIX_FIGHTERS_TABLE = """
    CREATE TABLE IF NOT EXISTS FIGHTMATRIX_FIGHTERS (
        FIGHTER_ID INTEGER PRIMARY KEY,
        SHERDOG_FIGHTER_ID INTEGER NOT NULL,
        FIGHTER_NAME TEXT,
        PRO_DEBUT_DATE DATE,
        UFC_DEBUT_DATE DATE
    );
"""

CREATE_FIGHTMATRIX_BOUTS_TABLE = """
    CREATE TABLE IF NOT EXISTS FIGHTMATRIX_BOUTS (
        EVENT_ID INTEGER NOT NULL,
        EVENT_NAME TEXT,
        DATE DATE,
        BOUT_ORDINAL INTEGER,
        FIGHTER_1_ID INTEGER NOT NULL,
        FIGHTER_2_ID INTEGER NOT NULL,
        FIGHTER_1_OUTCOME TEXT,
        FIGHTER_2_OUTCOME TEXT,
        FIGHTER_1_ELO_K170_PRE INTEGER,
        FIGHTER_1_ELO_K170_POST INTEGER,
        FIGHTER_2_ELO_K170_PRE INTEGER,
        FIGHTER_2_ELO_K170_POST INTEGER,
        FIGHTER_1_ELO_MODIFIED_PRE INTEGER,
        FIGHTER_1_ELO_MODIFIED_POST INTEGER,
        FIGHTER_2_ELO_MODIFIED_PRE INTEGER,
        FIGHTER_2_ELO_MODIFIED_POST INTEGER,
        FIGHTER_1_GLICKO1_PRE INTEGER,
        FIGHTER_1_GLICKO1_POST INTEGER,
        FIGHTER_2_GLICKO1_PRE INTEGER,
        FIGHTER_2_GLICKO1_POST INTEGER,
        WEIGHT_CLASS TEXT,
        OUTCOME_METHOD TEXT,
        OUTCOME_METHOD_DETAILS TEXT,
        END_ROUND INTEGER
    )
"""

CREATE_FIGHTMATRIX_RANKINGS_TABLE = """
    CREATE TABLE IF NOT EXISTS FIGHTMATRIX_RANKINGS (
        ISSUE_DATE DATE NOT NULL,
        WEIGHT_CLASS TEXT,
        FIGHTER_ID INTEGER NOT NULL,
        RANK INTEGER,
        POINTS INTEGER
    );
"""
