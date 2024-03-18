# standard library imports
import time

# third party imports
import pandas as pd
import w3lib.html
from scrapy.spiders import Spider

# local imports
from src.scrapers.ufc_scrapy.items import (
    FightMatrixBoutItem,
    FightMatrixFighterItem,
    FightMatrixRankingItem,
)


class FightMatrixResultsSpider(Spider):
    """
    Spider for scraping FightMatrix fighter profiles and
    Elo rating history
    """

    name = "fightmatrix_results_spider"
    allowed_domains = ["fightmatrix.com"]
    start_urls = ["https://www.fightmatrix.com/past-events-search/?org=UFC"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "CONCURRENT_REQUESTS": 1,
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
            "ufc_scrapy.scrapy_pipelines.fightmatrix_pipelines.FightMatrixFightersPipeline": 100,
            "ufc_scrapy.scrapy_pipelines.fightmatrix_pipelines.FightMatrixBoutsPipeline": 200,
        },
        "CLOSESPIDER_ERRORCOUNT": 1,
        "DOWNLOAD_DELAY": 1.5,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 1.5,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 1,
        "AUTOTHROTTLE_MAX_DELAY": 5,
    }

    def __init__(self, *args, scrape_type, **kwargs):
        """
        Initialize FightMatrixFightersSpider
        """

        super().__init__(*args, **kwargs)
        assert scrape_type in {"most_recent", "all"}
        self.scrape_type = scrape_type

    def parse(self, response):
        events = response.css(
            """table.tblRank[style='width:945px; border-collapse: collapse; border: 0px solid black'] 
            > tr"""
        )

        event_links = []
        for event in events[1:]:
            event_link = event.css(
                """td[style='border: 0px solid black; text-align: left'] 
                > a.redLink::attr(href)"""
            ).get()
            event_name = (
                event.css(
                    """td[style='border: 0px solid black; text-align: left']
                    > a.redLink::text"""
                )
                .get()
                .strip()
            )

            if "Road to UFC" in event_name:
                continue

            event_links.append(event_link)

        if self.scrape_type == "most_recent":
            event_links = [event_links[0]]

        yield from response.follow_all(event_links, self.parse_event)

    def parse_event(self, response):
        fighter_links = response.css("a.sherLink::attr(href)").getall()

        yield from response.follow_all(
            [
                response.urljoin(link)
                for link in fighter_links
                if "fighter-profile" in link
            ],
            self.parse_fighter,
        )

        event_id = int(response.url.split("/")[-2])
        event_name = response.css("H1 > a::text").get().strip()
        event_date = pd.to_datetime(
            w3lib.html.remove_tags(response.css("H3").get())
            .strip()
            .replace("UFC, ", "")
        ).strftime("%Y-%m-%d")

        table = response.css("table.tblRank")
        rows = table.css("tr")[1:]
        for row in rows:
            bout_item = FightMatrixBoutItem()

            bout_item["EVENT_ID"] = event_id
            bout_item["EVENT_NAME"] = event_name
            bout_item["DATE"] = event_date

            tds = row.css("td")
            bout_item["BOUT_ORDINAL"] = int(tds[0].css("::text").get().strip()) - 1
            bout_item["FIGHTER_1_ID"] = int(
                tds[2].css("a::attr(href)").get().split("/")[-2]
            )
            f1_elo_string_split = (
                w3lib.html.remove_tags(tds[2].css("::attr(onmouseover)").get().strip())
                .replace("LoadCustomData('stat','|", "")
                .replace("|'); TagToTip('tip_div')", "")
            ).split("|")
            assert len(f1_elo_string_split) == 6

            bout_item["FIGHTER_1_ELO_K170_PRE"] = int(f1_elo_string_split[0])
            bout_item["FIGHTER_1_ELO_K170_POST"] = int(f1_elo_string_split[1])
            bout_item["FIGHTER_1_ELO_MODIFIED_PRE"] = int(f1_elo_string_split[2])
            bout_item["FIGHTER_1_ELO_MODIFIED_POST"] = int(f1_elo_string_split[3])
            bout_item["FIGHTER_1_GLICKO1_PRE"] = int(f1_elo_string_split[4])
            bout_item["FIGHTER_1_GLICKO1_POST"] = int(f1_elo_string_split[5])

            outcome_split = [
                x.strip() for x in tds[2].css("p::text").get().split(" - ")
            ]
            assert len(outcome_split) == 3
            bout_item["FIGHTER_1_OUTCOME"] = outcome_split[0]
            bout_item["FIGHTER_2_OUTCOME"] = (
                "L" if outcome_split[0] == "W" else outcome_split[0]
            )
            method_split = outcome_split[1].split(" (")
            bout_item["OUTCOME_METHOD"] = method_split[0] if method_split[0] else None
            bout_item["OUTCOME_METHOD_DETAILS"] = (
                method_split[1].replace(")", "") if len(method_split) > 1 else None
            )
            bout_item["END_ROUND"] = int(outcome_split[2].split(" ")[-1])

            bout_item["FIGHTER_2_ID"] = int(
                tds[4].css("a::attr(href)").get().split("/")[-2]
            )
            f2_elo_string_split = (
                w3lib.html.remove_tags(tds[4].css("::attr(onmouseover)").get().strip())
                .replace("LoadCustomData('stat','|", "")
                .replace("|'); TagToTip('tip_div')", "")
            ).split("|")
            assert len(f2_elo_string_split) == 6

            bout_item["FIGHTER_2_ELO_K170_PRE"] = int(f2_elo_string_split[0])
            bout_item["FIGHTER_2_ELO_K170_POST"] = int(f2_elo_string_split[1])
            bout_item["FIGHTER_2_ELO_MODIFIED_PRE"] = int(f2_elo_string_split[2])
            bout_item["FIGHTER_2_ELO_MODIFIED_POST"] = int(f2_elo_string_split[3])
            bout_item["FIGHTER_2_GLICKO1_PRE"] = int(f2_elo_string_split[4])
            bout_item["FIGHTER_2_GLICKO1_POST"] = int(f2_elo_string_split[5])

            bout_item["WEIGHT_CLASS"] = tds[5].css("::text").get().strip()

            yield bout_item

    def parse_fighter(self, response):
        fighter_item = FightMatrixFighterItem()

        fighter_item["FIGHTER_NAME"] = (
            response.css("div.posttitle > h1 > a::text").get().strip()
        )
        fighter_id = int(response.url.split("/")[-2])
        fighter_item["FIGHTER_ID"] = fighter_id

        fighter_links = response.css(
            "td.tdRankHead > div.leftCol *> a::attr(href)"
        ).getall()
        sherdog_fighter_id = None
        for link in fighter_links:
            if "sherdog" in link:
                sherdog_fighter_id = int(link.split("/")[-1].strip().split("-")[-1])
                break
        assert sherdog_fighter_id is not None

        fighter_item["SHERDOG_FIGHTER_ID"] = sherdog_fighter_id

        pro_debut_date = None
        td_rank_head_divs = response.css(
            """td.tdRankHead[style='text-align: left; border: 0px; width: 100%; font-weight: normal'] 
            > div.rightCol"""
        )
        for div in td_rank_head_divs:
            label = div.css("::text").get().strip()
            if label == "Pro Debut Date:":
                pro_debut_date = pd.to_datetime(
                    div.css("strong::text").get().strip()
                ).strftime("%Y-%m-%d")
                break
        fighter_item["PRO_DEBUT_DATE"] = pro_debut_date

        td_rank_alt_divs = response.css(
            """tr > td.tdRankAlt[style='border: 1px solid black; text-align: left; '] 
            > div.leftCol"""
        )
        for div in td_rank_alt_divs:
            label = div.css("::text").get().strip()
            if label == "UFC Debut:":
                fighter_item["UFC_DEBUT_DATE"] = pd.to_datetime(
                    div.css("strong::text").get().strip()
                ).strftime("%Y-%m-%d")
                break

        # Edge cases
        if fighter_id == 1002:
            fighter_item["UFC_DEBUT_DATE"] = "1999-01-08"
        elif fighter_id in [1614, 21940]:
            fighter_item["UFC_DEBUT_DATE"] = "1999-03-05"

        yield fighter_item


