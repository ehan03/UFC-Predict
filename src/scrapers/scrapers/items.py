# standard library imports

# local imports

# third party imports
import scrapy


class FighterItem(scrapy.Item):
    fighter_id = scrapy.Field()
    fighter_name = scrapy.Field()
    wins = scrapy.Field()
    losses = scrapy.Field()
    draws = scrapy.Field()
    nc = scrapy.Field()
    height = scrapy.Field()
    weight = scrapy.Field()
    reach = scrapy.Field()
    stance = scrapy.Field()
    dob = scrapy.Field()
    slpm = scrapy.Field()
    str_acc = scrapy.Field()
    sapm = scrapy.Field()
    str_def = scrapy.Field()
    td_avg = scrapy.Field()
    td_acc = scrapy.Field()
    td_def = scrapy.Field()
    sub_avg = scrapy.Field()


class BoutItem(scrapy.Item):
    # info from event page
    event_id = scrapy.Field()
    event_name = scrapy.Field()
    date = scrapy.Field()
    location = scrapy.Field()
    bout_ordinal = scrapy.Field()

    # info from bout page


class UpcomingEventItem(scrapy.Item):
    pass
