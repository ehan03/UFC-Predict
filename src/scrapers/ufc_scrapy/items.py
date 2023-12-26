# standard library imports

# local imports

# third party imports
from scrapy import Field, Item


class UFCStatsFighterItem(Item):
    """
    Item class for fighter data from UFCStats
    """

    FIGHTER_ID = Field()
    FIGHTER_NAME = Field()
    HEIGHT_INCHES = Field()
    REACH_INCHES = Field()
    FIGHTING_STANCE = Field()
    DATE_OF_BIRTH = Field()


class UFCStatsBoutOverallItem(Item):
    """
    Item class for overall bout data from UFCStats
    """

    BOUT_ID = Field()

    # Info from event page
    EVENT_ID = Field()
    EVENT_NAME = Field()
    DATE = Field()
    LOCATION = Field()
    BOUT_ORDINAL = Field()

    # Info from bout page
    RED_FIGHTER_ID = Field()
    BLUE_FIGHTER_ID = Field()
    RED_OUTCOME = Field()
    BLUE_OUTCOME = Field()
    BOUT_TYPE = Field()
    BOUT_PERF_BONUS = Field()
    OUTCOME_METHOD = Field()
    OUTCOME_METHOD_DETAILS = Field()
    END_ROUND = Field()
    END_ROUND_TIME_SECONDS = Field()
    BOUT_TIME_FORMAT = Field()
    TOTAL_TIME_SECONDS = Field()

    # Overall
    RED_KNOCKDOWNS = Field()
    BLUE_KNOCKDOWNS = Field()
    RED_TOTAL_STRIKES_LANDED = Field()
    RED_TOTAL_STRIKES_ATTEMPTED = Field()
    BLUE_TOTAL_STRIKES_LANDED = Field()
    BLUE_TOTAL_STRIKES_ATTEMPTED = Field()
    RED_TAKEDOWNS_LANDED = Field()
    RED_TAKEDOWNS_ATTEMPTED = Field()
    BLUE_TAKEDOWNS_LANDED = Field()
    BLUE_TAKEDOWNS_ATTEMPTED = Field()
    RED_SUBMISSION_ATTEMPTS = Field()
    BLUE_SUBMISSION_ATTEMPTS = Field()
    RED_REVERSALS = Field()
    BLUE_REVERSALS = Field()
    RED_CONTROL_TIME_SECONDS = Field()
    BLUE_CONTROL_TIME_SECONDS = Field()
    RED_SIGNIFICANT_STRIKES_LANDED = Field()
    RED_SIGNIFICANT_STRIKES_ATTEMPTED = Field()
    BLUE_SIGNIFICANT_STRIKES_LANDED = Field()
    BLUE_SIGNIFICANT_STRIKES_ATTEMPTED = Field()
    RED_SIGNIFICANT_STRIKES_HEAD_LANDED = Field()
    RED_SIGNIFICANT_STRIKES_HEAD_ATTEMPTED = Field()
    BLUE_SIGNIFICANT_STRIKES_HEAD_LANDED = Field()
    BLUE_SIGNIFICANT_STRIKES_HEAD_ATTEMPTED = Field()
    RED_SIGNIFICANT_STRIKES_BODY_LANDED = Field()
    RED_SIGNIFICANT_STRIKES_BODY_ATTEMPTED = Field()
    BLUE_SIGNIFICANT_STRIKES_BODY_LANDED = Field()
    BLUE_SIGNIFICANT_STRIKES_BODY_ATTEMPTED = Field()
    RED_SIGNIFICANT_STRIKES_LEG_LANDED = Field()
    RED_SIGNIFICANT_STRIKES_LEG_ATTEMPTED = Field()
    BLUE_SIGNIFICANT_STRIKES_LEG_LANDED = Field()
    BLUE_SIGNIFICANT_STRIKES_LEG_ATTEMPTED = Field()
    RED_SIGNIFICANT_STRIKES_DISTANCE_LANDED = Field()
    RED_SIGNIFICANT_STRIKES_DISTANCE_ATTEMPTED = Field()
    BLUE_SIGNIFICANT_STRIKES_DISTANCE_LANDED = Field()
    BLUE_SIGNIFICANT_STRIKES_DISTANCE_ATTEMPTED = Field()
    RED_SIGNIFICANT_STRIKES_CLINCH_LANDED = Field()
    RED_SIGNIFICANT_STRIKES_CLINCH_ATTEMPTED = Field()
    BLUE_SIGNIFICANT_STRIKES_CLINCH_LANDED = Field()
    BLUE_SIGNIFICANT_STRIKES_CLINCH_ATTEMPTED = Field()
    RED_SIGNIFICANT_STRIKES_GROUND_LANDED = Field()
    RED_SIGNIFICANT_STRIKES_GROUND_ATTEMPTED = Field()
    BLUE_SIGNIFICANT_STRIKES_GROUND_LANDED = Field()
    BLUE_SIGNIFICANT_STRIKES_GROUND_ATTEMPTED = Field()


