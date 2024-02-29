# standard library imports
from datetime import datetime, timedelta, timezone

# third party imports
import pandas as pd
import w3lib.html
from scrapy.spiders import Spider

# local imports
from src.scrapers.ufc_scrapy.items import (
    UFCStatsBoutOverallItem,
    UFCStatsBoutRoundItem,
    UFCStatsFighterItem,
    UFCStatsUpcomingBoutItem,
)
from src.scrapers.ufc_scrapy.utils import (
    convert_height,
    ctrl_time,
    extract_landed_attempted,
    total_time,
)


class UFCStatsResultsSpider(Spider):
    """
    Spider for scraping UFC bout and fighter data from UFC Stats
    """

    name = "ufcstats_results_spider"
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
        "RETRY_TIMES": 0,
        "LOG_LEVEL": "INFO",
        "ITEM_PIPELINES": {
            "ufc_scrapy.scrapy_pipelines.ufcstats_pipelines.UFCStatsFightersPipeline": 100,
            "ufc_scrapy.scrapy_pipelines.ufcstats_pipelines.UFCStatsCompletedBoutsPipeline": 200,
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
        rows = response.css(
            "tr.b-fight-details__table-row.b-fight-details__table-row__hover.js-fight-details-click"
        )
        bout_urls = []
        weight_classes = []
        for row in rows:
            bout_urls.append(
                row.css(
                    """td.b-fight-details__table-col.b-fight-details__table-col_style_align-top >
                    p.b-fight-details__table-text > a.b-flag::attr(href)"""
                ).get()
            )
            weight_classes.append(
                row.css(
                    """td.b-fight-details__table-col.l-page_align_left:not([style='width:100px']) >
                    p.b-fight-details__table-text::text"""
                )
                .get()
                .strip()
            )
        assert len(bout_urls) == len(weight_classes)

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

        for bout_ordinal, (bout_url, weight_class) in enumerate(
            zip(reversed(bout_urls), reversed(weight_classes))
        ):
            yield response.follow(
                bout_url,
                callback=self.parse_bout,
                cb_kwargs={
                    "event_id": event_id,
                    "event_name": event_name,
                    "date": date,
                    "location": location,
                    "bout_ordinal": bout_ordinal,
                    "weight_class": weight_class,
                },
            )

        fighter_urls = response.css(
            """td[style='width:100px'].b-fight-details__table-col.l-page_align_left >
            p.b-fight-details__table-text >
            a.b-link.b-link_style_black::attr(href)
            """
        ).getall()

        yield from response.follow_all(fighter_urls, self.parse_fighter)

    def parse_bout(
        self,
        response,
        event_id,
        event_name,
        date,
        location,
        bout_ordinal,
        weight_class,
    ):
        bout_overall_item = UFCStatsBoutOverallItem()

        bout_overall_item["BOUT_ID"] = response.url.split("/")[-1]
        bout_overall_item["EVENT_ID"] = event_id
        bout_overall_item["EVENT_NAME"] = event_name
        bout_overall_item["DATE"] = pd.to_datetime(date).strftime("%Y-%m-%d")
        bout_overall_item["LOCATION"] = location
        bout_overall_item["BOUT_ORDINAL"] = bout_ordinal
        bout_overall_item["WEIGHT_CLASS"] = weight_class

        fighter_urls = response.css(
            "a.b-link.b-fight-details__person-link::attr(href)"
        ).getall()
        bout_overall_item["RED_FIGHTER_ID"] = fighter_urls[0].split("/")[-1]
        bout_overall_item["BLUE_FIGHTER_ID"] = fighter_urls[1].split("/")[-1]

        outcomes = response.css("i.b-fight-details__person-status::text").getall()
        bout_overall_item["RED_OUTCOME"] = outcomes[0].strip()
        bout_overall_item["BLUE_OUTCOME"] = outcomes[1].strip()

        bout_overall_item["BOUT_LONGNAME"] = [
            x.strip()
            for x in response.css("i.b-fight-details__fight-title::text").getall()
            if x.strip()
        ][0]

        bonus_img_src = response.css(
            "i.b-fight-details__fight-title > img::attr(src)"
        ).getall()
        if bonus_img_src:
            bonus_img_names = [x.split("/")[-1] for x in bonus_img_src]
            if any(x in ["perf.png", "sub.png", "ko.png"] for x in bonus_img_names):
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
        total_time_seconds, per_round_times = total_time(
            bout_overall_item["BOUT_TIME_FORMAT"],
            bout_overall_item["END_ROUND"],
            bout_overall_item["END_ROUND_TIME_SECONDS"],
        )
        bout_overall_item["TOTAL_TIME_SECONDS"] = total_time_seconds

        assert len(per_round_times) == bout_overall_item["END_ROUND"]

        tables = response.css("tbody.b-fight-details__table-body")
        if tables:
            stats_by_round_rows = tables[1].css("tr.b-fight-details__table-row")
            sig_stats_by_round_rows = tables[3].css("tr.b-fight-details__table-row")

            assert len(stats_by_round_rows) == len(sig_stats_by_round_rows)

            for i in range(len(stats_by_round_rows)):
                bout_round_item = UFCStatsBoutRoundItem()

                bout_round_item["BOUT_ID"] = bout_overall_item["BOUT_ID"]
                bout_round_item["ROUND"] = i + 1
                bout_round_item["TIME_FOUGHT_SECONDS"] = per_round_times[i]

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

    def parse_fighter(self, response):
        fighter_item = UFCStatsFighterItem()

        fighter_item["FIGHTER_ID"] = response.url.split("/")[-1]
        fighter_item["FIGHTER_NAME"] = (
            response.css("span.b-content__title-highlight::text").get().strip()
        )
        nick = response.css("p.b-content__Nickname::text").get().strip()
        fighter_item["FIGHTER_NICKNAME"] = nick if nick else None

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
            int(info[2].replace('"', "")) if info[2] != "--" else None
        )
        fighter_item["STANCE"] = info[3] if info[3] else None
        fighter_item["DATE_OF_BIRTH"] = (
            pd.to_datetime(info[4]).strftime("%Y-%m-%d") if info[4] != "--" else None
        )

        yield fighter_item


