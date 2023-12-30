# standard library imports
import logging

# third party imports
from scrapy import logformatter

# local imports


class PoliteLogFormatter(logformatter.LogFormatter):
    def dropped(self, item, exception, response, spider):
        return {
            "level": logging.DEBUG,
            "msg": logformatter.DROPPEDMSG,
            "args": {
                "exception": exception,
                "item": item,
            },
        }
