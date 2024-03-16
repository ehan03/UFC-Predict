# standard library imports

# third party imports
import pandas as pd
import w3lib.html
from scrapy.http import Request
from scrapy.spiders import Spider

# local imports
from src.scrapers.ufc_scrapy.items import (
    SherdogBoutItem,
    SherdogFighterBoutHistoryItem,
    SherdogFighterItem,
)
from src.scrapers.ufc_scrapy.utils import convert_height


class SherdogResultsSpider(Spider):
    """
    Spider for scraping historical fighter and bout data from Sherdog
    and FightMatrix
    """

    name = "sherdog_results_spider"
    allowed_domains = ["sherdog.com"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 4,
        "CONCURRENT_REQUESTS": 4,
        "COOKIES_ENABLED": False,
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
        "RETRY_TIMES": 5,
        "LOG_LEVEL": "INFO",
        "ITEM_PIPELINES": {
            "ufc_scrapy.scrapy_pipelines.sherdog_pipelines.SherdogFightersPipeline": 100,
            "ufc_scrapy.scrapy_pipelines.sherdog_pipelines.SherdogCompletedBoutsPipeline": 200,
            "ufc_scrapy.scrapy_pipelines.sherdog_pipelines.SherdogFighterBoutHistoryPipeline": 300,
        },
        "CLOSESPIDER_ERRORCOUNT": 1,
        "DOWNLOAD_TIMEOUT": 600,
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
        self.weight_class_map = {
            "Strawweight": 115,
            "Flyweight": 125,
            "Bantamweight": 135,
            "Featherweight": 145,
            "Lightweight": 155,
            "Welterweight": 170,
            "Middleweight": 185,
            "Light Heavyweight": 205,
            "Heavyweight": 265,
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
            main_event_bout_item["EVENT_ID"] = int(
                response.url.split("/")[-1].split("-")[-1]
            )
            main_event_bout_item["EVENT_NAME"] = event_name
            main_event_bout_item["DATE"] = date
            main_event_bout_item["LOCATION"] = location_city
            main_event_bout_item["VENUE"] = venue
            main_event_bout_item["FIGHTER_1_ID"] = int(
                main_event.css("div.fighter.left_side > a[itemprop='url']::attr(href)")
                .get()
                .split("/")[-1]
                .split("-")[-1]
            )
            fighter_urls.append(
                main_event.css(
                    "div.fighter.left_side > a[itemprop='url']::attr(href)"
                ).get()
            )
            main_event_bout_item["FIGHTER_2_ID"] = int(
                main_event.css("div.fighter.right_side > a[itemprop='url']::attr(href)")
                .get()
                .split("/")[-1]
                .split("-")[-1]
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
            main_event_bout_item["WEIGHT_CLASS"] = None
            main_event_bout_item["WEIGHT"] = None
            if main_event_weight_class:
                main_event_weight_class_name = main_event_weight_class.get().strip()
                if "lb" not in main_event_weight_class_name:
                    main_event_bout_item["WEIGHT_CLASS"] = main_event_weight_class_name
                    main_event_bout_item["WEIGHT"] = self.weight_class_map[
                        main_event_weight_class_name
                    ]
                else:
                    main_event_weight = int(
                        main_event_weight_class_name.split(" ")[0].replace("lb", "")
                    )
                    main_event_bout_item["WEIGHT_CLASS"] = "Catchweight"
                    main_event_bout_item["WEIGHT"] = main_event_weight

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

                bout_item["EVENT_ID"] = int(response.url.split("/")[-1].split("-")[-1])
                bout_item["EVENT_NAME"] = event_name
                bout_item["DATE"] = date
                bout_item["LOCATION"] = location_city
                bout_item["VENUE"] = venue

                tds = row.css("td")

                bout_item["BOUT_ORDINAL"] = (
                    int(w3lib.html.remove_tags(tds[0].get()).strip()) - 1
                )

                bout_item["FIGHTER_1_ID"] = int(
                    tds[1]
                    .css(
                        "div.fighter_list.left > div.fighter_result_data > a[itemprop='url']::attr(href)"
                    )
                    .get()
                    .split("/")[-1]
                    .split("-")[-1]
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

                weight_class = tds[2].css("span.weight_class::text")
                bout_item["WEIGHT_CLASS"] = None
                bout_item["WEIGHT"] = None
                if weight_class:
                    weight_class_name = weight_class.get().strip()
                    if "lb" not in weight_class_name:
                        bout_item["WEIGHT_CLASS"] = weight_class_name
                        bout_item["WEIGHT"] = self.weight_class_map[weight_class_name]
                    else:
                        weight = int(weight_class_name.split(" ")[0].replace("lb", ""))
                        bout_item["WEIGHT_CLASS"] = "Catchweight"
                        bout_item["WEIGHT"] = weight

                bout_item["FIGHTER_2_ID"] = int(
                    tds[3]
                    .css(
                        "div.fighter_list.right > div.fighter_result_data > a[itemprop='url']::attr(href)"
                    )
                    .get()
                    .split("/")[-1]
                    .split("-")[-1]
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

        fighter_id = int(response.url.split("/")[-1].split("-")[-1])
        fighter_item["FIGHTER_ID"] = fighter_id

        fighter_name = response.css(
            "div.fighter-line1 > h1[itemprop='name'] > span.fn::text"
        ).get()
        fighter_item["FIGHTER_NAME"] = fighter_name

        nick = response.css("div.fighter-line2 > h1[itemprop='name'] > span.nickname")
        fighter_item["FIGHTER_NICKNAME"] = nick.css("em::text").get() if nick else None
        fighter_item["NATIONALITY"] = response.css(
            """div.fighter-nationality > span.item.birthplace > 
            strong[itemprop='nationality']::text"""
        ).get()

        dob = response.css(
            """div.fighter-data > div.bio-holder > table > tr > 
            td > span[itemprop='birthDate']::text"""
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

        pro_fight_history_table = response.css(
            "div.module.fight_history > div.new_table_holder > table.new_table.fighter"
        )[0]
        fight_history_rows = pro_fight_history_table.css("tr:not([class='table_head'])")
        pro_debut_date = pd.to_datetime(
            fight_history_rows[-1].css("td > span.sub_line::text").get()
        ).strftime("%Y-%m-%d")
        fighter_item["PRO_DEBUT_DATE"] = pro_debut_date

        yield fighter_item

        for fighter_bout_ordinal, row in enumerate(reversed(fight_history_rows)):
            fighter_bout_history_item = SherdogFighterBoutHistoryItem()

            fighter_bout_history_item["FIGHTER_ID"] = fighter_id
            fighter_bout_history_item["FIGHTER_BOUT_ORDINAL"] = fighter_bout_ordinal

            tds = row.css("td")

            fighter_bout_history_item["OUTCOME"] = self.outcome_map[
                tds[0].css("span.final_result::text").get().lower()
            ]
            fighter_bout_history_item["OPPONENT_ID"] = (
                int(tds[1].css("a::attr(href)").get().split("/")[-1].split("-")[-1])
                if tds[1].css("a::attr(href)").get().split("/")[-1].split("-")[-1]
                != "javascript:void();"
                else None
            )
            fighter_bout_history_item["OPPONENT_NAME"] = (
                tds[1].css("a::text").get()
                if tds[1].css("a::text").get() != "Unknown Fighter"
                else None
            )
            fighter_bout_history_item["EVENT_ID"] = int(
                tds[2].css("a::attr(href)").get().split("/")[-1].split("-")[-1]
            )
            fighter_bout_history_item["EVENT_NAME"] = w3lib.html.remove_tags(
                tds[2].css("a").get()
            )
            fighter_bout_history_item["DATE"] = pd.to_datetime(
                tds[2].css("span.sub_line::text").get()
            ).strftime("%Y-%m-%d")

            outcome_method = tds[3].css("b::text").get()
            fighter_bout_history_item["OUTCOME_METHOD"] = (
                outcome_method if outcome_method and outcome_method != "N/A" else None
            )

            end_round = int(tds[4].css("::text").get().strip())
            fighter_bout_history_item["END_ROUND"] = (
                end_round if end_round != 0 else None
            )

            end_round_time = tds[5].css("::text").get().strip()
            end_round_time_split = (
                end_round_time.split(":")
                if end_round_time not in ["N/A", "M/A"]
                else None
            )

            if end_round_time_split is not None and len(end_round_time_split) == 1:
                end_round_time_split = [end_round_time_split[0], "00"]
            elif end_round_time_split is not None and end_round_time_split[0] == "":
                end_round_time_split = ["00", end_round_time_split[1]]

            end_round_time_seconds = (
                60 * int(end_round_time_split[0]) + int(end_round_time_split[1])
                if end_round_time_split is not None
                else None
            )
            fighter_bout_history_item["END_ROUND_TIME_SECONDS"] = end_round_time_seconds
            fighter_bout_history_item["TOTAL_TIME_SECONDS"] = (
                (300 * (end_round - 1) + end_round_time_seconds)
                if end_round_time_seconds is not None and end_round != 0
                else None
            )

            yield fighter_bout_history_item