class FightMatrixRankingsSpider(Spider):
    """
    Spider for scraping FightMatrix rankings
    """

    name = "fightmatrix_rankings_spider"
    allowed_domains = ["fightmatrix.com"]
    start_urls = [
        "https://www.fightmatrix.com/historical-mma-rankings/ranking-snapshots/"
    ]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "CONCURRENT_REQUESTS": 1,
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
            "ufc_scrapy.scrapy_pipelines.fightmatrix_pipelines.FightMatrixRankingsPipeline": 100,
        },
        "CLOSESPIDER_ERRORCOUNT": 1,
        "DOWNLOAD_DELAY": 1.5,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 1.5,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 1,
        "AUTOTHROTTLE_MAX_DELAY": 5,
    }

    def __init__(self, *args, scrape_type, **kwargs):
        """
        Initialize FightMatrixRankingsSpider
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
            "13": "Women's Strawweight",
            "14": "Women's Flyweight",
            "15": "Women's Bantamweight",
            "16": "Women's Featherweight",
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
                    "2013-01-01", "%Y-%m-%d"
                ) and division in {"16", "15", "14", "13"}:
                    # Women's divisions didn't exist before 2013 in the UFC
                    continue

                if date == "2008-01-20":
                    # First issue date
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
            ranking_item["ISSUE_DATE"] = date
            ranking_item["WEIGHT_CLASS"] = weight_class

            cells = row.css("td")

            ranking_item["RANK"] = int(cells[0].css("::text").get().strip())

            fighter_link = cells[2].css("a::attr(href)").get()
            fighter_id = fighter_link.replace("/fighter-profile/", "")

            if fighter_id == "//":
                # Edge case for missing fighter
                continue

            fighter_id = int(fighter_id.split("/")[-2])
            ranking_item["FIGHTER_ID"] = fighter_id
            ranking_item["POINTS"] = int(cells[3].css("div.tdBar::text").get().strip())

            yield ranking_item

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
