"""
This module contains all the spiders for scraping UFC data.
"""

# standard library imports
import re
import time
from ast import literal_eval
from html import unescape
from urllib.parse import parse_qs, urlparse

# third party imports
import pandas as pd
import w3lib.html
from scrapy.http import FormRequest, Request
from scrapy.spiders import Spider

# local imports
from src.scrapers.ufc_scrapy.items import (
    FightMatrixFighterItem,
    FightMatrixRankingItem,
    TapologyBoutItem,
    TapologyFighterItem,
    UFCStatsBoutOverallItem,
    UFCStatsBoutRoundItem,
    UFCStatsFighterItem,
)
from src.scrapers.ufc_scrapy.utils import (
    convert_height,
    ctrl_time,
    extract_landed_attempted,
    total_time,
)


class UFCStatsSpider(Spider):
    """
    Spider for scraping UFC bout and fighter data from UFCStats
    """

    name = "ufcstats_spider"
    allowed_domains = ["ufcstats.com"]
    start_urls = [
        "http://ufcstats.com/statistics/events/completed?page=all",
    ]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 10,
        "CONCURRENT_REQUESTS": 10,
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
        # "LOG_LEVEL": "INFO",
        "LOG_LEVEL": "DEBUG",
        "ITEM_PIPELINES": {
            # "ufc_scrapy.pipelines.UFCStatsFightersPipeline": 100,
            # "ufc_scrapy.pipelines.UFCStatsBoutsPipeline": 100,
        },
        "CLOSESPIDER_ERRORCOUNT": 1,
    }

    def __init__(self, *args, scrape_type, **kwargs):
        super().__init__(*args, **kwargs)
        assert scrape_type in {"all", "most_recent"}
        self.scrape_type = scrape_type

    def parse(self, response):
        event_urls = ["http://ufcstats.com/event-details/6420efac0578988b"]
        event_urls.extend(
            reversed(
                response.css(
                    """tr.b-statistics__table-row >
                td.b-statistics__table-col >
                i.b-statistics__table-content >
                a.b-link.b-link_style_black::attr(href)"""
                ).getall()
            )
        )

        if self.scrape_type == "most_recent":
            event_urls = [event_urls[-1]]

        yield from response.follow_all(event_urls, self.parse_event)

    def parse_event(self, response):
        bout_urls = response.css(
            """tr.b-fight-details__table-row.b-fight-details__table-row__hover.js-fight-details-click > 
            td.b-fight-details__table-col.b-fight-details__table-col_style_align-top >
            p.b-fight-details__table-text > 
            a.b-flag::attr(href)"""
        ).getall()

        # Event metadata we can grab up front
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

        # Preserve order of bouts
        for bout_ordinal, bout_url in enumerate(reversed(bout_urls)):
            # Overall stats
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

        fighter_urls = response.css(
            """td[style='width:100px'].b-fight-details__table-col.l-page_align_left >
            p.b-fight-details__table-text >
            a.b-link.b-link_style_black::attr(href)
            """
        ).getall()

        yield from response.follow_all(fighter_urls, self.parse_fighter)

    def parse_fighter(self, response):
        fighter_item = UFCStatsFighterItem()

        # Get all relevant fields
        fighter_item["FIGHTER_ID"] = response.url.split("/")[-1]
        fighter_item["FIGHTER_NAME"] = (
            response.css("span.b-content__title-highlight::text").get().strip()
        )

        info = [
            x.strip()
            for i, x in enumerate(
                response.css(
                    "li.b-list__box-list-item.b-list__box-list-item_type_block::text"
                ).getall()
            )
            if (i % 2 == 1 and i != 19)
        ]
        fighter_item["HEIGHT_INCHES"] = convert_height(info[0])
        fighter_item["REACH_INCHES"] = (
            float(info[2].replace('"', "")) if info[2] != "--" else None
        )
        fighter_item["FIGHTING_STANCE"] = info[3] if info[3] else None
        fighter_item["DATE_OF_BIRTH"] = (
            pd.to_datetime(info[4]).strftime("%Y-%m-%d") if info[4] != "--" else None
        )

        yield fighter_item

    def parse_bout(
        self,
        response,
        event_id,
        event_name,
        date,
        location,
        bout_ordinal,
    ):
        bout_overall_item = UFCStatsBoutOverallItem()

        bout_overall_item["BOUT_ID"] = response.url.split("/")[-1]

        bout_overall_item["EVENT_ID"] = event_id
        bout_overall_item["EVENT_NAME"] = event_name
        bout_overall_item["DATE"] = pd.to_datetime(date).strftime("%Y-%m-%d")
        bout_overall_item["LOCATION"] = location
        bout_overall_item["BOUT_ORDINAL"] = bout_ordinal

        # Get all relevant fields
        fighter_urls = response.css(
            "a.b-link.b-fight-details__person-link::attr(href)"
        ).getall()
        bout_overall_item["RED_FIGHTER_ID"] = fighter_urls[0].split("/")[-1]
        bout_overall_item["BLUE_FIGHTER_ID"] = fighter_urls[1].split("/")[-1]

        outcomes = response.css("i.b-fight-details__person-status::text").getall()
        bout_overall_item["RED_OUTCOME"] = outcomes[0].strip()
        bout_overall_item["BLUE_OUTCOME"] = outcomes[1].strip()

        bout_overall_item["BOUT_TYPE"] = [
            x.strip()
            for x in response.css("i.b-fight-details__fight-title::text").getall()
            if x.strip()
        ][0]

        bonus_img_src = response.css(
            "i.b-fight-details__fight-title > img::attr(src)"
        ).getall()
        if bonus_img_src:
            bonus_img_names = [x.split("/")[-1] for x in bonus_img_src]
            if "perf.png" in bonus_img_names:
                bout_overall_item["BOUT_PERF_BONUS"] = 1
            else:
                bout_overall_item["BOUT_PERF_BONUS"] = 0
        else:
            bout_overall_item["BOUT_PERF_BONUS"] = 0

        method_info = response.css("i.b-fight-details__text-item_first").getall()
        bout_overall_item["OUTCOME_METHOD"] = (
            w3lib.html.remove_tags(method_info[0]).replace("Method:", "").strip()
        )

        details = response.css("p.b-fight-details__text").getall()
        bout_overall_item["OUTCOME_METHOD_DETAILS"] = " ".join(
            w3lib.html.remove_tags(details[1]).replace("Details:", "").strip().split()
        )

        time_format_info = response.css("i.b-fight-details__text-item").getall()
        bout_overall_item["END_ROUND"] = int(
            w3lib.html.remove_tags(time_format_info[0]).replace("Round:", "").strip()
        )
        end_round_time_split = (
            w3lib.html.remove_tags(time_format_info[1])
            .replace("Time:", "")
            .strip()
            .split(":")
        )
        bout_overall_item["END_ROUND_TIME_SECONDS"] = int(
            end_round_time_split[0]
        ) * 60 + int(end_round_time_split[1])
        bout_overall_item["BOUT_TIME_FORMAT"] = (
            w3lib.html.remove_tags(time_format_info[2])
            .replace("Time format:", "")
            .strip()
        )
        bout_overall_item["TOTAL_TIME_SECONDS"] = total_time(
            bout_overall_item["BOUT_TIME_FORMAT"],
            bout_overall_item["END_ROUND"],
            bout_overall_item["END_ROUND_TIME_SECONDS"],
        )

        # Stats tables
        # Initialize all stats to None
        non_fight_table_fields = {
            "BOUT_ID",
            "EVENT_ID",
            "EVENT_NAME",
            "EVENT_IS_UFC",
            "DATE",
            "LOCATION",
            "BOUT_ORDINAL",
            "RED_FIGHTER_ID",
            "BLUE_FIGHTER_ID",
            "RED_OUTCOME",
            "BLUE_OUTCOME",
            "BOUT_TYPE",
            "BOUT_BONUS",
            "OUTCOME_METHOD",
            "OUTCOME_METHOD_DETAILS",
            "END_ROUND",
            "END_ROUND_TIME_SECONDS",
            "BOUT_TIME_FORMAT",
            "TOTAL_TIME_SECONDS",
        }
        for key in UFCStatsBoutOverallItem.fields.keys() - non_fight_table_fields:
            bout_overall_item[key] = None

        tables = response.css("tbody.b-fight-details__table-body")
        if tables:
            assert len(tables) == 4

            # Overall
            stats = [
                x.strip()
                for x in tables[0].css("p.b-fight-details__table-text::text").getall()
            ]
            bout_overall_item["RED_KNOCKDOWNS"] = int(stats[4])
            bout_overall_item["BLUE_KNOCKDOWNS"] = int(stats[5])
            (
                bout_overall_item["RED_TOTAL_STRIKES_LANDED"],
                bout_overall_item["RED_TOTAL_STRIKES_ATTEMPTED"],
            ) = extract_landed_attempted(stats[10])
            (
                bout_overall_item["BLUE_TOTAL_STRIKES_LANDED"],
                bout_overall_item["BLUE_TOTAL_STRIKES_ATTEMPTED"],
            ) = extract_landed_attempted(stats[11])
            (
                bout_overall_item["RED_TAKEDOWNS_LANDED"],
                bout_overall_item["RED_TAKEDOWNS_ATTEMPTED"],
            ) = extract_landed_attempted(stats[12])
            (
                bout_overall_item["BLUE_TAKEDOWNS_LANDED"],
                bout_overall_item["BLUE_TAKEDOWNS_ATTEMPTED"],
            ) = extract_landed_attempted(stats[13])
            bout_overall_item["RED_SUBMISSION_ATTEMPTS"] = int(stats[16])
            bout_overall_item["BLUE_SUBMISSION_ATTEMPTS"] = int(stats[17])
            bout_overall_item["RED_REVERSALS"] = int(stats[18])
            bout_overall_item["BLUE_REVERSALS"] = int(stats[19])
            bout_overall_item["RED_CONTROL_TIME_SECONDS"] = ctrl_time(stats[20])
            bout_overall_item["BLUE_CONTROL_TIME_SECONDS"] = ctrl_time(stats[21])

            sig_stats = [
                x.strip()
                for x in tables[2].css("p.b-fight-details__table-text::text").getall()
            ]
            (
                bout_overall_item["RED_SIGNIFICANT_STRIKES_LANDED"],
                bout_overall_item["RED_SIGNIFICANT_STRIKES_ATTEMPTED"],
            ) = extract_landed_attempted(sig_stats[4])
            (
                bout_overall_item["BLUE_SIGNIFICANT_STRIKES_LANDED"],
                bout_overall_item["BLUE_SIGNIFICANT_STRIKES_ATTEMPTED"],
            ) = extract_landed_attempted(sig_stats[5])
            (
                bout_overall_item["RED_SIGNIFICANT_STRIKES_HEAD_LANDED"],
                bout_overall_item["RED_SIGNIFICANT_STRIKES_HEAD_ATTEMPTED"],
            ) = extract_landed_attempted(sig_stats[8])
            (
                bout_overall_item["BLUE_SIGNIFICANT_STRIKES_HEAD_LANDED"],
                bout_overall_item["BLUE_SIGNIFICANT_STRIKES_HEAD_ATTEMPTED"],
            ) = extract_landed_attempted(sig_stats[9])
            (
                bout_overall_item["RED_SIGNIFICANT_STRIKES_BODY_LANDED"],
                bout_overall_item["RED_SIGNIFICANT_STRIKES_BODY_ATTEMPTED"],
            ) = extract_landed_attempted(sig_stats[10])
            (
                bout_overall_item["BLUE_SIGNIFICANT_STRIKES_BODY_LANDED"],
                bout_overall_item["BLUE_SIGNIFICANT_STRIKES_BODY_ATTEMPTED"],
            ) = extract_landed_attempted(sig_stats[11])
            (
                bout_overall_item["RED_SIGNIFICANT_STRIKES_LEG_LANDED"],
                bout_overall_item["RED_SIGNIFICANT_STRIKES_LEG_ATTEMPTED"],
            ) = extract_landed_attempted(sig_stats[12])
            (
                bout_overall_item["BLUE_SIGNIFICANT_STRIKES_LEG_LANDED"],
                bout_overall_item["BLUE_SIGNIFICANT_STRIKES_LEG_ATTEMPTED"],
            ) = extract_landed_attempted(sig_stats[13])
            (
                bout_overall_item["RED_SIGNIFICANT_STRIKES_DISTANCE_LANDED"],
                bout_overall_item["RED_SIGNIFICANT_STRIKES_DISTANCE_ATTEMPTED"],
            ) = extract_landed_attempted(sig_stats[14])
            (
                bout_overall_item["BLUE_SIGNIFICANT_STRIKES_DISTANCE_LANDED"],
                bout_overall_item["BLUE_SIGNIFICANT_STRIKES_DISTANCE_ATTEMPTED"],
            ) = extract_landed_attempted(sig_stats[15])
            (
                bout_overall_item["RED_SIGNIFICANT_STRIKES_CLINCH_LANDED"],
                bout_overall_item["RED_SIGNIFICANT_STRIKES_CLINCH_ATTEMPTED"],
            ) = extract_landed_attempted(sig_stats[16])
            (
                bout_overall_item["BLUE_SIGNIFICANT_STRIKES_CLINCH_LANDED"],
                bout_overall_item["BLUE_SIGNIFICANT_STRIKES_CLINCH_ATTEMPTED"],
            ) = extract_landed_attempted(sig_stats[17])
            (
                bout_overall_item["RED_SIGNIFICANT_STRIKES_GROUND_LANDED"],
                bout_overall_item["RED_SIGNIFICANT_STRIKES_GROUND_ATTEMPTED"],
            ) = extract_landed_attempted(sig_stats[18])
            (
                bout_overall_item["BLUE_SIGNIFICANT_STRIKES_GROUND_LANDED"],
                bout_overall_item["BLUE_SIGNIFICANT_STRIKES_GROUND_ATTEMPTED"],
            ) = extract_landed_attempted(sig_stats[19])

            # Round by round
            stats_by_round_rows = tables[1].css("tr.b-fight-details__table-row")
            sig_stats_by_round_rows = tables[3].css("tr.b-fight-details__table-row")

            assert len(stats_by_round_rows) == len(sig_stats_by_round_rows)

            for i in range(len(stats_by_round_rows)):
                bout_round_item = UFCStatsBoutRoundItem()

                bout_round_item["BOUT_ID"] = bout_overall_item["BOUT_ID"]
                bout_round_item["EVENT_ID"] = bout_overall_item["EVENT_ID"]
                bout_round_item["DATE"] = bout_overall_item["DATE"]
                bout_round_item["BOUT_ORDINAL"] = bout_overall_item["BOUT_ORDINAL"]
                bout_round_item["ROUND"] = i + 1
                bout_round_item["BOUT_ROUND_ID"] = (
                    bout_round_item["BOUT_ID"] + "_" + str(bout_round_item["ROUND"])
                )

                stats_for_round = [
                    x.strip()
                    for x in stats_by_round_rows[i]
                    .css("p.b-fight-details__table-text::text")
                    .getall()
                ]
                bout_round_item["RED_KNOCKDOWNS"] = int(stats_for_round[4])
                bout_round_item["BLUE_KNOCKDOWNS"] = int(stats_for_round[5])
                (
                    bout_round_item["RED_TOTAL_STRIKES_LANDED"],
                    bout_round_item["RED_TOTAL_STRIKES_ATTEMPTED"],
                ) = extract_landed_attempted(stats_for_round[10])
                (
                    bout_round_item["BLUE_TOTAL_STRIKES_LANDED"],
                    bout_round_item["BLUE_TOTAL_STRIKES_ATTEMPTED"],
                ) = extract_landed_attempted(stats_for_round[11])
                (
                    bout_round_item["RED_TAKEDOWNS_LANDED"],
                    bout_round_item["RED_TAKEDOWNS_ATTEMPTED"],
                ) = extract_landed_attempted(stats_for_round[12])
                (
                    bout_round_item["BLUE_TAKEDOWNS_LANDED"],
                    bout_round_item["BLUE_TAKEDOWNS_ATTEMPTED"],
                ) = extract_landed_attempted(stats_for_round[13])
                bout_round_item["RED_SUBMISSION_ATTEMPTS"] = int(stats_for_round[16])
                bout_round_item["BLUE_SUBMISSION_ATTEMPTS"] = int(stats_for_round[17])
                bout_round_item["RED_REVERSALS"] = int(stats_for_round[18])
                bout_round_item["BLUE_REVERSALS"] = int(stats_for_round[19])
                bout_round_item["RED_CONTROL_TIME_SECONDS"] = ctrl_time(
                    stats_for_round[20]
                )
                bout_round_item["BLUE_CONTROL_TIME_SECONDS"] = ctrl_time(
                    stats_for_round[21]
                )

                sig_stats_for_round = [
                    x.strip()
                    for x in sig_stats_by_round_rows[i]
                    .css("p.b-fight-details__table-text::text")
                    .getall()
                ]
                (
                    bout_round_item["RED_SIGNIFICANT_STRIKES_LANDED"],
                    bout_round_item["RED_SIGNIFICANT_STRIKES_ATTEMPTED"],
                ) = extract_landed_attempted(sig_stats_for_round[4])
                (
                    bout_round_item["BLUE_SIGNIFICANT_STRIKES_LANDED"],
                    bout_round_item["BLUE_SIGNIFICANT_STRIKES_ATTEMPTED"],
                ) = extract_landed_attempted(sig_stats_for_round[5])
                (
                    bout_round_item["RED_SIGNIFICANT_STRIKES_HEAD_LANDED"],
                    bout_round_item["RED_SIGNIFICANT_STRIKES_HEAD_ATTEMPTED"],
                ) = extract_landed_attempted(sig_stats_for_round[8])
                (
                    bout_round_item["BLUE_SIGNIFICANT_STRIKES_HEAD_LANDED"],
                    bout_round_item["BLUE_SIGNIFICANT_STRIKES_HEAD_ATTEMPTED"],
                ) = extract_landed_attempted(sig_stats_for_round[9])
                (
                    bout_round_item["RED_SIGNIFICANT_STRIKES_BODY_LANDED"],
                    bout_round_item["RED_SIGNIFICANT_STRIKES_BODY_ATTEMPTED"],
                ) = extract_landed_attempted(sig_stats_for_round[10])
                (
                    bout_round_item["BLUE_SIGNIFICANT_STRIKES_BODY_LANDED"],
                    bout_round_item["BLUE_SIGNIFICANT_STRIKES_BODY_ATTEMPTED"],
                ) = extract_landed_attempted(sig_stats_for_round[11])
                (
                    bout_round_item["RED_SIGNIFICANT_STRIKES_LEG_LANDED"],
                    bout_round_item["RED_SIGNIFICANT_STRIKES_LEG_ATTEMPTED"],
                ) = extract_landed_attempted(sig_stats_for_round[12])
                (
                    bout_round_item["BLUE_SIGNIFICANT_STRIKES_LEG_LANDED"],
                    bout_round_item["BLUE_SIGNIFICANT_STRIKES_LEG_ATTEMPTED"],
                ) = extract_landed_attempted(sig_stats_for_round[13])
                (
                    bout_round_item["RED_SIGNIFICANT_STRIKES_DISTANCE_LANDED"],
                    bout_round_item["RED_SIGNIFICANT_STRIKES_DISTANCE_ATTEMPTED"],
                ) = extract_landed_attempted(sig_stats_for_round[14])
                (
                    bout_round_item["BLUE_SIGNIFICANT_STRIKES_DISTANCE_LANDED"],
                    bout_round_item["BLUE_SIGNIFICANT_STRIKES_DISTANCE_ATTEMPTED"],
                ) = extract_landed_attempted(sig_stats_for_round[15])
                (
                    bout_round_item["RED_SIGNIFICANT_STRIKES_CLINCH_LANDED"],
                    bout_round_item["RED_SIGNIFICANT_STRIKES_CLINCH_ATTEMPTED"],
                ) = extract_landed_attempted(sig_stats_for_round[16])
                (
                    bout_round_item["BLUE_SIGNIFICANT_STRIKES_CLINCH_LANDED"],
                    bout_round_item["BLUE_SIGNIFICANT_STRIKES_CLINCH_ATTEMPTED"],
                ) = extract_landed_attempted(sig_stats_for_round[17])
                (
                    bout_round_item["RED_SIGNIFICANT_STRIKES_GROUND_LANDED"],
                    bout_round_item["RED_SIGNIFICANT_STRIKES_GROUND_ATTEMPTED"],
                ) = extract_landed_attempted(sig_stats_for_round[18])
                (
                    bout_round_item["BLUE_SIGNIFICANT_STRIKES_GROUND_LANDED"],
                    bout_round_item["BLUE_SIGNIFICANT_STRIKES_GROUND_ATTEMPTED"],
                ) = extract_landed_attempted(sig_stats_for_round[19])

                yield bout_round_item

        yield bout_overall_item


