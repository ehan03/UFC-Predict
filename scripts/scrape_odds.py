# Standard library imports
import json
import random

# Third-party imports
import requests

# Local imports
from useragents import AGENT_LIST


def get_upcoming_event():
    pass


def get_odds_for_event(event_pk):
    url = "https://api.fightinsider.io/gql"

    payload = json.dumps(
        {
            "query": "query EventOddsQuery(\n  $eventPk: Int!\n) {\n  sportsbooks: allSportsbooks(hasOdds: true) {\n    ...EventTabPanelOdds_sportsbooks\n  }\n  eventOfferTable(pk: $eventPk) {\n    slug\n    ...EventTabPanelOdds_eventOfferTable\n    id\n  }\n}\n\nfragment EventOfferTable_eventOfferTable on EventOfferTableNode {\n  name\n  pk\n  fightOffers {\n    edges {\n      node {\n        id\n        fighter1 {\n          firstName\n          lastName\n          slug\n          id\n        }\n        fighter2 {\n          firstName\n          lastName\n          slug\n          id\n        }\n        bestOdds1\n        bestOdds2\n        slug\n        propCount\n        isCancelled\n        straightOffers {\n          edges {\n            node {\n              sportsbook {\n                id\n                shortName\n                slug\n              }\n              outcome1 {\n                id\n                odds\n                ...OddsWithArrowButton_outcome\n              }\n              outcome2 {\n                id\n                odds\n                ...OddsWithArrowButton_outcome\n              }\n              id\n            }\n          }\n        }\n      }\n    }\n  }\n}\n\nfragment EventOfferTable_sportsbooks on SportsbookNodeConnection {\n  edges {\n    node {\n      id\n      shortName\n      slug\n    }\n  }\n}\n\nfragment EventTabPanelOdds_eventOfferTable on EventOfferTableNode {\n  fightOffers {\n    edges {\n      node {\n        id\n        isCancelled\n      }\n    }\n  }\n  ...EventOfferTable_eventOfferTable\n}\n\nfragment EventTabPanelOdds_sportsbooks on SportsbookNodeConnection {\n  ...EventOfferTable_sportsbooks\n}\n\nfragment OddsWithArrowButton_outcome on OutcomeNode {\n  id\n  ...OddsWithArrow_outcome\n}\n\nfragment OddsWithArrow_outcome on OutcomeNode {\n  odds\n  oddsPrev\n}\n",
            "variables": {"eventPk": event_pk},
        }
    )

    headers = {
        "authority": "api.fightinsider.io",
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://fightodds.io",
        "referer": "https://fightodds.io/",
        "user-agent": random.choice(AGENT_LIST),
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    response.raise_for_status()
    response_data = response.json()
    bout_odds = [
        x["node"]
        for x in response_data["data"]["eventOfferTable"]["fightOffers"]["edges"]
    ]

    return bout_odds
