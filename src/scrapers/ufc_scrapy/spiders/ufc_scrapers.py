# standard library imports
import re
from ast import literal_eval
from html import unescape

# third party imports
import pandas as pd
import w3lib.html
from scrapy.http import FormRequest
from scrapy.spiders import Spider

# local imports
from src.scrapers.ufc_scrapy.items import BoutItem, FighterItem
from src.scrapers.ufc_scrapy.utils import (
    convert_height,
    ctrl_time,
    extract_landed_attempted,
    extract_record,
    total_time,
)


class UFCStatsSpider(Spider):
    name = "ufc_stats_spider"
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
        "RETRY_TIMES": 5,
        "LOG_LEVEL": "INFO",
        "ITEM_PIPELINES": {
            "ufc_scrapy.pipelines.BoutsSQLitePipeline": 100,
            "ufc_scrapy.pipelines.FightersSQLitePipeline": 100,
        },
    }

    def parse(self, response):
        event_urls = ["http://ufcstats.com/event-details/6420efac0578988b"]
        event_urls.extend(
            response.css(
                """tr.b-statistics__table-row >
                td.b-statistics__table-col >
                i.b-statistics__table-content >
                a.b-link.b-link_style_black::attr(href)"""
            ).getall()
        )

        for event_url in event_urls:
            yield response.follow(event_url, callback=self.parse_event)

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

        fighter_urls = response.css(
            """td[style='width:100px'].b-fight-details__table-col.l-page_align_left >
            p.b-fight-details__table-text >
            a.b-link.b-link_style_black::attr(href)
            """
        ).getall()

        for fighter_url in fighter_urls:
            yield response.follow(fighter_url, callback=self.parse_fighter)

    def parse_fighter(self, response):
        fighter_item = FighterItem()

        # Get all relevant fields
        fighter_item["FIGHTER_ID"] = response.url.split("/")[-1]
        fighter_item["FIGHTER_NAME"] = (
            response.css("span.b-content__title-highlight::text").get().strip()
        )
        record = (
            response.css("span.b-content__title-record::text")
            .get()
            .replace("Record: ", "")
            .strip()
        )
        (
            fighter_item["WINS"],
            fighter_item["LOSSES"],
            fighter_item["DRAWS"],
            fighter_item["NO_CONTESTS"],
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
        fighter_item["HEIGHT_INCHES"] = convert_height(info[0])
        fighter_item["REACH_INCHES"] = (
            float(info[2].replace('"', "")) if info[2] != "--" else None
        )
        fighter_item["FIGHTING_STANCE"] = info[3] if info[3] else None
        fighter_item["DATE_OF_BIRTH"] = (
            pd.to_datetime(info[4]).strftime("%Y-%m-%d") if info[4] != "--" else None
        )

        yield fighter_item

    def parse_bout(self, response, event_id, event_name, date, location, bout_ordinal):
        bout_item = BoutItem()

        bout_item["BOUT_ID"] = response.url.split("/")[-1]

        bout_item["EVENT_ID"] = event_id
        bout_item["EVENT_NAME"] = event_name
        bout_item["DATE"] = pd.to_datetime(date).strftime("%Y-%m-%d")
        bout_item["LOCATION"] = location
        bout_item["BOUT_ORDINAL"] = bout_ordinal

        # Get all relevant fields
        fighter_urls = response.css(
            "a.b-link.b-fight-details__person-link::attr(href)"
        ).getall()
        bout_item["RED_FIGHTER_ID"] = fighter_urls[0].split("/")[-1]
        bout_item["BLUE_FIGHTER_ID"] = fighter_urls[1].split("/")[-1]

        fighter_names = response.css(
            "a.b-link.b-fight-details__person-link::text"
        ).getall()
        bout_item["RED_FIGHTER_NAME"] = fighter_names[0].strip()
        bout_item["BLUE_FIGHTER_NAME"] = fighter_names[1].strip()

        outcomes = response.css("i.b-fight-details__person-status::text").getall()
        bout_item["RED_OUTCOME"] = outcomes[0].strip()
        bout_item["BLUE_OUTCOME"] = outcomes[1].strip()

        bout_item["BOUT_TYPE"] = [
            x.strip()
            for x in response.css("i.b-fight-details__fight-title::text").getall()
            if x.strip()
        ][0]

        method_info = response.css("i.b-fight-details__text-item_first").getall()
        bout_item["OUTCOME_METHOD"] = (
            w3lib.html.remove_tags(method_info[0]).replace("Method:", "").strip()
        )

        details = response.css("p.b-fight-details__text").getall()
        bout_item["OUTCOME_METHOD_DETAILS"] = (
            w3lib.html.remove_tags(details[1]).replace("Details:", "").strip()
        )

        time_format_info = response.css("i.b-fight-details__text-item").getall()
        bout_item["END_ROUND"] = int(
            w3lib.html.remove_tags(time_format_info[0]).replace("Round:", "").strip()
        )
        end_round_time_split = (
            w3lib.html.remove_tags(time_format_info[1])
            .replace("Time:", "")
            .strip()
            .split(":")
        )
        bout_item["END_ROUND_TIME_MINUTES"] = (
            int(end_round_time_split[0]) + int(end_round_time_split[1]) / 60.0
        )
        bout_item["BOUT_TIME_FORMAT"] = (
            w3lib.html.remove_tags(time_format_info[2])
            .replace("Time format:", "")
            .strip()
        )
        bout_item["TOTAL_TIME_MINUTES"] = total_time(
            bout_item["BOUT_TIME_FORMAT"],
            bout_item["END_ROUND"],
            bout_item["END_ROUND_TIME_MINUTES"],
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
            "RED_FIGHTER_NAME",
            "BLUE_FIGHTER_NAME",
            "RED_OUTCOME",
            "BLUE_OUTCOME",
            "BOUT_TYPE",
            "OUTCOME_METHOD",
            "OUTCOME_METHOD_DETAILS",
            "END_ROUND",
            "END_ROUND_TIME_MINUTES",
            "BOUT_TIME_FORMAT",
            "TOTAL_TIME_MINUTES",
        }
        for key in BoutItem.fields.keys() - non_fight_table_fields:
            bout_item[key] = None

        tables = response.css("tbody.b-fight-details__table-body")
        if tables:
            assert len(tables) == 4

            # Overall
            stats = [
                x.strip()
                for x in tables[0].css("p.b-fight-details__table-text::text").getall()
            ]
            bout_item["RED_KNOCKDOWNS"] = int(stats[4])
            bout_item["BLUE_KNOCKDOWNS"] = int(stats[5])
            (
                bout_item["RED_TOTAL_STRIKES_LANDED"],
                bout_item["RED_TOTAL_STRIKES_ATTEMPTED"],
            ) = extract_landed_attempted(stats[10])
            (
                bout_item["BLUE_TOTAL_STRIKES_LANDED"],
                bout_item["BLUE_TOTAL_STRIKES_ATTEMPTED"],
            ) = extract_landed_attempted(stats[11])
            (
                bout_item["RED_TAKEDOWNS_LANDED"],
                bout_item["RED_TAKEDOWNS_ATTEMPTED"],
            ) = extract_landed_attempted(stats[12])
            (
                bout_item["BLUE_TAKEDOWNS_LANDED"],
                bout_item["BLUE_TAKEDOWNS_ATTEMPTED"],
            ) = extract_landed_attempted(stats[13])
            bout_item["RED_SUBMISSION_ATTEMPTS"] = int(stats[16])
            bout_item["BLUE_SUBMISSION_ATTEMPTS"] = int(stats[17])
            bout_item["RED_REVERSALS"] = int(stats[18])
            bout_item["BLUE_REVERSALS"] = int(stats[19])
            bout_item["RED_CONTROL_TIME_MINUTES"] = ctrl_time(stats[20])
            bout_item["BLUE_CONTROL_TIME_MINUTES"] = ctrl_time(stats[21])

            sig_stats = [
                x.strip()
                for x in tables[2].css("p.b-fight-details__table-text::text").getall()
            ]
            (
                bout_item["RED_SIGNIFICANT_STRIKES_LANDED"],
                bout_item["RED_SIGNIFICANT_STRIKES_ATTEMPTED"],
            ) = extract_landed_attempted(sig_stats[4])
            (
                bout_item["BLUE_SIGNIFICANT_STRIKES_LANDED"],
                bout_item["BLUE_SIGNIFICANT_STRIKES_ATTEMPTED"],
            ) = extract_landed_attempted(sig_stats[5])
            (
                bout_item["RED_SIGNIFICANT_STRIKES_HEAD_LANDED"],
                bout_item["RED_SIGNIFICANT_STRIKES_HEAD_ATTEMPTED"],
            ) = extract_landed_attempted(sig_stats[8])
            (
                bout_item["BLUE_SIGNIFICANT_STRIKES_HEAD_LANDED"],
                bout_item["BLUE_SIGNIFICANT_STRIKES_HEAD_ATTEMPTED"],
            ) = extract_landed_attempted(sig_stats[9])
            (
                bout_item["RED_SIGNIFICANT_STRIKES_BODY_LANDED"],
                bout_item["RED_SIGNIFICANT_STRIKES_BODY_ATTEMPTED"],
            ) = extract_landed_attempted(sig_stats[10])
            (
                bout_item["BLUE_SIGNIFICANT_STRIKES_BODY_LANDED"],
                bout_item["BLUE_SIGNIFICANT_STRIKES_BODY_ATTEMPTED"],
            ) = extract_landed_attempted(sig_stats[11])
            (
                bout_item["RED_SIGNIFICANT_STRIKES_LEG_LANDED"],
                bout_item["RED_SIGNIFICANT_STRIKES_LEG_ATTEMPTED"],
            ) = extract_landed_attempted(sig_stats[12])
            (
                bout_item["BLUE_SIGNIFICANT_STRIKES_LEG_LANDED"],
                bout_item["BLUE_SIGNIFICANT_STRIKES_LEG_ATTEMPTED"],
            ) = extract_landed_attempted(sig_stats[13])
            (
                bout_item["RED_SIGNIFICANT_STRIKES_DISTANCE_LANDED"],
                bout_item["RED_SIGNIFICANT_STRIKES_DISTANCE_ATTEMPTED"],
            ) = extract_landed_attempted(sig_stats[14])
            (
                bout_item["BLUE_SIGNIFICANT_STRIKES_DISTANCE_LANDED"],
                bout_item["BLUE_SIGNIFICANT_STRIKES_DISTANCE_ATTEMPTED"],
            ) = extract_landed_attempted(sig_stats[15])
            (
                bout_item["RED_SIGNIFICANT_STRIKES_CLINCH_LANDED"],
                bout_item["RED_SIGNIFICANT_STRIKES_CLINCH_ATTEMPTED"],
            ) = extract_landed_attempted(sig_stats[16])
            (
                bout_item["BLUE_SIGNIFICANT_STRIKES_CLINCH_LANDED"],
                bout_item["BLUE_SIGNIFICANT_STRIKES_CLINCH_ATTEMPTED"],
            ) = extract_landed_attempted(sig_stats[17])
            (
                bout_item["RED_SIGNIFICANT_STRIKES_GROUND_LANDED"],
                bout_item["RED_SIGNIFICANT_STRIKES_GROUND_ATTEMPTED"],
            ) = extract_landed_attempted(sig_stats[18])
            (
                bout_item["BLUE_SIGNIFICANT_STRIKES_GROUND_LANDED"],
                bout_item["BLUE_SIGNIFICANT_STRIKES_GROUND_ATTEMPTED"],
            ) = extract_landed_attempted(sig_stats[19])

            # Round by round
            stats_by_round_rows = tables[1].css("tr.b-fight-details__table-row")
            sig_stats_by_round_rows = tables[3].css("tr.b-fight-details__table-row")

            assert len(stats_by_round_rows) == len(sig_stats_by_round_rows)

            for i in range(len(stats_by_round_rows)):
                stats_for_round = [
                    x.strip()
                    for x in stats_by_round_rows[i]
                    .css("p.b-fight-details__table-text::text")
                    .getall()
                ]
                bout_item[f"RED_KNOCKDOWNS_ROUND_{i+1}"] = int(stats_for_round[4])
                bout_item[f"BLUE_KNOCKDOWNS_ROUND_{i+1}"] = int(stats_for_round[5])
                (
                    bout_item[f"RED_TOTAL_STRIKES_LANDED_ROUND_{i+1}"],
                    bout_item[f"RED_TOTAL_STRIKES_ATTEMPTED_ROUND_{i+1}"],
                ) = extract_landed_attempted(stats_for_round[10])
                (
                    bout_item[f"BLUE_TOTAL_STRIKES_LANDED_ROUND_{i+1}"],
                    bout_item[f"BLUE_TOTAL_STRIKES_ATTEMPTED_ROUND_{i+1}"],
                ) = extract_landed_attempted(stats_for_round[11])
                (
                    bout_item[f"RED_TAKEDOWNS_LANDED_ROUND_{i+1}"],
                    bout_item[f"RED_TAKEDOWNS_ATTEMPTED_ROUND_{i+1}"],
                ) = extract_landed_attempted(stats_for_round[12])
                (
                    bout_item[f"BLUE_TAKEDOWNS_LANDED_ROUND_{i+1}"],
                    bout_item[f"BLUE_TAKEDOWNS_ATTEMPTED_ROUND_{i+1}"],
                ) = extract_landed_attempted(stats_for_round[13])
                bout_item[f"RED_SUBMISSION_ATTEMPTS_ROUND_{i+1}"] = int(
                    stats_for_round[16]
                )
                bout_item[f"BLUE_SUBMISSION_ATTEMPTS_ROUND_{i+1}"] = int(
                    stats_for_round[17]
                )
                bout_item[f"RED_REVERSALS_ROUND_{i+1}"] = int(stats_for_round[18])
                bout_item[f"BLUE_REVERSALS_ROUND_{i+1}"] = int(stats_for_round[19])
                bout_item[f"RED_CONTROL_TIME_MINUTES_ROUND_{i+1}"] = ctrl_time(
                    stats_for_round[20]
                )
                bout_item[f"BLUE_CONTROL_TIME_MINUTES_ROUND_{i+1}"] = ctrl_time(
                    stats_for_round[21]
                )

                sig_stats_for_round = [
                    x.strip()
                    for x in sig_stats_by_round_rows[i]
                    .css("p.b-fight-details__table-text::text")
                    .getall()
                ]
                (
                    bout_item[f"RED_SIGNIFICANT_STRIKES_LANDED_ROUND_{i+1}"],
                    bout_item[f"RED_SIGNIFICANT_STRIKES_ATTEMPTED_ROUND_{i+1}"],
                ) = extract_landed_attempted(sig_stats_for_round[4])
                (
                    bout_item[f"BLUE_SIGNIFICANT_STRIKES_LANDED_ROUND_{i+1}"],
                    bout_item[f"BLUE_SIGNIFICANT_STRIKES_ATTEMPTED_ROUND_{i+1}"],
                ) = extract_landed_attempted(sig_stats_for_round[5])
                (
                    bout_item[f"RED_SIGNIFICANT_STRIKES_HEAD_LANDED_ROUND_{i+1}"],
                    bout_item[f"RED_SIGNIFICANT_STRIKES_HEAD_ATTEMPTED_ROUND_{i+1}"],
                ) = extract_landed_attempted(sig_stats_for_round[8])
                (
                    bout_item[f"BLUE_SIGNIFICANT_STRIKES_HEAD_LANDED_ROUND_{i+1}"],
                    bout_item[f"BLUE_SIGNIFICANT_STRIKES_HEAD_ATTEMPTED_ROUND_{i+1}"],
                ) = extract_landed_attempted(sig_stats_for_round[9])
                (
                    bout_item[f"RED_SIGNIFICANT_STRIKES_BODY_LANDED_ROUND_{i+1}"],
                    bout_item[f"RED_SIGNIFICANT_STRIKES_BODY_ATTEMPTED_ROUND_{i+1}"],
                ) = extract_landed_attempted(sig_stats_for_round[10])
                (
                    bout_item[f"BLUE_SIGNIFICANT_STRIKES_BODY_LANDED_ROUND_{i+1}"],
                    bout_item[f"BLUE_SIGNIFICANT_STRIKES_BODY_ATTEMPTED_ROUND_{i+1}"],
                ) = extract_landed_attempted(sig_stats_for_round[11])
                (
                    bout_item[f"RED_SIGNIFICANT_STRIKES_LEG_LANDED_ROUND_{i+1}"],
                    bout_item[f"RED_SIGNIFICANT_STRIKES_LEG_ATTEMPTED_ROUND_{i+1}"],
                ) = extract_landed_attempted(sig_stats_for_round[12])
                (
                    bout_item[f"BLUE_SIGNIFICANT_STRIKES_LEG_LANDED_ROUND_{i+1}"],
                    bout_item[f"BLUE_SIGNIFICANT_STRIKES_LEG_ATTEMPTED_ROUND_{i+1}"],
                ) = extract_landed_attempted(sig_stats_for_round[13])
                (
                    bout_item[f"RED_SIGNIFICANT_STRIKES_DISTANCE_LANDED_ROUND_{i+1}"],
                    bout_item[
                        f"RED_SIGNIFICANT_STRIKES_DISTANCE_ATTEMPTED_ROUND_{i+1}"
                    ],
                ) = extract_landed_attempted(sig_stats_for_round[14])
                (
                    bout_item[f"BLUE_SIGNIFICANT_STRIKES_DISTANCE_LANDED_ROUND_{i+1}"],
                    bout_item[
                        f"BLUE_SIGNIFICANT_STRIKES_DISTANCE_ATTEMPTED_ROUND_{i+1}"
                    ],
                ) = extract_landed_attempted(sig_stats_for_round[15])
                (
                    bout_item[f"RED_SIGNIFICANT_STRIKES_CLINCH_LANDED_ROUND_{i+1}"],
                    bout_item[f"RED_SIGNIFICANT_STRIKES_CLINCH_ATTEMPTED_ROUND_{i+1}"],
                ) = extract_landed_attempted(sig_stats_for_round[16])
                (
                    bout_item[f"BLUE_SIGNIFICANT_STRIKES_CLINCH_LANDED_ROUND_{i+1}"],
                    bout_item[f"BLUE_SIGNIFICANT_STRIKES_CLINCH_ATTEMPTED_ROUND_{i+1}"],
                ) = extract_landed_attempted(sig_stats_for_round[17])
                (
                    bout_item[f"RED_SIGNIFICANT_STRIKES_GROUND_LANDED_ROUND_{i+1}"],
                    bout_item[f"RED_SIGNIFICANT_STRIKES_GROUND_ATTEMPTED_ROUND_{i+1}"],
                ) = extract_landed_attempted(sig_stats_for_round[18])
                (
                    bout_item[f"BLUE_SIGNIFICANT_STRIKES_GROUND_LANDED_ROUND_{i+1}"],
                    bout_item[f"BLUE_SIGNIFICANT_STRIKES_GROUND_ATTEMPTED_ROUND_{i+1}"],
                ) = extract_landed_attempted(sig_stats_for_round[19])

        yield bout_item


class UFCTapologySpider(Spider):
    name = "ufc_tapology_spider"
    allowed_domains = ["tapology.com"]
    start_urls = [
        "https://www.tapology.com/fightcenter?group=ufc&schedule=results&sport=mma"
    ]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_DELAY": 0.5,
        "NUMBER_OF_PROXIES_TO_FETCH": 50,
        "DOWNLOADER_MIDDLEWARES": {
            "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
            "scrapy_user_agents.middlewares.RandomUserAgentMiddleware": 400,
            "rotating_free_proxies.middlewares.RotatingProxyMiddleware": 610,
            "rotating_free_proxies.middlewares.BanDetectionMiddleware": 620,
        },
        "REQUEST_FINGERPRINTER_IMPLEMENTATION": "2.7",
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "FEED_EXPORT_ENCODING": "utf-8",
        "DEPTH_PRIORITY": 1,
        "SCHEDULER_DISK_QUEUE": "scrapy.squeues.PickleFifoDiskQueue",
        "SCHEDULER_MEMORY_QUEUE": "scrapy.squeues.FifoMemoryQueue",
        "RETRY_TIMES": 5,
    }

    def parse(self, response):
        events = response.css(
            "section.fcListing > div.main > div.left > div.promotion > span.name > a::attr(href)"
        )
        event_urls = [response.urljoin(url.get()) for url in events]

        yield from response.follow_all(event_urls, self.parse_event)

        pagination_headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "*/*;q=0.5, text/javascript, application/javascript, application/ecmascript, application/x-ecmascript",
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

    def parse_next_page(self, response):
        data = response.text
        data = re.search(r"html\((.*)\);", data)
        assert data is not None
        data = data.group(1)
        data = unescape(literal_eval(data)).replace(r"\/", "/")

        yield from self.parse(response.replace(body=data))

    def parse_event(self, response):
        bouts = response.css(
            "div.fightCardMatchup > table > tr > td > span.billing > a::attr(href)"
        )
        bout_urls = [response.urljoin(url.get()) for url in bouts]

        yield from response.follow_all(bout_urls, self.parse_bout)

    def parse_bout(self, response):
        pass

    def parse_fighter(self, response):
        pass


class UFCRankingsSpider(Spider):
    pass


class UpcomingEventSpider(Spider):
    pass


class FightOddsIOSpider(Spider):
    pass