class UFCStatsUpcomingEventSpider(Spider):
    """
    Spider for scraping upcoming UFC event data from UFCStats
    """

    name = "ufcstats_upcoming_spider"
    allowed_domains = ["ufcstats.com"]
    start_urls = ["http://www.ufcstats.com/statistics/events/upcoming"]
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
            "ufc_scrapy.pipelines.UFCStatsUpcomingBoutsPipeline": 100,
        },
        "CLOSESPIDER_ERRORCOUNT": 1,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.date_today = datetime.now(timezone.utc).date()

    def parse(self, response):
        next_saturday = (
            self.date_today + timedelta((5 - self.date_today.weekday()) % 7)
        ).strftime("%Y-%m-%d")

        next_event_date = pd.to_datetime(
            response.css("span.b-statistics__date::text").get().strip()
        ).strftime("%Y-%m-%d")

        if next_event_date == next_saturday:
            upcoming_event_link = response.css(
                """table.b-statistics__table-events > tbody > tr.b-statistics__table-row > td.b-statistics__table-col > 
                i.b-statistics__table-content > a.b-link.b-link_style_black::attr(href)"""
            ).get()

            yield response.follow(
                upcoming_event_link, callback=self.parse_upcoming_event
            )

    def parse_upcoming_event(self, response):
        rows = response.css(
            "tr.b-fight-details__table-row.b-fight-details__table-row__hover.js-fight-details-click"
        )
        bout_urls = []
        weight_classes = []
        for row in rows:
            bout_urls.append(
                row.css(
                    """td.b-fight-details__table-col > p.b-fight-details__table-text > 
                    a.b-link.b-link_style_black::attr(data-link)"""
                ).get()
            )
            weight_classes.append(
                row.css(
                    """td.b-fight-details__table-col.l-page_align_left:not([style='width:100px']) >
                    p.b-fight-details__table-text::text"""
                )
                .get()
                .strip()
            )
        assert len(bout_urls) == len(weight_classes)

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

        for bout_ordinal, (bout_url, weight_class) in enumerate(
            zip(reversed(bout_urls), reversed(weight_classes))
        ):
            yield response.follow(
                bout_url,
                callback=self.parse_upcoming_bout,
                cb_kwargs={
                    "event_id": event_id,
                    "event_name": event_name,
                    "date": date,
                    "location": location,
                    "bout_ordinal": bout_ordinal,
                    "weight_class": weight_class,
                },
            )

    def parse_upcoming_bout(
        self, response, event_id, event_name, date, location, bout_ordinal, weight_class
    ):
        upcoming_bout_item = UFCStatsUpcomingBoutItem()

        upcoming_bout_item["BOUT_ID"] = response.url.split("/")[-1]
        upcoming_bout_item["EVENT_ID"] = event_id
        upcoming_bout_item["EVENT_NAME"] = event_name
        upcoming_bout_item["DATE"] = pd.to_datetime(date).strftime("%Y-%m-%d")
        upcoming_bout_item["LOCATION"] = location
        upcoming_bout_item["BOUT_ORDINAL"] = bout_ordinal
        upcoming_bout_item["WEIGHT_CLASS"] = weight_class

        upcoming_bout_item["BOUT_LONGNAME"] = [
            x.strip()
            for x in response.css("i.b-fight-details__fight-title::text").getall()
            if x.strip()
        ][0]
        fighter_urls = response.css(
            "a.b-link.b-fight-details__person-link::attr(href)"
        ).getall()
        upcoming_bout_item["RED_FIGHTER_ID"] = fighter_urls[0].split("/")[-1]
        upcoming_bout_item["BLUE_FIGHTER_ID"] = fighter_urls[1].split("/")[-1]

        yield upcoming_bout_item
