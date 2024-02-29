# standard library imports
import json
from datetime import datetime, timedelta, timezone

# third party imports
import numpy as np
from scrapy.http import Request
from scrapy.spiders import Spider

# local imports
from src.scrapers.ufc_scrapy.items import (
    FightOddsIOBoutItem,
    FightOddsIOClosingOddsItem,
    FightOddsIOFighterItem,
    FightOddsIOUpcomingBoutItem,
)
from src.scrapers.ufc_scrapy.utils import (
    EVENT_ODDS_GQL_QUERY,
    EVENTS_RECENT_GQL_QUERY,
    EVENTS_UPCOMING_GQL_QUERY,
    FIGHTERS_GQL_QUERY,
    FIGHTS_GQL_QUERY,
)


class FightOddsIOResultsSpider(Spider):
    """
    Spider for scraping historical fighter and bout data from FightOdds.io
    """

    name = "fightoddsio_results_spider"
    allowed_domains = ["fightodds.io"]
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
        "RETRY_TIMES": 1,
        "LOG_LEVEL": "INFO",
        "LOG_FORMATTER": "ufc_scrapy.logformatter.PoliteLogFormatter",
        "ITEM_PIPELINES": {
            "ufc_scrapy.scrapy_pipelines.fightoddsio_pipelines.FightOddsIOFightersPipeline": 100,
            "ufc_scrapy.scrapy_pipelines.fightoddsio_pipelines.FightOddsIOCompletedBoutsPipeline": 200,
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
        self.date_today = datetime.now(timezone.utc).date()

        # Bookmakers to target (don't do live odds as closing odds)
        self.bookie_slugs_target = {
            "betonline",
            "bovada",
            "betus",
            "sx-bet",
            "jazz-sports",
            "unibet",
            "betanysports",
        }

        # Weird cases as a result of the website and its DB having awful design
        self.edge_case_bout_slugs = {
            "gegard-mousasi-vs-mark-munoz-9476",
            "cb-dollaway-vs-francis-carmont-9528",
            "sean-strickland-vs-luke-barnatt-9586",
            "niklas-backstrom-vs-tom-niinimaki-9641",
            "nick-hein-vs-drew-dober-9701",
            "magnus-cedenblad-vs-krzysztof-jotko-9760",
            "iuri-alcantara-vs-vaughan-lee-9816",
            "peter-sobotta-vs-pawel-pawlak-9873",
            "maximo-blanco-vs-andy-ogle-9925",
            "ruslan-magomedov-vs-viktor-pesta-9981",
        }
        self.duplicates = {
            "ross-pearson-vs-george-sotiropoulos-9465",
            "robert-whittaker-vs-bradley-scott-9516",
            "norman-parke-vs-colin-fletcher-9575",
            "hector-lombard-vs-rousimar-palhares-9631",
            "chad-mendes-vs-yaotzin-meza-9688",
            "joey-beltran-vs-igor-pokrajac-9747",
            "mike-pierce-vs-seth-baczynski-9802",
            "benny-alloway-vs-manuel-rodriguez-9861",
            "mike-wilkinson-vs-brendan-loughnane-9914",
            "cody-donovan-vs-nick-penner-9968",
            "anthony-macias-vs-he-man-ali-gipson-265",
            "heather-clark-vs-bec-rawlings-9842",
            "masio-fullen-vs-alex-torres-10056",
        }
        self.dont_exist = {
            "ken-shamrock-vs-tito-ortiz-8826",
            "pascal-krauss-vs-adam-khaliev-9215",
            "pascal-krauss-vs-adam-aliev-9279",
            "ion-cutelaba-vs-luiz-philipe-lins-49546",
            "justin-willis-vs-allen-crowder-20870",
        }
        self.falsely_cancelled = {
            "alexander-hernandez-vs-beneil-dariush-22185",
            "cm-punk-vs-mike-jackson-22023",
        }

    def start_requests(self):
        payload = json.dumps(
            {
                "query": EVENTS_RECENT_GQL_QUERY,
                "variables": {
                    "promotionSlug": "ufc",
                    "dateLt": self.date_today.strftime("%Y-%m-%d"),
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

            if "UFC" not in event_name and "The Ultimate Fighter" not in event_name:
                continue

            if edge["node"]["slug"] == "ufc-fight-night-85-hunt-vs-mir":
                edge["node"]["date"] = "2016-03-19"

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
                cb_kwargs={"info_dict": edge, "pk": pk},
            )

        has_next_page = events["pageInfo"]["hasNextPage"]
        if has_next_page and self.scrape_type == "all":
            cursor_pos = events["pageInfo"]["endCursor"]
            payload_pagination = json.dumps(
                {
                    "query": EVENTS_RECENT_GQL_QUERY,
                    "variables": {
                        "promotionSlug": "ufc",
                        "dateLt": self.date_today.strftime("%Y-%m-%d"),
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

    def parse_event_fights(self, response, info_dict, pk):
        json_resp = json.loads(response.body)
        edges = json_resp["data"]["event"]["fights"]["edges"]
        confirmed = [
            edge
            for edge in edges
            if not edge["node"]["isCancelled"]
            or edge["node"]["slug"] in self.falsely_cancelled
        ]

        valid_bout_slugs = []
        for bout in confirmed:
            if (
                bout["node"]["slug"] in self.duplicates
                or bout["node"]["slug"] in self.dont_exist
            ):
                continue

            bout_item = FightOddsIOBoutItem()

            bout_slug = bout["node"]["slug"]
            bout_item["BOUT_SLUG"] = bout_slug
            bout_item["EVENT_SLUG"] = info_dict["node"]["slug"]
            bout_item["EVENT_NAME"] = info_dict["node"]["name"].strip()
            bout_item["DATE"] = info_dict["node"]["date"]
            bout_item["LOCATION"] = info_dict["node"]["city"].strip()
            bout_item["VENUE"] = info_dict["node"]["venue"].strip()
            bout_item["BOUT_ORDINAL"] = -1 * bout["node"]["order"]

            if bout["node"]["slug"] in self.edge_case_bout_slugs:
                bout_item["EVENT_SLUG"] = "ufc-fight-night-41-munoz-vs-mousasi"
                bout_item["EVENT_NAME"] = "UFC Fight Night 41: Munoz vs. Mousasi"
                bout_item["LOCATION"] = "Berlin, Germany"
                bout_item["VENUE"] = "O2 World Arena"

            if info_dict["node"]["slug"] == "ufc-fight-night-65-miocic-vs-hunt":
                bout_item["LOCATION"] = "Adelaide, South Australia"
                bout_item["VENUE"] = "Adelaide Entertainment Center"

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

            # Filter out cancelled events not marked cancelled
            if (
                bout_item["END_ROUND"]
                or bout_item["END_ROUND_TIME_SECONDS"] is not None
            ):
                yield bout_item

                valid_bout_slugs.append(bout_slug)

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

        payload_odds = json.dumps(
            {"query": EVENT_ODDS_GQL_QUERY, "variables": {"eventPk": pk}}
        )

        yield Request(
            url=self.gql_url,
            method="POST",
            headers=self.headers,
            body=payload_odds,
            callback=self.parse_bout_odds,
            dont_filter=True,
            cb_kwargs={"valid_bout_slugs": valid_bout_slugs},
        )

    def parse_fighter(self, response, fighter_slug):
        json_resp = json.loads(response.body)
        fighter_data = json_resp["data"]["fighter"]

        fighter_item = FightOddsIOFighterItem()

        fighter_item["FIGHTER_SLUG"] = fighter_slug
        fighter_item["FIGHTER_NAME"] = (
            f"{fighter_data['firstName']} {fighter_data['lastName']}".strip()
        )
        fighter_item["FIGHTER_NICKNAME"] = (
            fighter_data["nickName"] if fighter_data["nickName"] else None
        )
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
        # 1970-01-01 used as placeholder for missing DOB
        fighter_item["DATE_OF_BIRTH"] = (
            fighter_data["birthDate"]
            if fighter_data["birthDate"] and fighter_data["birthDate"] != "1970-01-01"
            else None
        )

        yield fighter_item

    def parse_bout_odds(self, response, valid_bout_slugs):
        json_resp = json.loads(response.body)

        if json_resp["data"]["eventOfferTable"]:
            fightoffer_edges = json_resp["data"]["eventOfferTable"]["fightOffers"][
                "edges"
            ]
            valid = [
                edge
                for edge in fightoffer_edges
                if edge["node"]["slug"] in valid_bout_slugs
            ]

            for bout in valid:
                bout_slug = bout["node"]["slug"]

                closing_odds_item = FightOddsIOClosingOddsItem()
                closing_odds_item["BOUT_SLUG"] = bout_slug
                f1_odds = []
                f2_odds = []

                seen = set()
                for offer in bout["node"]["straightOffers"]["edges"]:
                    if offer["node"]["sportsbook"]["slug"] in self.bookie_slugs_target:
                        if offer["node"]["sportsbook"]["slug"] in seen:
                            # just take first one, there are some weird duplicate edge cases
                            continue
                        seen.add(offer["node"]["sportsbook"]["slug"])

                        if offer["node"]["outcome1"]:
                            if offer["node"]["outcome1"]["odds"]:
                                f1_odds.append(offer["node"]["outcome1"]["odds"])

                        if offer["node"]["outcome2"]:
                            if offer["node"]["outcome2"]["odds"]:
                                f2_odds.append(offer["node"]["outcome2"]["odds"])

                if f1_odds or f2_odds:
                    closing_odds_item["FIGHTER_1_ODDS"] = self.get_average_decimal_odds(
                        np.array(f1_odds)
                    )
                    closing_odds_item["FIGHTER_2_ODDS"] = self.get_average_decimal_odds(
                        np.array(f2_odds)
                    )

                    yield closing_odds_item

    def get_average_decimal_odds(self, odds):
        if not odds.size:
            return None

        decimal_odds = np.where(odds > 0, odds / 100 + 1, -100 / odds + 1)

        return np.round(np.mean(decimal_odds), 6)


class FightOddsIOUpcomingEventSpider(Spider):
    """
    Spider for scraping upcoming UFC event data from FightOdds.io
    """

    name = "fightoddsio_upcoming_spider"
    allowed_domains = ["fightodds.io"]
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
        "RETRY_TIMES": 1,
        "LOG_LEVEL": "INFO",
        "LOG_FORMATTER": "ufc_scrapy.logformatter.PoliteLogFormatter",
        "ITEM_PIPELINES": {
            "ufc_scrapy.scrapy_pipelines.fightoddsio_pipelines.FightOddsIOUpcomingBoutsPipeline": 100,
        },
        "CLOSESPIDER_ERRORCOUNT": 1,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.gql_url = "https://api.fightinsider.io/gql"
        self.headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/json",
        }
        self.date_today = datetime.now(timezone.utc).date()

    def start_requests(self):
        payload = json.dumps(
            {
                "query": EVENTS_UPCOMING_GQL_QUERY,
                "variables": {
                    "promotionSlug": "ufc",
                    "dateGte": self.date_today.strftime("%Y-%m-%d"),
                    "after": "",
                    "first": 10,
                    "orderBy": "date",
                },
            }
        )

        yield Request(
            url=self.gql_url,
            method="POST",
            headers=self.headers,
            body=payload,
            callback=self.parse_upcoming_event,
            dont_filter=True,
        )

    def parse_upcoming_event(self, response):
        json_resp = json.loads(response.body)
        upcoming_event_edge = json_resp["data"]["promotion"]["events"]["edges"][0]

        event_name = upcoming_event_edge["node"]["name"]
        event_pk = upcoming_event_edge["node"]["pk"]
        event_date = upcoming_event_edge["node"]["date"]

        next_saturday = (
            self.date_today + timedelta((5 - self.date_today.weekday()) % 7)
        ).strftime("%Y-%m-%d")

        if event_date == next_saturday and (
            "UFC" in event_name or "The Ultimate Fighter" in event_name
        ):
            payload_event_odds = json.dumps(
                {"query": EVENT_ODDS_GQL_QUERY, "variables": {"eventPk": event_pk}}
            )

            yield Request(
                url=self.gql_url,
                method="POST",
                headers=self.headers,
                body=payload_event_odds,
                callback=self.parse_upcoming_bout_odds,
                dont_filter=True,
                cb_kwargs={"info_dict": upcoming_event_edge},
            )

    def parse_upcoming_bout_odds(self, response, info_dict):
        json_resp = json.loads(response.body)
        fightoffer_edges = json_resp["data"]["eventOfferTable"]["fightOffers"]["edges"]
        confirmed = [
            edge for edge in fightoffer_edges if not edge["node"]["isCancelled"]
        ]

        for bout in confirmed:
            upcoming_bout_item = FightOddsIOUpcomingBoutItem()

            upcoming_bout_item["BOUT_SLUG"] = bout["node"]["slug"]
            upcoming_bout_item["EVENT_SLUG"] = info_dict["node"]["slug"]
            upcoming_bout_item["EVENT_NAME"] = info_dict["node"]["name"].strip()
            upcoming_bout_item["DATE"] = info_dict["node"]["date"]
            upcoming_bout_item["LOCATION"] = info_dict["node"]["city"].strip()
            upcoming_bout_item["VENUE"] = info_dict["node"]["venue"].strip()

            f1_slug = bout["node"]["fighter1"]["slug"]
            f2_slug = bout["node"]["fighter2"]["slug"]
            upcoming_bout_item["FIGHTER_1_SLUG"] = f1_slug
            upcoming_bout_item["FIGHTER_2_SLUG"] = f2_slug

            f1_odds_draftkings = f2_odds_draftkings = None
            for offer in bout["node"]["straightOffers"]["edges"]:
                if offer["node"]["sportsbook"]["slug"] == "draftkings":
                    f1_odds_draftkings = offer["node"]["outcome1"]["odds"]
                    f2_odds_draftkings = offer["node"]["outcome2"]["odds"]
                    break
            assert f1_odds_draftkings is not None and f2_odds_draftkings is not None

            upcoming_bout_item["FIGHTER_1_ODDS_DRAFTKINGS"] = f1_odds_draftkings
            upcoming_bout_item["FIGHTER_2_ODDS_DRAFTKINGS"] = f2_odds_draftkings

            yield upcoming_bout_item
