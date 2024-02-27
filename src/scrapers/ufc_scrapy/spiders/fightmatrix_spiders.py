# standard library imports
import time

# third party imports
import pandas as pd
import w3lib.html
from scrapy.spiders import Spider

# local imports
from src.scrapers.ufc_scrapy.items import (
    FightMatrixBoutELOItem,
    FightMatrixFighterItem,
    FightMatrixRankingItem,
)


class FightMatrixFightersSpider(Spider):
    """
    Spider for scraping FightMatrix fighter profiles and
    ELO rating history
    """

    name = "fightmatrix_fighters_spider"
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
            "ufc_scrapy.scrapy_pipelines.fightmatrix_pipelines.FightMatrixFighterEloHistoryPipeline": 200,
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
        sherdog_fighter_id = None
        for link in fighter_links:
            if "sherdog" in link:
                sherdog_fighter_id = link.split("/")[-1].strip()
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

        yield fighter_item

        # ELO rating history
        bout_history_table = response.css("table.tblRank[style='width:845px']")
        rows = bout_history_table.css("tr[onmouseout='UnTip()']")
        for row in rows:
            bout_elo_item = FightMatrixBoutELOItem()

            bout_elo_item["FIGHTER_ID"] = response.url.replace(
                "https://www.fightmatrix.com/fighter-profile/", ""
            )

            tds = row.css("td")
            bout_elo_item["OUTCOME"] = tds[0].css("b::text").get().strip()
            bout_elo_item["OPPONENT_ID"] = (
                tds[1]
                .css("strong > a.sherLink::attr(href)")
                .get()
                .replace("/fighter-profile/", "")
            )
            bout_elo_item["OPPONENT_NAME"] = (
                tds[1].css("strong > a.sherLink::text").get().strip()
            )
            bout_elo_item["EVENT_NAME"] = tds[2].css("strong > a::text").get().strip()
            bout_elo_item["EVENT_ID"] = (
                tds[2].css("strong > a::attr(href)").get().replace("/event/", "")
            )
            bout_elo_item["DATE"] = pd.to_datetime(
                tds[2].css("em::text").get().strip()
            ).strftime("%Y-%m-%d")

            outcome_details = [x.strip() for x in tds[3].css("::text").getall()]
            assert len(outcome_details) == 2

            bout_elo_item["OUTCOME_METHOD"] = outcome_details[0]
            end_round = int(outcome_details[1].split(" ")[-1])
            bout_elo_item["END_ROUND"] = end_round if end_round != 0 else None

            elo_string = (
                w3lib.html.remove_tags(row.css("::attr(onmouseover)").get().strip())
                .replace("LoadCustomData('stat','", "")
                .replace("'); TagToTip('tip_div')", "")
            )
            elo_string_split = elo_string.split("|")
            assert len(elo_string_split) == 18

            bout_elo_item["ELO_K170_PRE"] = int(elo_string_split[6])
            bout_elo_item["ELO_K170_POST"] = int(elo_string_split[7])
            bout_elo_item["OPPONENT_ELO_K170_PRE"] = int(elo_string_split[8])
            bout_elo_item["OPPONENT_ELO_K170_POST"] = int(elo_string_split[9])
            bout_elo_item["ELO_MODIFIED_PRE"] = int(elo_string_split[10])
            bout_elo_item["ELO_MODIFIED_POST"] = int(elo_string_split[11])
            bout_elo_item["OPPONENT_ELO_MODIFIED_PRE"] = int(elo_string_split[12])
            bout_elo_item["OPPONENT_ELO_MODIFIED_POST"] = int(elo_string_split[13])
            bout_elo_item["GLICKO1_PRE"] = int(elo_string_split[14])
            bout_elo_item["GLICKO1_POST"] = int(elo_string_split[15])
            bout_elo_item["OPPONENT_GLICKO1_PRE"] = int(elo_string_split[16])
            bout_elo_item["OPPONENT_GLICKO1_POST"] = int(elo_string_split[17])

            yield bout_elo_item


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
