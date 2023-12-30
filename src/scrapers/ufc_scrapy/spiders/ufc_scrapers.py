"""
This module contains all the spiders for scraping UFC data.
"""

# standard library imports
import json
from datetime import datetime, timedelta, timezone

# third party imports
import pandas as pd
import w3lib.html
from scrapy.http import Request
from scrapy.spiders import Spider

# local imports
from src.scrapers.ufc_scrapy.items import (
    FightOddsIOBoutItem,
    FightOddsIOFighterItem,
    UFCStatsBoutOverallItem,
    UFCStatsBoutRoundItem,
    UFCStatsFighterItem,
)
from src.scrapers.ufc_scrapy.utils import (
    EVENTS_RECENT_GQL_QUERY,
    FIGHTERS_GQL_QUERY,
    FIGHTS_GQL_QUERY,
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
            "ufc_scrapy.pipelines.UFCStatsResultsPipeline": 100,
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

    def parse_fighter(self, response):
        fighter_item = UFCStatsFighterItem()

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
            int(info[2].replace('"', "")) if info[2] != "--" else None
        )
        fighter_item["STANCE"] = info[3] if info[3] else None
        fighter_item["DATE_OF_BIRTH"] = (
            pd.to_datetime(info[4]).strftime("%Y-%m-%d") if info[4] != "--" else None
        )

        yield fighter_item

    def parse_bout(
        self, response, event_id, event_name, date, location, bout_ordinal, weight_class
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
            if any(["perf.png", "sub.png", "ko.png"]) in bonus_img_names:
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


class FightOddsIOSpider(Spider):
    """
    Spider for scraping historical fighter and bout data from FightOdds.io
    """

    name = "fightoddsio_spider"
    allowed_domains = ["fightodds.io"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 8,
        "CONCURRENT_REQUESTS": 8,
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
        "LOG_FORMATTER": "ufc_scrapy.logformatter.PoliteLogFormatter",
        "ITEM_PIPELINES": {
            "ufc_scrapy.pipelines.FightOddsIOFightersDuplicatesPipeline": 100,
            "ufc_scrapy.pipelines.FightOddsIOResultsPipeline": 200,
        },
        "CLOSESPIDER_ERRORCOUNT": 1,
    }

    def __init__(self, *args, scrape_type, **kwargs):
        super().__init__(*args, **kwargs)
        assert scrape_type in {"all", "most_recent"}
        self.scrape_type = scrape_type

        self.gql_url = "https://api.fightinsider.io/gql"
        self.headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/json",
        }
        self.date_today = datetime.now(timezone.utc).date().strftime("%Y-%m-%d")

    def start_requests(self):
        payload = json.dumps(
            {
                "query": EVENTS_RECENT_GQL_QUERY,
                "variables": {
                    "promotionSlug": "ufc",
                    "dateLt": self.date_today,
                    "after": "",
                    "first": 100,
                    "orderBy": "-date",
                },
            }
        )

        yield Request(
            url=self.gql_url,
            method="POST",
            headers=self.headers,
            body=payload,
            callback=self.parse_infinite_scroll,
            dont_filter=True,
        )

    def parse_infinite_scroll(self, response):
        json_resp = json.loads(response.body)

        events = json_resp["data"]["promotion"]["events"]
        edges = events["edges"]
        event_pks = [edge["node"]["pk"] for edge in edges]

        if self.scrape_type == "most_recent":
            edges = [edges[0]]
            event_pks = [event_pks[0]]

        for edge, pk in zip(edges, event_pks):
            event_name = edge["node"]["name"]

            if "Dana White" in event_name:
                continue

            payload_fights = json.dumps(
                {"query": FIGHTS_GQL_QUERY, "variables": {"eventPk": pk}}
            )

            yield Request(
                url=self.gql_url,
                method="POST",
                headers=self.headers,
                body=payload_fights,
                callback=self.parse_event_fights,
                dont_filter=True,
                cb_kwargs={"info_dict": edge},
            )

        has_next_page = events["pageInfo"]["hasNextPage"]
        if has_next_page and self.scrape_type == "all":
            cursor_pos = events["pageInfo"]["endCursor"]
            payload_pagination = json.dumps(
                {
                    "query": EVENTS_RECENT_GQL_QUERY,
                    "variables": {
                        "promotionSlug": "ufc",
                        "dateLt": self.date_today,
                        "after": cursor_pos,
                        "first": 100,
                        "orderBy": "-date",
                    },
                }
            )

            yield Request(
                url=self.gql_url,
                method="POST",
                headers=self.headers,
                body=payload_pagination,
                callback=self.parse_infinite_scroll,
                dont_filter=True,
            )

    def parse_event_fights(self, response, info_dict):
        json_resp = json.loads(response.body)
        edges = json_resp["data"]["event"]["fights"]["edges"]
        confirmed = [edge for edge in edges if not edge["node"]["isCancelled"]]
        last_bout_ordinal = (
            max([bout["node"]["order"] for bout in confirmed]) if confirmed else 0
        )

        for bout in confirmed:
            bout_item = FightOddsIOBoutItem()

            bout_item["BOUT_SLUG"] = bout["node"]["slug"]
            bout_item["EVENT_SLUG"] = info_dict["node"]["slug"]
            bout_item["EVENT_NAME"] = info_dict["node"]["name"]
            bout_item["DATE"] = info_dict["node"]["date"]
            bout_item["LOCATION"] = info_dict["node"]["city"]
            bout_item["VENUE"] = info_dict["node"]["venue"]
            bout_item["BOUT_ORDINAL"] = last_bout_ordinal - bout["node"]["order"]
            bout_item["BOUT_CARD_TYPE"] = (
                bout["node"]["fightType"] if bout["node"]["fightType"] else None
            )

            f1_slug = bout["node"]["fighter1"]["slug"]
            f2_slug = bout["node"]["fighter2"]["slug"]
            bout_item["FIGHTER_1_SLUG"] = f1_slug
            bout_item["FIGHTER_2_SLUG"] = f2_slug
            bout_item["WEIGHT_CLASS"] = (
                bout["node"]["weightClass"]["weightClass"]
                if bout["node"]["weightClass"]
                else None
            )
            bout_item["WEIGHT"] = (
                bout["node"]["weightClass"]["weight"]
                if bout["node"]["weightClass"]
                else None
            )
            bout_item["WINNER_SLUG"] = (
                bout["node"]["fighterWinner"]["slug"]
                if bout["node"]["fighterWinner"]
                else None
            )
            bout_item["OUTCOME_METHOD_1"] = (
                bout["node"]["methodOfVictory1"]
                if bout["node"]["methodOfVictory1"]
                else None
            )
            bout_item["OUTCOME_METHOD_2"] = (
                bout["node"]["methodOfVictory2"]
                if bout["node"]["methodOfVictory2"]
                else None
            )
            bout_item["END_ROUND"] = bout["node"]["round"]
            end_round_time_split = bout["node"]["duration"].split(":")

            try:
                end_round_time_seconds = (
                    60 * int(end_round_time_split[0]) + int(end_round_time_split[1])
                    if bout["node"]["duration"]
                    else None
                )
            except:
                end_round_time_seconds = None

            bout_item["END_ROUND_TIME_SECONDS"] = end_round_time_seconds
            bout_item["TOTAL_TIME_SECONDS"] = (
                (300 * (bout["node"]["round"] - 1) + end_round_time_seconds)
                if bout["node"]["round"] and end_round_time_seconds
                else None
            )
            bout_item["FIGHTER_1_ODDS"] = bout["node"]["fighter1Odds"]
            bout_item["FIGHTER_2_ODDS"] = bout["node"]["fighter2Odds"]

            yield bout_item

            fighter_slugs = [f1_slug, f2_slug]
            for fighter_slug in fighter_slugs:
                payload_fighter = json.dumps(
                    {
                        "query": FIGHTERS_GQL_QUERY,
                        "variables": {"fighterSlug": fighter_slug},
                    }
                )

                yield Request(
                    url=self.gql_url,
                    method="POST",
                    headers=self.headers,
                    body=payload_fighter,
                    callback=self.parse_fighter,
                    dont_filter=True,
                    cb_kwargs={"fighter_slug": fighter_slug},
                )

    def parse_fighter(self, response, fighter_slug):
        json_resp = json.loads(response.body)
        fighter_data = json_resp["data"]["fighter"]

        fighter_item = FightOddsIOFighterItem()

        fighter_item["FIGHTER_SLUG"] = fighter_slug
        fighter_item[
            "FIGHTER_NAME"
        ] = f"{fighter_data['firstName']} {fighter_data['lastName']}".strip()
        fighter_item["HEIGHT_CENTIMETERS"] = (
            float(fighter_data["height"])
            if fighter_data["height"] and fighter_data["height"] != "0.0"
            else None
        )
        fighter_item["REACH_INCHES"] = (
            float(fighter_data["reach"])
            if fighter_data["reach"] and fighter_data["reach"] != "0.0"
            else None
        )
        fighter_item["LEG_REACH_INCHES"] = (
            float(fighter_data["legReach"])
            if fighter_data["legReach"] and fighter_data["legReach"] != "0.0"
            else None
        )
        fighter_item["FIGHTING_STYLE"] = (
            fighter_data["fightingStyle"] if fighter_data["fightingStyle"] else None
        )
        fighter_item["STANCE"] = (
            fighter_data["stance"] if fighter_data["stance"] else None
        )
        fighter_item["NATIONALITY"] = (
            fighter_data["nationality"] if fighter_data["nationality"] else None
        )
        # 1970-01-01 used as placeholder for missing DOB
        fighter_item["DATE_OF_BIRTH"] = (
            fighter_data["birthDate"]
            if fighter_data["birthDate"] and fighter_data["birthDate"] != "1970-01-01"
            else None
        )

        yield fighter_item


class UpcomingEventSpider(Spider):
    """
    Spider for scraping upcoming UFC event from UFCStats and corresponding
    betting odds from FightOdds.io
    """

    name = "upcoming_event_spider"
    allowed_domains = ["ufcstats.com", "fightodds.io"]
    start_urls = ["http://www.ufcstats.com/statistics/events/upcoming"]
    custom_settings = {}

    def parse(self, response):
        today_utc = datetime.now(timezone.utc).date()
        next_saturday = (today_utc + timedelta((5 - today_utc.weekday()) % 7)).strftime(
            "%Y-%m-%d"
        )

        next_event_date = pd.to_datetime(
            response.css("span.b-statistics__date::text").get().strip()
        ).strftime("%Y-%m-%d")

        if next_event_date == next_saturday:
            pass

    def parse_event(self, response):
        pass

    def parse_fighter(self, response):
        fighter_item = UFCStatsFighterItem()

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

    def parse_bout(self, response):
        pass

    def parse_fightodds_main_page(self, response, date):
        pass
