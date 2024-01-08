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
    WEIGHT_CLASS = Field()
    BOUT_GENDER = Field()
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

    BOUT_ROUND_ID = Field()
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


class FightOddsIOFighterItem(Item):
    """
    Item class for fighter data from FightOdds.io
    """

    FIGHTER_SLUG = Field()
    FIGHTER_NAME = Field()
    FIGHTER_NICKNAME = Field()
    HEIGHT_CENTIMETERS = Field()
    REACH_INCHES = Field()
    LEG_REACH_INCHES = Field()
    FIGHTING_STYLE = Field()
    STANCE = Field()
    NATIONALITY = Field()
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

    FIGHTER_1_SLUG = Field()
    FIGHTER_2_SLUG = Field()
    WINNER_SLUG = Field()
    OUTCOME_METHOD_1 = Field()
    OUTCOME_METHOD_2 = Field()
    END_ROUND = Field()
    END_ROUND_TIME_SECONDS = Field()
    FIGHTER_1_ODDS = Field()
    FIGHTER_2_ODDS = Field()


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
    BOUT_GENDER = Field()
    BOUT_LONGNAME = Field()


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

    FIGHTER_1_SLUG = Field()
    FIGHTER_2_SLUG = Field()
    FIGHTER_1_ODDS_DRAFTKINGS = Field()
    FIGHTER_2_ODDS_DRAFTKINGS = Field()