class TapologySpider(Spider):
    """
    Spider for scraping UFC bout and fighter data from Tapology
    """

    name = "tapology_spider"
    allowed_domains = ["tapology.com"]
    start_urls = [
        "https://www.tapology.com/fightcenter?group=ufc&schedule=results&sport=mma"
    ]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_DELAY": 10,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "DOWNLOAD_TIMEOUT": 600,
        "CONCURRENT_REQUESTS": 1,
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
            "ufc_scrapy.pipelines.TapologyBoutsPipeline": 100,
        },
        "CLOSESPIDER_ERRORCOUNT": 1,
    }

    def __init__(self, *args, scrape_type, **kwargs):
        """
        Initialize TapologySpider
        """

        super().__init__(*args, **kwargs)
        assert scrape_type == "most_recent" or scrape_type.startswith("page_")
        self.scrape_type = scrape_type

    def parse(self, response):
        event_listings = response.css("section.fcListing > div.main > div.left")
        event_urls = []
        for event_listing in event_listings:
            event_urls.append(
                response.urljoin(
                    event_listing.css("div.promotion > span.name > a::attr(href)").get()
                )
            )

        if "page_" in self.scrape_type:
            page_num = int(self.scrape_type.split("_")[1])
            assert page_num > 0

            if page_num == 1:
                for event_url in event_urls:
                    yield response.follow(
                        event_url,
                        callback=self.parse_event,
                    )
            else:
                parsed_url = urlparse(response.url)

                try:
                    current_page = int(parse_qs(parsed_url.query)["page"][0])
                except:
                    current_page = 1

                if current_page == page_num:
                    for event_url in event_urls:
                        yield response.follow(
                            event_url,
                            callback=self.parse_event,
                        )
                else:
                    # Workaround for terrible Ajax pagination, part 1
                    pagination_headers = {
                        "X-Requested-With": "XMLHttpRequest",
                        "Accept": """*/*;q=0.5, text/javascript, application/javascript,
                                    application/ecmascript, application/x-ecmascript""",
                    }
                    next_page = response.css("span.next > a::attr(href)")
                    next_page_url = [response.urljoin(url.get()) for url in next_page]
                    if next_page_url:
                        yield FormRequest(
                            url=next_page_url[0],
                            method="GET",
                            headers=pagination_headers,
                            callback=self.parse_next_page,
                        )
        else:
            yield response.follow(
                event_urls[0],
                callback=self.parse_event,
            )

    def parse_next_page(self, response):
        # Workaround, part 2
        data = response.text
        data = re.search(r"html\((.*)\);", data)
        assert data is not None
        data = data.group(1)  # type: ignore
        data = unescape(literal_eval(data)).replace(r"\/", "/")

        yield from self.parse(response.replace(body=data))  # type: ignore

    def parse_event(self, response):
        bouts = response.css(
            "div.fightCardMatchup > table > tr > td > span.billing > a::attr(href)"
        )
        bout_urls = [response.urljoin(url.get()) for url in bouts]

        event_id = response.url.split("/")[-1]
        event_name = response.css("div.eventPageHeaderTitles > h1::text").get().strip()
        event_info_list = [
            w3lib.html.remove_tags(x).strip()
            for x in response.css(
                "div.details.details_with_poster.clearfix > div.right > ul.clearfix > li"
            ).getall()
        ]
        region = response.css(
            "div.regionFCSidebar > div.iconLead > div.textContents > div.leader > a::text"
        ).get()

        date = location = venue = None
        for i, info in enumerate(event_info_list):
            if i == 0:
                raw_date = info.split(" ")[1]
                date = pd.to_datetime(raw_date).strftime("%Y-%m-%d")
            elif info.startswith("Location:"):
                location_raw = info.replace("Location:", "").strip()
                if location_raw:
                    location = location_raw
            elif info.startswith("Venue:"):
                venue_raw = info.replace("Venue:", "").strip()
                if venue_raw:
                    venue = venue_raw

        event_and_promo_links = response.css(
            "div.details.details_with_poster.clearfix > div.right > ul.clearfix > li > div.externalIconsHolder > a::attr(href)"
        ).getall()
        ufcstats_event_id = None
        for link in event_and_promo_links:
            if "www.ufcstats.com/event-details/" in link:
                ufcstats_event_id = link.split("/")[-1]
                break
        assert ufcstats_event_id is not None

        for bout_ordinal, bout_url in enumerate(reversed(bout_urls)):
            yield response.follow(
                bout_url,
                callback=self.parse_bout,
                cb_kwargs={
                    "event_id": event_id,
                    "ufcstats_event_id": ufcstats_event_id,
                    "event_name": event_name,
                    "date": date,
                    "region": region,
                    "location": location,
                    "venue": venue,
                    "bout_ordinal": bout_ordinal,
                },
            )

    def parse_bout(
        self,
        response,
        event_id,
        ufcstats_event_id,
        event_name,
        date,
        region,
        location,
        venue,
        bout_ordinal,
    ):
        bout_item = TapologyBoutItem()
        bout_id = response.url.split("/")[-1]

        bout_item["BOUT_ID"] = bout_id
        bout_item["EVENT_ID"] = event_id
        bout_item["EVENT_NAME"] = event_name
        bout_item["DATE"] = date
        bout_item["REGION"] = region
        bout_item["LOCATION"] = location
        bout_item["VENUE"] = venue
        bout_item["BOUT_ORDINAL"] = bout_ordinal

        bout_item["UFCSTATS_EVENT_ID"] = ufcstats_event_id

        bout_and_event_links = response.css(
            "div.details.details_with_poster.clearfix > div.right > ul.clearfix > li > div.externalIconsHolder > a::attr(href)"
        ).getall()
        ufcstats_bout_id = None
        for link in bout_and_event_links:
            if link.startswith("http://www.ufcstats.com/fight-details/"):
                ufcstats_bout_id = link.split("/")[-1]
                break
        assert ufcstats_bout_id is not None

        bout_item["UFCSTATS_BOUT_ID"] = ufcstats_bout_id

        bout_preresult = (
            response.css("h4.boutPreResult::text").get().split(" | ")[0].strip()
        )
        if bout_preresult == "Preliminary Card":
            bout_item["BOUT_CARD_TYPE"] = "Prelim"
        else:
            bout_item["BOUT_CARD_TYPE"] = "Main"

        # Fighter info
        f1_url = response.css("span.fName.left > a::attr(href)").get()
        f2_url = response.css("span.fName.right > a::attr(href)").get()

        bout_item["FIGHTER_1_ID"] = f1_url.split("/")[-1]
        bout_item["FIGHTER_2_ID"] = f2_url.split("/")[-1]

        stats_table_rows = response.css("table.fighterStats.spaced > tr")
        for row in stats_table_rows:
            values = row.css("td").getall()
            assert len(values) == 5
            f1_stat = w3lib.html.remove_tags(values[0]).strip()
            stat_category = w3lib.html.remove_tags(values[2]).strip()
            f2_stat = w3lib.html.remove_tags(values[4]).strip()

            if stat_category == "Pro Record At Fight":
                bout_item["FIGHTER_1_RECORD_AT_BOUT"] = f1_stat if f1_stat else None
                bout_item["FIGHTER_2_RECORD_AT_BOUT"] = f2_stat if f2_stat else None
            elif stat_category == "Weigh-In Result":
                bout_item["FIGHTER_1_WEIGHT_POUNDS"] = (
                    float(f1_stat.split(" ")[0])
                    if (f1_stat and f1_stat != "N/A")
                    else None
                )
                bout_item["FIGHTER_2_WEIGHT_POUNDS"] = (
                    float(f2_stat.split(" ")[0])
                    if (f2_stat and f2_stat != "N/A")
                    else None
                )
            elif stat_category == "Gym":
                if f1_stat:
                    f1_gym_list = f1_stat.split("\n\n")
                    if len(f1_gym_list) > 1:
                        f1_possible_gyms = []
                        f1_flag = False
                        for f1_gym in f1_gym_list:
                            if "(Primary)" in f1_gym:
                                bout_item["FIGHTER_1_GYM"] = f1_gym.replace(
                                    "(Primary)", ""
                                ).strip()
                                f1_flag = True
                                break

                            if "(Other)" in f1_gym:
                                continue
                            f1_possible_gyms.append(f1_gym)

                        if f1_possible_gyms and not f1_flag:
                            bout_item["FIGHTER_1_GYM"] = (
                                f1_possible_gyms[-1].split("(")[0].strip()
                            )
                    else:
                        bout_item["FIGHTER_1_GYM"] = f1_gym_list[0]
                else:
                    bout_item["FIGHTER_1_GYM"] = None

                if f2_stat:
                    f2_gym_list = f2_stat.split("\n\n")
                    f2_flag = False
                    if len(f2_gym_list) > 1:
                        f2_possible_gyms = []
                        for f2_gym in f2_gym_list:
                            if "(Primary)" in f2_gym:
                                bout_item["FIGHTER_2_GYM"] = f2_gym.replace(
                                    "(Primary)", ""
                                ).strip()
                                f2_flag = True
                                break

                            if "(Other)" in f2_gym:
                                continue
                            f2_possible_gyms.append(f2_gym)

                        if f2_possible_gyms and not f2_flag:
                            bout_item["FIGHTER_2_GYM"] = (
                                f2_possible_gyms[-1].split("(")[0].strip()
                            )
                    else:
                        bout_item["FIGHTER_2_GYM"] = f2_gym_list[0]
                else:
                    bout_item["FIGHTER_2_GYM"] = None

        yield bout_item

        fighter_urls = [response.urljoin(f1_url), response.urljoin(f2_url)]
        for fighter_url in fighter_urls:
            yield response.follow(
                fighter_url,
                callback=self.parse_fighter,
            )

    def parse_fighter(self, response):
        fighter_item = TapologyFighterItem()

        fighter_item["FIGHTER_ID"] = response.url.split("/")[-1]
        fighter_item["FIGHTER_NAME"] = (
            response.css("div.fighterUpcomingHeader > h1::text").getall()[-1].strip()
        )
        fighter_item["NATIONALITY"] = (
            response.css("div.fighterUpcomingHeader > h2#flag > a::attr(title)")
            .get()
            .replace("See all ", "")
            .replace(" Fighters", "")
            .strip()
        )

        details = [
            w3lib.html.remove_tags(x).strip()
            for x in response.css(
                "div.details.details_two_columns > ul.clearfix > li"
            ).getall()
        ]
        for detail in details:
            if detail.startswith("Age:"):
                dob = detail.split("| ")[1].replace("Date of Birth:", "").strip()
                fighter_item["DATE_OF_BIRTH"] = (
                    pd.to_datetime(dob).strftime("%Y-%m-%d") if dob != "N/A" else None
                )
            elif detail.startswith("Height:"):
                height, reach = detail.split("| ")
                height = height.replace("Height:", "").split(" (")[0].strip()
                reach = reach.replace("Reach:", "").split(" (")[0].strip()
                fighter_item["HEIGHT_INCHES"] = (
                    convert_height(height.replace("'", "' "))
                    if height != "N/A"
                    else None
                )
                fighter_item["REACH_INCHES"] = (
                    float(reach.replace('"', "")) if reach != "N/A" else None
                )

        fighter_links = response.css(
            "div.details.details_two_columns > ul.clearfix > li > div.externalIconsHolder > a::attr(href)"
        ).getall()
        ufcstats_fighter_id = sherdog_fighter_id = None
        for link in fighter_links:
            if "www.ufcstats.com/fighter-details/" in link:
                ufcstats_fighter_id = link.split("/")[-1]
            elif "www.sherdog.com/fighter/" in link:
                sherdog_fighter_id = link.split("/")[-1]
        fighter_item["UFCSTATS_FIGHTER_ID"] = ufcstats_fighter_id
        fighter_item["SHERDOG_FIGHTER_ID"] = sherdog_fighter_id

        yield fighter_item


