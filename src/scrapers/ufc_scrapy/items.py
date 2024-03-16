# standard library imports

# local imports

# third party imports
from scrapy import Field, Item


# UFC Stats items
class UFCStatsFighterItem(Item):
    """
    Item class for fighter data from UFCStats
    """

    FIGHTER_ID = Field()
    FIGHTER_NAME = Field()
    FIGHTER_NICKNAME = Field()
    HEIGHT_INCHES = Field()
    REACH_INCHES = Field()
    STANCE = Field()
    DATE_OF_BIRTH = Field()


class UFCStatsBoutOverallItem(Item):
    """
    Item class for overall bout data from UFCStats
    """

    BOUT_ID = Field()
    EVENT_ID = Field()
    EVENT_NAME = Field()
    DATE = Field()
    LOCATION = Field()
    BOUT_ORDINAL = Field()
    RED_FIGHTER_ID = Field()
    BLUE_FIGHTER_ID = Field()
    RED_OUTCOME = Field()
    BLUE_OUTCOME = Field()
    WEIGHT_CLASS = Field()
    BOUT_LONGNAME = Field()
    BOUT_PERF_BONUS = Field()
    OUTCOME_METHOD = Field()
    OUTCOME_METHOD_DETAILS = Field()
    END_ROUND = Field()
    END_ROUND_TIME_SECONDS = Field()
    BOUT_TIME_FORMAT = Field()
    TOTAL_TIME_SECONDS = Field()


class UFCStatsBoutRoundItem(Item):
    """
    Item class for round-by-round bout data from UFCStats
    """

    BOUT_ID = Field()
    ROUND = Field()
    TIME_FOUGHT_SECONDS = Field()
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


class UFCStatsUpcomingBoutItem(Item):
    """
    Item class for upcoming bout data from UFCStats
    """

    BOUT_ID = Field()
    EVENT_ID = Field()
    EVENT_NAME = Field()
    DATE = Field()
    LOCATION = Field()
    BOUT_ORDINAL = Field()
    RED_FIGHTER_ID = Field()
    BLUE_FIGHTER_ID = Field()
    WEIGHT_CLASS = Field()
    BOUT_LONGNAME = Field()


# FightOdds.io items
class FightOddsIOFighterItem(Item):
    """
    Item class for fighter data from FightOdds.io
    """

    FIGHTER_ID = Field()
    FIGHTER_NAME = Field()
    FIGHTER_NICKNAME = Field()
    HEIGHT_CENTIMETERS = Field()
    REACH_INCHES = Field()
    LEG_REACH_INCHES = Field()
    FIGHTING_STYLE = Field()
    STANCE = Field()
    DATE_OF_BIRTH = Field()


class FightOddsIOBoutItem(Item):
    """
    Item class for historical bout data from FightOdds.io
    """

    BOUT_SLUG = Field()
    EVENT_SLUG = Field()
    EVENT_NAME = Field()
    DATE = Field()
    LOCATION = Field()
    VENUE = Field()
    BOUT_ORDINAL = Field()
    BOUT_CARD_TYPE = Field()
    WEIGHT_CLASS = Field()
    WEIGHT = Field()
    FIGHTER_1_ID = Field()
    FIGHTER_2_ID = Field()
    WINNER_ID = Field()
    OUTCOME_METHOD_1 = Field()
    OUTCOME_METHOD_2 = Field()
    END_ROUND = Field()
    END_ROUND_TIME_SECONDS = Field()


class FightOddsIOClosingOddsItem(Item):
    """
    Item class for historical average closing odds data from FightOdds.io
    """

    BOUT_SLUG = Field()
    FIGHTER_1_ODDS = Field()
    FIGHTER_2_ODDS = Field()


