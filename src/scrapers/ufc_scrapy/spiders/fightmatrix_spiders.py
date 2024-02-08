# standard library imports
import json
from datetime import datetime, timedelta, timezone

# third party imports
import numpy as np
import pandas as pd
import w3lib.html
from scrapy.http import Request
from scrapy.spiders import Spider

# local imports
from src.scrapers.ufc_scrapy.items import (
    FightOddsIOBoutItem,
    FightOddsIOClosingOddsItem,
    FightOddsIOFighterItem,
    FightOddsIOUpcomingBoutItem,
    SherdogBoutItem,
    SherdogFighterItem,
    UFCStatsBoutOverallItem,
    UFCStatsBoutRoundItem,
    UFCStatsFighterItem,
    UFCStatsUpcomingBoutItem,
)
from src.scrapers.ufc_scrapy.utils import (
    EVENT_ODDS_GQL_QUERY,
    EVENTS_RECENT_GQL_QUERY,
    EVENTS_UPCOMING_GQL_QUERY,
    FIGHTERS_GQL_QUERY,
    FIGHTS_GQL_QUERY,
    convert_height,
    ctrl_time,
    extract_landed_attempted,
    total_time,
)


class FightMatrixResultsSpider(Spider):
    """
    Spider for scraping historical rankings and custom ELO data from FightMatrix
    """


class FightMatrixUpcomingEventSpider(Spider):
    """
    Spider for scraping rankings and custom ELO data for
    upcoming UFC event from FightMatrix
    """