class FightMatrixSpider(Spider):
    """
    Spider for scraping data from FightMatrix
    """

    name = "fightmatrix_spider"
    allowed_domains = ["fightmatrix.com"]
    start_urls = [
        "https://www.fightmatrix.com/historical-mma-rankings/ranking-snapshots/"
    ]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 10,
        "CONCURRENT_REQUESTS": 10,
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
            #
        },
        "CLOSESPIDER_ERRORCOUNT": 1,
    }

    def __init__(self, *args, scrape_type, **kwargs):
        """
        Initialize FightMatrixSpider
        """

        super().__init__(*args, **kwargs)
        assert scrape_type in {"most_recent", "all"}
        self.scrape_type = scrape_type
        self.weight_class_map = {
            "1": "Heavyweight",
            "2": "Light Heavyweight",
            "3": "Middleweight",
            "4": "Welterweight",
            "5": "Lightweight",
            "6": "Featherweight",
            "7": "Bantamweight",
            "8": "Flyweight",
            "16": "Women's Featherweight",
            "15": "Women's Bantamweight",
            "14": "Women's Flyweight",
            "13": "Women's Strawweight",
        }

    def parse(self, response):
        filtertable_td = response.css("table#filterTable *> td")
        issues = filtertable_td[0].css("option::attr(value)").getall()[1:]
        dates = filtertable_td[0].css("option::text").getall()[1:]
        dates = [pd.to_datetime(x).strftime("%Y-%m-%d") for x in dates]
        assert len(issues) == len(dates)

        if self.scrape_type == "most_recent":
            issues = [issues[0]]
            dates = [dates[0]]

        for issue, date in zip(issues, dates):
            for division, weight_class in self.weight_class_map.items():
                if time.strptime(date, "%Y-%m-%d") < time.strptime(
                    "2010-03-01", "%Y-%m-%d"
                ):
                    # UFCStats data is useless before 2010 (no red/blue distinction)
                    break

                if time.strptime(date, "%Y-%m-%d") < time.strptime(
                    "2013-02-01", "%Y-%m-%d"
                ) and division in {"16", "15", "14", "13"}:
                    # Women's divisions didn't exist before 2013 in the UFC
                    continue

                yield response.follow(
                    f"https://www.fightmatrix.com/historical-mma-rankings/ranking-snapshots/?Issue={issue}&Division={division}",
                    callback=self.parse_ranking_page,
                    cb_kwargs={"date": date, "weight_class": weight_class},
                )

    def parse_ranking_page(self, response, date, weight_class):
        rows = response.css("table.tblRank > tbody > tr")
        for row in rows[1:]:
            ranking_item = FightMatrixRankingItem()
            ranking_item["DATE"] = date
            ranking_item["WEIGHT_CLASS"] = weight_class

            cells = row.css("td")

            ranking_item["RANK"] = int(cells[0].css("::text").get().strip())
            rank_change = cells[1].css("::text").get().strip()
            if rank_change == "NR":
                ranking_item["RANK_CHANGE"] = None
            elif not rank_change:
                ranking_item["RANK_CHANGE"] = 0
            else:
                ranking_item["RANK_CHANGE"] = int(rank_change)

            fighter_link = cells[2].css("a::attr(href)").get()
            fighter_id = fighter_link.replace("/fighter-profile/", "")

            if fighter_id == "//":
                # Edge case for missing fighter
                continue

            ranking_item["FIGHTER_ID"] = fighter_id
            ranking_item["POINTS"] = int(cells[3].css("div.tdBar::text").get().strip())

            yield ranking_item

            yield response.follow(
                fighter_link,
                callback=self.parse_fighter,
            )

        pager_table = response.css("table.pager")[0]
        pager_atags = pager_table.css("tr > td > a")
        if pager_atags:
            for atag in pager_atags:
                arrow = atag.css("b::text").get().strip()
                href = atag.css("::attr(href)").get()
                if arrow == ">":
                    yield response.follow(
                        href,
                        callback=self.parse_ranking_page,
                        cb_kwargs={"date": date, "weight_class": weight_class},
                    )
                    break

    def parse_fighter(self, response):
        fighter_item = FightMatrixFighterItem()

        fighter_item["FIGHTER_NAME"] = (
            response.css("div.posttitle > h1 > a::text").get().strip()
        )
        fighter_item["FIGHTER_ID"] = response.url.replace(
            "https://www.fightmatrix.com/fighter-profile/", ""
        )
        fighter_links = response.css(
            "td.tdRankHead > div.leftCol *> a::attr(href)"
        ).getall()
        sherdog_fighter_id = tapology_fighter_id = None
        for link in fighter_links:
            if "www.sherdog.com" in link:
                sherdog_fighter_id = link.split("/")[-1]
            elif "www.tapology.com" in link:
                tapology_fighter_id = link.split("/")[-1]
        fighter_item["SHERDOG_FIGHTER_ID"] = sherdog_fighter_id
        fighter_item["TAPOLOGY_FIGHTER_ID"] = tapology_fighter_id

        yield fighter_item


class UFCStatsUpcomingEventSpider(Spider):
    """
    Spider for scraping upcoming UFC event from UFCStats
    """

    name = "ufcstats_upcoming_event_spider"
    allowed_domains = ["ufcstats.com"]
    start_urls = ["http://www.ufcstats.com/statistics/events/upcoming"]
    custom_settings = {}

    def parse(self, response):
        pass


class TapologyUpcomingEventSpider(Spider):
    """
    Spider for scraping upcoming UFC event from Tapology
    """

    name = "tapology_upcoming_event_spider"
    allowed_domains = ["tapology.com"]
    start_urls = [
        "https://www.tapology.com/fightcenter?group=ufc&schedule=upcoming&sport=mma"
    ]
    custom_settings = {}

    def parse(self, response):
        pass


class FightOddsIOSpider(Spider):
    """
    Spider for scraping betting odds from FightOdds.io
    """

    name = "fightoddsio_spider"
    allowed_domains = ["fightodds.io"]
    start_urls = ["https://fightodds.io/upcoming-mma-events/ufc"]
    custom_settings = {}

    def parse(self, response):
        pass