class FightOddsIOUpcomingBoutItem(Item):
    """
    Item class for upcoming bout data from FightOdds.io
    """

    BOUT_SLUG = Field()
    EVENT_SLUG = Field()
    EVENT_NAME = Field()
    DATE = Field()
    LOCATION = Field()
    VENUE = Field()
    FIGHTER_1_ID = Field()
    FIGHTER_2_ID = Field()
    FIGHTER_1_ODDS_DRAFTKINGS = Field()
    FIGHTER_2_ODDS_DRAFTKINGS = Field()


# Sherdog items
class SherdogFighterItem(Item):
    """
    Item class for fighter data from Sherdog
    """

    FIGHTER_ID = Field()
    FIGHTER_NAME = Field()
    FIGHTER_NICKNAME = Field()
    HEIGHT_INCHES = Field()
    DATE_OF_BIRTH = Field()
    NATIONALITY = Field()
    PRO_DEBUT_DATE = Field()


class SherdogBoutItem(Item):
    """
    Item class for historical bout data from Sherdog
    """

    EVENT_ID = Field()
    EVENT_NAME = Field()
    DATE = Field()
    LOCATION = Field()
    VENUE = Field()
    BOUT_ORDINAL = Field()
    FIGHTER_1_ID = Field()
    FIGHTER_2_ID = Field()
    FIGHTER_1_OUTCOME = Field()
    FIGHTER_2_OUTCOME = Field()
    WEIGHT_CLASS = Field()
    WEIGHT = Field()
    OUTCOME_METHOD = Field()
    END_ROUND = Field()
    END_ROUND_TIME_SECONDS = Field()
    TOTAL_TIME_SECONDS = Field()


class SherdogFighterBoutHistoryItem(Item):
    """
    Item class for historical bout data from Sherdog beyond
    those in the UFC
    """

    FIGHTER_ID = Field()
    FIGHTER_BOUT_ORDINAL = Field()
    EVENT_ID = Field()
    EVENT_NAME = Field()
    DATE = Field()
    OPPONENT_ID = Field()
    OPPONENT_NAME = Field()
    OUTCOME = Field()
    OUTCOME_METHOD = Field()
    END_ROUND = Field()
    END_ROUND_TIME_SECONDS = Field()
    TOTAL_TIME_SECONDS = Field()


# FightMatrix items
class FightMatrixFighterItem(Item):
    """
    Item class for fighter data from FightMatrix
    """

    FIGHTER_ID = Field()
    SHERDOG_FIGHTER_ID = Field()
    FIGHTER_NAME = Field()
    PRO_DEBUT_DATE = Field()
    UFC_DEBUT_DATE = Field()


class FightMatrixBoutEloItem(Item):
    """
    Item class for historical bout data from FightMatrix
    """

    FIGHTER_ID = Field()
    FIGHTER_BOUT_ORDINAL = Field()
    EVENT_ID = Field()
    EVENT_NAME = Field()
    DATE = Field()
    OPPONENT_ID = Field()
    OPPONENT_NAME = Field()
    ELO_K170_PRE = Field()
    ELO_K170_POST = Field()
    ELO_MODIFIED_PRE = Field()
    ELO_MODIFIED_POST = Field()
    GLICKO1_PRE = Field()
    GLICKO1_POST = Field()
    OPPONENT_ELO_K170_PRE = Field()
    OPPONENT_ELO_K170_POST = Field()
    OPPONENT_ELO_MODIFIED_PRE = Field()
    OPPONENT_ELO_MODIFIED_POST = Field()
    OPPONENT_GLICKO1_PRE = Field()
    OPPONENT_GLICKO1_POST = Field()
    OUTCOME = Field()
    OUTCOME_METHOD = Field()
    END_ROUND = Field()


class FightMatrixCutoffEventItem(Item):
    """
    Item class for events whose names are cutoff
    """

    EVENT_ID = Field()
    EVENT_NAME = Field()


class FightMatrixRankingItem(Item):
    """
    Item class for ranking data from FightMatrix
    """

    ISSUE_DATE = Field()
    WEIGHT_CLASS = Field()
    FIGHTER_ID = Field()
    RANK = Field()
    POINTS = Field()
