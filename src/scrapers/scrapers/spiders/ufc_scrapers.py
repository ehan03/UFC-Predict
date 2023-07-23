# standard library imports
from string import ascii_lowercase

# third party imports
import pandas as pd
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule, Spider

# local imports
from ..items import BoutItem, FighterItem
from ..utils import convert_height, extract_record


class UFCStatsCrawler(CrawlSpider):
    name = "ufc_stats_crawler"
    allowed_domains = ["ufcstats.com"]
    start_urls = [
        f"http://ufcstats.com/statistics/fighters?char={char}&page=all"
        for char in ascii_lowercase
    ]
    rules = (
        Rule(
            LinkExtractor(
                allow=r"fighter-details",
                restrict_css="""
                    td.b-statistics__table-col > 
                    a.b-link.b-link_style_black""",
            ),
            callback="parse_fighter",
            follow=True,
        ),
        Rule(
            LinkExtractor(
                allow=r"event-details",
                restrict_css="""
                    td.b-fight-details__table-col.l-page_align_left >
                    p.b-fight-details__table-text >
                    a.b-link.b-link_style_black""",
            ),
            callback="parse_event",
            follow=True,
        ),
    )
    custom_settings = {
        "ITEM_PIPELINES": {
            "scrapers.pipelines.FightersSQLitePipeline": 100,
            "scrapers.pipelines.BoutsSQLitePipeline": 100,
        }
    }

    def parse_fighter(self, response):
        fighter_item = FighterItem()

        # Get all relevant fields
        fighter_item["fighter_id"] = response.url.split("/")[-1]
        fighter_item["fighter_name"] = (
            response.css("span.b-content__title-highlight::text").get().strip()
        )
        record = (
            response.css("span.b-content__title-record::text")
            .get()
            .replace("Record: ", "")
            .strip()
        )
        (
            fighter_item["wins"],
            fighter_item["losses"],
            fighter_item["draws"],
            fighter_item["nc"],
        ) = extract_record(record)

        info = [
            x.strip()
            for i, x in enumerate(
                response.css(
                    "li.b-list__box-list-item.b-list__box-list-item_type_block::text"
                ).getall()
            )
            if (i % 2 == 1 and i != 19)
        ]
        fighter_item["height"] = convert_height(info[0])
        fighter_item["weight"] = (
            float(info[1].replace(" lbs.", "")) if info[1] != "--" else None
        )
        fighter_item["reach"] = (
            float(info[2].replace('"', "")) if info[2] != "--" else None
        )
        fighter_item["stance"] = info[3] if info[3] else None
        fighter_item["dob"] = (
            pd.to_datetime(info[4]).strftime("%Y-%m-%d") if info[4] != "--" else None
        )
        fighter_item["slpm"] = float(info[5])
        fighter_item["str_acc"] = float(info[6].replace("%", "")) / 100
        fighter_item["sapm"] = float(info[7])
        fighter_item["str_def"] = float(info[8].replace("%", "")) / 100
        fighter_item["td_avg"] = float(info[9])
        fighter_item["td_acc"] = float(info[10].replace("%", "")) / 100
        fighter_item["td_def"] = float(info[11].replace("%", "")) / 100
        fighter_item["sub_avg"] = float(info[12])

        yield fighter_item

    def parse_event(self, response):
        bout_urls = response.css(
            """tr.b-fight-details__table-row.b-fight-details__table-row__hover.js-fight-details-click > 
            td.b-fight-details__table-col.b-fight-details__table-col_style_align-top >
            p.b-fight-details__table-text > 
            a.b-flag::attr(href)"""
        ).getall()

        event_id = response.url.split("/")[-1]
        event_name = (
            response.css(
                """h2.b-content__title > 
                span.b-content__title-highlight::text"""
            )
            .get()
            .strip()
        )
        date, location = [
            x.strip()
            for i, x in enumerate(
                response.css("li.b-list__box-list-item::text").getall()
            )
            if i % 2 == 1
        ]

        for bout_ordinal, bout_url in enumerate(reversed(bout_urls)):
            yield response.follow(
                bout_url,
                callback=self.parse_bout,
                cb_kwargs={
                    "event_id": event_id,
                    "event_name": event_name,
                    "date": date,
                    "location": location,
                    "bout_ordinal": bout_ordinal,
                },
            )

    def parse_bout(self, response):
        bout_item = BoutItem()

        bout_item["event_id"] = response.cb_kwargs["event_id"]
        bout_item["event_name"] = response.cb_kwargs["event_name"]
        bout_item["date"] = response.cb_kwargs["date"]
        bout_item["location"] = response.cb_kwargs["location"]
        bout_item["bout_ordinal"] = response.cb_kwargs["bout_ordinal"]

        # Get all relevant fields


class UpcomingEventSpider(Spider):
    pass


class FightOddsIOSpider(Spider):
    pass