class UFCStatsBoutRoundItem(Item):
    """
    Item class for round-by-round bout data from UFCStats
    """

    BOUT_ROUND_ID = Field()
    BOUT_ID = Field()
    EVENT_ID = Field()
    DATE = Field()
    BOUT_ORDINAL = Field()
    ROUND = Field()

    # Round stats
    RED_KNOCKDOWNS = Field()
    BLUE_KNOCKDOWNS = Field()
    RED_TOTAL_STRIKES_LANDED = Field()
    RED_TOTAL_STRIKES_ATTEMPTED = Field()
    BLUE_TOTAL_STRIKES_LANDED = Field()
    BLUE_TOTAL_STRIKES_ATTEMPTED = Field()
    RED_TAKEDOWNS_LANDED = Field()
    RED_TAKEDOWNS_ATTEMPTED = Field()
    BLUE_TAKEDOWNS_LANDED = Field()
    BLUE_TAKEDOWNS_ATTEMPTED = Field()
    RED_SUBMISSION_ATTEMPTS = Field()
    BLUE_SUBMISSION_ATTEMPTS = Field()
    RED_REVERSALS = Field()
    BLUE_REVERSALS = Field()
    RED_CONTROL_TIME_SECONDS = Field()
    BLUE_CONTROL_TIME_SECONDS = Field()
    RED_SIGNIFICANT_STRIKES_LANDED = Field()
    RED_SIGNIFICANT_STRIKES_ATTEMPTED = Field()
    BLUE_SIGNIFICANT_STRIKES_LANDED = Field()
    BLUE_SIGNIFICANT_STRIKES_ATTEMPTED = Field()
    RED_SIGNIFICANT_STRIKES_HEAD_LANDED = Field()
    RED_SIGNIFICANT_STRIKES_HEAD_ATTEMPTED = Field()
    BLUE_SIGNIFICANT_STRIKES_HEAD_LANDED = Field()
    BLUE_SIGNIFICANT_STRIKES_HEAD_ATTEMPTED = Field()
    RED_SIGNIFICANT_STRIKES_BODY_LANDED = Field()
    RED_SIGNIFICANT_STRIKES_BODY_ATTEMPTED = Field()
    BLUE_SIGNIFICANT_STRIKES_BODY_LANDED = Field()
    BLUE_SIGNIFICANT_STRIKES_BODY_ATTEMPTED = Field()
    RED_SIGNIFICANT_STRIKES_LEG_LANDED = Field()
    RED_SIGNIFICANT_STRIKES_LEG_ATTEMPTED = Field()
    BLUE_SIGNIFICANT_STRIKES_LEG_LANDED = Field()
    BLUE_SIGNIFICANT_STRIKES_LEG_ATTEMPTED = Field()
    RED_SIGNIFICANT_STRIKES_DISTANCE_LANDED = Field()
    RED_SIGNIFICANT_STRIKES_DISTANCE_ATTEMPTED = Field()
    BLUE_SIGNIFICANT_STRIKES_DISTANCE_LANDED = Field()
    BLUE_SIGNIFICANT_STRIKES_DISTANCE_ATTEMPTED = Field()
    RED_SIGNIFICANT_STRIKES_CLINCH_LANDED = Field()
    RED_SIGNIFICANT_STRIKES_CLINCH_ATTEMPTED = Field()
    BLUE_SIGNIFICANT_STRIKES_CLINCH_LANDED = Field()
    BLUE_SIGNIFICANT_STRIKES_CLINCH_ATTEMPTED = Field()
    RED_SIGNIFICANT_STRIKES_GROUND_LANDED = Field()
    RED_SIGNIFICANT_STRIKES_GROUND_ATTEMPTED = Field()
    BLUE_SIGNIFICANT_STRIKES_GROUND_LANDED = Field()
    BLUE_SIGNIFICANT_STRIKES_GROUND_ATTEMPTED = Field()


class TapologyBoutItem(Item):
    """
    Item class for bout data from Tapology
    """

    BOUT_ID = Field()
    UFCSTATS_BOUT_ID = Field()
    EVENT_ID = Field()
    UFCSTATS_EVENT_ID = Field()
    EVENT_NAME = Field()
    DATE = Field()
    REGION = Field()
    LOCATION = Field()
    VENUE = Field()
    BOUT_ORDINAL = Field()
    BOUT_CARD_TYPE = Field()

    # Fighter info
    FIGHTER_1_ID = Field()
    FIGHTER_2_ID = Field()
    FIGHTER_1_RECORD_AT_BOUT = Field()
    FIGHTER_2_RECORD_AT_BOUT = Field()
    FIGHTER_1_WEIGHT_POUNDS = Field()
    FIGHTER_2_WEIGHT_POUNDS = Field()
    FIGHTER_1_GYM = Field()
    FIGHTER_2_GYM = Field()


class TapologyFighterItem(Item):
    """
    Item class for fighter data from Tapology
    """

    FIGHTER_ID = Field()
    UFCSTATS_FIGHTER_ID = Field()
    SHERDOG_FIGHTER_ID = Field()
    FIGHTER_NAME = Field()
    NATIONALITY = Field()
    HEIGHT_INCHES = Field()
    REACH_INCHES = Field()
    DATE_OF_BIRTH = Field()


class FightMatrixRankingItem(Item):
    """
    Item class for ranking data from FightMatrix
    """

    FIGHTER_ID = Field()
    DATE = Field()
    WEIGHT_CLASS = Field()
    RANK = Field()
    RANK_CHANGE = Field()
    POINTS = Field()


class FightMatrixFighterItem(Item):
    """
    Item class for fighter data from FightMatrix
    """

    FIGHTER_NAME = Field()
    FIGHTER_ID = Field()
    TAPOLOGY_FIGHTER_ID = Field()
    SHERDOG_FIGHTER_ID = Field()


class UFCStatsUpcomingBoutItem(Item):
    """
    Item class for upcoming bout data from UFCStats
    """


class TapologyUpcomingBoutItem(Item):
    """
    Item class for upcoming bout data from Tapology
    """


class FightOddsIOBoutItem:
    """
    Item class for odds data for upcoming bouts from FightOdds.io
    """
