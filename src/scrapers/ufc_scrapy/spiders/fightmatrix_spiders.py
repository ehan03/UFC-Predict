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


class FightMatrixResultsSpider(Spider):
    """
    Spider for scraping historical rankings and custom ELO data from FightMatrix
    """


class FightMatrixUpcomingEventSpider(Spider):
    """
    Spider for scraping rankings and custom ELO data for
    upcoming UFC event from FightMatrix
    """
