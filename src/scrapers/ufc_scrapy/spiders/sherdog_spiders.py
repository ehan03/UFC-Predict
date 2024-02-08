# standard library imports
from datetime import datetime, timedelta, timezone

# third party imports
import pandas as pd
import w3lib.html
from scrapy.http import Request
from scrapy.spiders import Spider

# local imports
from src.scrapers.ufc_scrapy.items import (
    SherdogBoutItem,
    SherdogFighterItem,
    SherdogUpcomingBoutItem,
)
from src.scrapers.ufc_scrapy.utils import convert_height


class SherdogResultsSpider(Spider):
    """
    Spider for scraping historical fighter and bout data from Sherdog
    """

    name = "sherdog_results_spider"
    allowed_domains = ["sherdog.com"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 10,
        "CONCURRENT_REQUESTS": 10,
        "DOWNLOADER_MIDDLEWARES": {
            "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
            "scrapy_user_agents.middlewares.RandomUserAgentMiddleware": 400,
        },
        "REQUEST_FINGERPRINTER_IMPLEMENTATION": "2.7",
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "FEED_EXPORT_ENCODING": "utf-8",
        "DEPTH_PRIORITY": 1,
        "SCHEDULER_DISK_QUEUE": "scrapy.squeues.PickleFifoDiskQueue",
        "SCHEDULER_MEMORY_QUEUE": "scrapy.squeues.FifoMemoryQueue",
        "RETRY_TIMES": 1,
        "LOG_LEVEL": "INFO",
        "ITEM_PIPELINES": {
            # TODO: Add Sherdog pipelines
        },
        "CLOSESPIDER_ERRORCOUNT": 1,
    }

    def __init__(self, *args, scrape_type: str, **kwargs):
        super().__init__(*args, **kwargs)
        assert scrape_type in {"all", "most_recent"}
        self.scrape_type = scrape_type
        self.outcome_map = {
            "win": "W",
            "loss": "L",
            "draw": "D",
            "nc": "NC",
        }

    def start_requests(self):
        start_url = "https://www.sherdog.com/organizations/Ultimate-Fighting-Championship-UFC-2/recent-events/1"

        yield Request(
            url=start_url,
            callback=self.parse_recent_events_page,
        )

    def parse_recent_events_page(self, response):
        table = response.css("div.single_tab#recent_tab > table.new_table.event")
        event_urls = table.css(
            "tr[itemtype='http://schema.org/Event'] > td > a::attr(href)"
        ).getall()
        event_names = table.css(
            "tr[itemtype='http://schema.org/Event'] > td > a > span[itemprop='name']::text"
        ).getall()
        dates = table.css(
            "tr[itemtype='http://schema.org/Event'] > td > meta[itemprop='startDate']::attr(content)"
        ).getall()
        locations = [
            x.strip()
            for x in table.css(
                "tr[itemtype='http://schema.org/Event'] > td[itemprop='location']::text"
            ).getall()
        ]

        event_urls_valid = []
        event_names_valid = []
        dates_valid = []
        locations_valid = []

        for event_url, event_name, date, location in zip(
            event_urls, event_names, dates, locations
        ):
            if "Road to UFC" not in event_name:
                event_urls_valid.append(event_url)
                event_names_valid.append(event_name)
                dates_valid.append(date)
                locations_valid.append(location)

        if self.scrape_type == "most_recent":
            event_urls_valid = [event_urls_valid[0]]
            event_names_valid = [event_names_valid[0]]
            dates_valid = [dates_valid[0]]
            locations_valid = [locations_valid[0]]

        for event_url, event_name, date, location in zip(
            event_urls_valid, event_names_valid, dates_valid, locations_valid
        ):
            yield response.follow(
                response.urljoin(event_url),
                callback=self.parse_event,
                cb_kwargs={
                    "event_name": event_name,
                    "date": pd.to_datetime(date).strftime("%Y-%m-%d"),
                    "location": location,
                },
            )

        pagination = response.css("div.footer > span.pagination")[0]
        pagination_url = pagination.css("a")[-1].attrib["href"]
        pagination_desc = pagination.css("a")[-1].css("::text").get()

        if pagination_desc == "Older Events »" and self.scrape_type == "all":
            yield response.follow(
                response.urljoin(pagination_url),
                callback=self.parse_recent_events_page,
            )

    def parse_event(self, response, event_name, date, location):
        venue = location.split(", ")[0].strip()
        location_city = location.replace(f"{venue}, ", "").strip()
        fighter_urls = []

        # Main event
        main_event_bout_item = SherdogBoutItem()

        main_event = response.css(
            "div[itemprop='subEvent'][itemtype='http://schema.org/Event']"
        )

        if main_event:
            main_event_bout_item["EVENT_ID"] = response.url.split("/")[-1]
            main_event_bout_item["EVENT_NAME"] = event_name
            main_event_bout_item["DATE"] = date
            main_event_bout_item["LOCATION"] = location_city
            main_event_bout_item["VENUE"] = venue
            main_event_bout_item["FIGHTER_1_ID"] = (
                main_event.css("div.fighter.left_side > a[itemprop='url']::attr(href)")
                .get()
                .split("/")[-1]
            )
            fighter_urls.append(
                main_event.css(
                    "div.fighter.left_side > a[itemprop='url']::attr(href)"
                ).get()
            )
            main_event_bout_item["FIGHTER_2_ID"] = (
                main_event.css("div.fighter.right_side > a[itemprop='url']::attr(href)")
                .get()
                .split("/")[-1]
            )
            fighter_urls.append(
                main_event.css(
                    "div.fighter.right_side > a[itemprop='url']::attr(href)"
                ).get()
            )
            main_event_bout_item["FIGHTER_1_OUTCOME"] = self.outcome_map[
                main_event.css("div.fighter.left_side > span.final_result::text")
                .get()
                .lower()
            ]
            main_event_bout_item["FIGHTER_2_OUTCOME"] = self.outcome_map[
                main_event.css("div.fighter.right_side > span.final_result::text")
                .get()
                .lower()
            ]
            main_event_weight_class = main_event.css(
                "div.versus > span.weight_class::text"
            )
            main_event_bout_item["WEIGHT_CLASS"] = (
                main_event_weight_class.get().strip()
                if main_event_weight_class
                else None
            )

            main_event_resume_td_tags = main_event.css(
                "table.fight_card_resume > tr > td"
            )
            for td_tag in main_event_resume_td_tags:
                td_text = td_tag.css("::text").getall()
                if td_text[0] == "Match":
                    main_event_bout_item["BOUT_ORDINAL"] = int(td_text[1]) - 1
                elif td_text[0] == "Method":
                    main_event_bout_item["OUTCOME_METHOD"] = td_text[1].strip()
                elif td_text[0] == "Round":
                    main_event_bout_item["END_ROUND"] = int(td_text[1])
                elif td_text[0] == "Time":
                    end_round_time_split = td_text[1].strip().split(":")
                    main_event_bout_item["END_ROUND_TIME_SECONDS"] = 60 * int(
                        end_round_time_split[0]
                    ) + int(end_round_time_split[1])

            yield main_event_bout_item

            # Rest of the card
            card_table_rows = response.css(
                """div.new_table_holder > table.new_table.result > tbody > 
                tr[itemprop='subEvent'][itemtype='http://schema.org/Event']"""
            )
            for row in card_table_rows:
                bout_item = SherdogBoutItem()

                bout_item["EVENT_ID"] = response.url.split("/")[-1]
                bout_item["EVENT_NAME"] = event_name
                bout_item["DATE"] = date
                bout_item["LOCATION"] = location_city
                bout_item["VENUE"] = venue

                tds = row.css("td")

                bout_item["BOUT_ORDINAL"] = (
                    int(w3lib.html.remove_tags(tds[0].get()).strip()) - 1
                )

                bout_item["FIGHTER_1_ID"] = (
                    tds[1]
                    .css(
                        "div.fighter_list.left > div.fighter_result_data > a[itemprop='url']::attr(href)"
                    )
                    .get()
                    .split("/")[-1]
                )
                bout_item["FIGHTER_1_OUTCOME"] = self.outcome_map[
                    tds[1].css("span.final_result::text").get().lower()
                ]
                fighter_urls.append(
                    tds[1]
                    .css(
                        "div.fighter_list.left > div.fighter_result_data > a[itemprop='url']::attr(href)"
                    )
                    .get()
                )

                weight_class = tds[2].css("span.weight_class::text").get()
                bout_item["WEIGHT_CLASS"] = (
                    weight_class.strip() if weight_class else None
                )

                bout_item["FIGHTER_2_ID"] = (
                    tds[3]
                    .css(
                        "div.fighter_list.right > div.fighter_result_data > a[itemprop='url']::attr(href)"
                    )
                    .get()
                    .split("/")[-1]
                )
                bout_item["FIGHTER_2_OUTCOME"] = self.outcome_map[
                    tds[3].css("span.final_result::text").get().lower()
                ]
                fighter_urls.append(
                    tds[3]
                    .css(
                        "div.fighter_list.right > div.fighter_result_data > a[itemprop='url']::attr(href)"
                    )
                    .get()
                )

                bout_item["OUTCOME_METHOD"] = tds[4].css("b::text").get().strip()
                bout_item["END_ROUND"] = int(tds[5].css("::text").get().strip())
                end_round_time_split = tds[6].css("::text").get().strip().split(":")
                bout_item["END_ROUND_TIME_SECONDS"] = 60 * int(
                    end_round_time_split[0]
                ) + int(end_round_time_split[1])

                yield bout_item

            for fighter_url in fighter_urls:
                yield response.follow(
                    response.urljoin(fighter_url),
                    callback=self.parse_fighter,
                )

    def parse_fighter(self, response):
        fighter_item = SherdogFighterItem()

        fighter_item["FIGHTER_ID"] = response.url.split("/")[-1]
        fighter_item["FIGHTER_NAME"] = response.css(
            "div.fighter-line1 > h1[itemprop='name'] > span.fn::text"
        ).get()

        nick = response.css("div.fighter-line2 > h1[itemprop='name'] > span.nickname")
        fighter_item["FIGHTER_NICKNAME"] = nick.css("em::text").get() if nick else None
        fighter_item["NATIONALITY"] = response.css(
            "div.fighter-nationality > span.item.birthplace > strong[itemprop='nationality']::text"
        ).get()

        dob = response.css(
            "div.fighter-data > div.bio-holder > table > tr > td > span[itemprop='birthDate']::text"
        ).get()
        fighter_item["DATE_OF_BIRTH"] = (
            pd.to_datetime(dob).strftime("%Y-%m-%d") if dob else None
        )

        height = response.css(
            "div.fighter-data > div.bio-holder > table > tr > td > b[itemprop='height']::text"
        ).get()
        fighter_item["HEIGHT_INCHES"] = (
            convert_height(height.replace("'", "' ")) if height else None
        )

        fight_history_rows = response.css(
            "div.module.fight_history > div.new_table_holder > table.new_table.fighter > tr"
        )
        fighter_item["PRO_DEBUT_DATE"] = pd.to_datetime(
            fight_history_rows[-1].css("td > span.sub_line::text").get()
        ).strftime("%Y-%m-%d")

        yield fighter_item


class SherdogUpcomingEventSpider(Spider):
    """
    Spider for scraping upcoming UFC event data from Sherdog
    """

    name = "sherdog_upcoming_event_spider"
    allowed_domains = ["sherdog.com"]
    start_urls = [
        "https://www.sherdog.com/organizations/Ultimate-Fighting-Championship-UFC-2/upcoming-events/1"
    ]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 10,
        "CONCURRENT_REQUESTS": 10,
        "DOWNLOADER_MIDDLEWARES": {
            "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
            "scrapy_user_agents.middlewares.RandomUserAgentMiddleware": 400,
        },
        "REQUEST_FINGERPRINTER_IMPLEMENTATION": "2.7",
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "FEED_EXPORT_ENCODING": "utf-8",
        "DEPTH_PRIORITY": 1,
        "SCHEDULER_DISK_QUEUE": "scrapy.squeues.PickleFifoDiskQueue",
        "SCHEDULER_MEMORY_QUEUE": "scrapy.squeues.FifoMemoryQueue",
        "RETRY_TIMES": 1,
        "LOG_LEVEL": "INFO",
        "ITEM_PIPELINES": {
            # TODO: Add Sherdog pipelines
        },
        "CLOSESPIDER_ERRORCOUNT": 1,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.date_today = datetime.now(timezone.utc).date()

    def parse(self, response, **kwargs):
        next_saturday = (
            self.date_today + timedelta((5 - self.date_today.weekday()) % 7)
        ).strftime("%Y-%m-%d")

        table = response.css(
            "div.single_tab#upcoming_tab > div.new_table_holder > table.new_table.event"
        )
        next_event_date = pd.to_datetime(
            table.css(
                "tr[itemtype='http://schema.org/Event'] > td > meta[itemprop='startDate']::attr(content)"
            ).get()
        ).strftime("%Y-%m-%d")

        if next_event_date == next_saturday:
            upcoming_event_link = table.css(
                "tr[itemtype='http://schema.org/Event'] > td > a::attr(href)"
            ).get()
            upcoming_event_name = table.css(
                "tr[itemtype='http://schema.org/Event'] > td > a > span[itemprop='name']::text"
            ).get()
            upcoming_event_location = (
                table.css(
                    "tr[itemtype='http://schema.org/Event'] > td[itemprop='location']::text"
                )
                .get()
                .strip()
            )

            yield response.follow(
                response.urljoin(upcoming_event_link),
                callback=self.parse_upcoming_event,
                cb_kwargs={
                    "event_name": upcoming_event_name,
                    "date": next_event_date,
                    "location": upcoming_event_location,
                },
            )

    def parse_upcoming_event(self, response, event_name, date, location):
        venue = location.split(", ")[0].strip()
        location_city = location.replace(f"{venue}, ", "").strip()
        fighter_urls = []

        # Main event
        main_event_upcoming_bout_item = SherdogUpcomingBoutItem()

        main_event = response.css(
            "div[itemprop='subEvent'][itemtype='http://schema.org/Event']"
        )
        main_event_upcoming_bout_item["EVENT_ID"] = response.url.split("/")[-1]
        main_event_upcoming_bout_item["EVENT_NAME"] = event_name
        main_event_upcoming_bout_item["DATE"] = date
        main_event_upcoming_bout_item["LOCATION"] = location_city
        main_event_upcoming_bout_item["VENUE"] = venue
        main_event_upcoming_bout_item["FIGHTER_1_ID"] = (
            main_event.css("div.fighter.left_side > a[itemprop='url']::attr(href)")
            .get()
            .split("/")[-1]
        )
        fighter_urls.append(
            main_event.css(
                "div.fighter.left_side > a[itemprop='url']::attr(href)"
            ).get()
        )
        main_event_upcoming_bout_item["FIGHTER_2_ID"] = (
            main_event.css("div.fighter.right_side > a[itemprop='url']::attr(href)")
            .get()
            .split("/")[-1]
        )
        fighter_urls.append(
            main_event.css(
                "div.fighter.right_side > a[itemprop='url']::attr(href)"
            ).get()
        )
        main_event_upcoming_bout_item["WEIGHT_CLASS"] = (
            main_event.css("div.versus > span.weight_class::text").get().strip()
        )
        main_event_upcoming_bout_item["BOUT_ORDINAL"] = int(
            w3lib.html.remove_tags(
                response.css(
                    """div.new_table_holder > table.new_table.upcoming > tbody > 
                    tr[itemprop='subEvent'][itemtype='http://schema.org/Event'] > td"""
                ).get()
            )
        )

        yield main_event_upcoming_bout_item

        # Rest of the card
        card_table_rows = response.css(
            """div.new_table_holder > table.new_table.upcoming > tbody > 
            tr[itemprop='subEvent'][itemtype='http://schema.org/Event']"""
        )
        for row in card_table_rows:
            upcoming_bout_item = SherdogUpcomingBoutItem()

            upcoming_bout_item["EVENT_ID"] = response.url.split("/")[-1]
            upcoming_bout_item["EVENT_NAME"] = event_name
            upcoming_bout_item["DATE"] = date
            upcoming_bout_item["LOCATION"] = location_city
            upcoming_bout_item["VENUE"] = venue

            tds = row.css("td")

            upcoming_bout_item["BOUT_ORDINAL"] = (
                int(w3lib.html.remove_tags(tds[0].get()).strip()) - 1
            )

            upcoming_bout_item["FIGHTER_1_ID"] = (
                tds[1]
                .css(
                    "div.fighter_list.left > div.fighter_result_data > a[itemprop='url']::attr(href)"
                )
                .get()
                .split("/")[-1]
            )
            fighter_urls.append(
                tds[1]
                .css(
                    "div.fighter_list.left > div.fighter_result_data > a[itemprop='url']::attr(href)"
                )
                .get()
            )
            upcoming_bout_item["WEIGHT_CLASS"] = (
                tds[2].css("span.weight_class::text").get().strip()
            )
            upcoming_bout_item["FIGHTER_2_ID"] = (
                tds[3]
                .css(
                    "div.fighter_list.right > div.fighter_result_data > a[itemprop='url']::attr(href)"
                )
                .get()
                .split("/")[-1]
            )
            fighter_urls.append(
                tds[3]
                .css(
                    "div.fighter_list.right > div.fighter_result_data > a[itemprop='url']::attr(href)"
                )
                .get()
            )

            yield upcoming_bout_item

        for fighter_url in fighter_urls:
            yield response.follow(
                response.urljoin(fighter_url),
                callback=self.parse_fighter,
            )

    def parse_fighter(self, response):
        fighter_item = SherdogFighterItem()

        fighter_item["FIGHTER_ID"] = response.url.split("/")[-1]
        fighter_item["FIGHTER_NAME"] = response.css(
            "div.fighter-line1 > h1[itemprop='name'] > span.fn::text"
        ).get()

        nick = response.css("div.fighter-line2 > h1[itemprop='name'] > span.nickname")
        fighter_item["FIGHTER_NICKNAME"] = nick.css("em::text").get() if nick else None
        fighter_item["NATIONALITY"] = response.css(
            "div.fighter-nationality > span.item.birthplace > strong[itemprop='nationality']::text"
        ).get()

        dob = response.css(
            "div.fighter-data > div.bio-holder > table > tr > td > span[itemprop='birthDate']::text"
        ).get()
        fighter_item["DATE_OF_BIRTH"] = (
            pd.to_datetime(dob).strftime("%Y-%m-%d") if dob else None
        )

        height = response.css(
            "div.fighter-data > div.bio-holder > table > tr > td > b[itemprop='height']::text"
        ).get()
        fighter_item["HEIGHT_INCHES"] = (
            convert_height(height.replace("'", "' ")) if height else None
        )

        fight_history_rows = response.css(
            "div.module.fight_history > div.new_table_holder > table.new_table.fighter > tr"
        )
        fighter_item["PRO_DEBUT_DATE"] = pd.to_datetime(
            fight_history_rows[-1].css("td > span.sub_line::text").get()
        ).strftime("%Y-%m-%d")

        yield fighter_item
