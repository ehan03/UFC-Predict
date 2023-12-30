# standard library imports
from typing import List, Optional, Tuple

# local imports

# third party imports


def convert_height(height: str) -> Optional[int]:
    """
    Converts a height string to inches
    """

    if height != "--":
        feet, inches = height.split()
        return 12 * int(feet[:-1]) + int(inches[:-1])
    else:
        return None


def total_time(
    format: str, end_round: int, end_round_time_seconds: int
) -> Tuple[int, List[int]]:
    """
    Calculates the total time of a bout in seconds and per-round times
    """

    one_round = {
        "No Time Limit",
        "1 Rnd (20)",
        "1 Rnd (30)",
        "1 Rnd (15)",
        "1 Rnd (18)",
        "1 Rnd (10)",
        "1 Rnd (12)",
    }
    thirty_OT = {
        "1 Rnd + OT (30-5)",
        "1 Rnd + OT (30-3)",
    }
    fives = {
        "2 Rnd (5-5)",
        "3 Rnd (5-5-5)",
        "5 Rnd (5-5-5-5-5)",
        "3 Rnd + OT (5-5-5-5)",
    }

    if format in one_round:
        return end_round_time_seconds, [end_round_time_seconds]
    elif format in thirty_OT:
        return end_round_time_seconds + 30 * 60 * (end_round - 1), [30 * 60] * (
            end_round - 1
        ) + [end_round_time_seconds]
    elif format in fives:
        return end_round_time_seconds + 5 * 60 * (end_round - 1), [5 * 60] * (
            end_round - 1
        ) + [end_round_time_seconds]
    elif format == "1 Rnd + OT (31-5)":
        return end_round_time_seconds + 31 * 60 * (end_round - 1), [31 * 60] * (
            end_round - 1
        ) + [end_round_time_seconds]
    elif format == "1 Rnd + OT (27-3)":
        return end_round_time_seconds + 27 * 60 * (end_round - 1), [27 * 60] * (
            end_round - 1
        ) + [end_round_time_seconds]
    elif format == "1 Rnd + OT (12-3)":
        return end_round_time_seconds + 12 * 60 * (end_round - 1), [12 * 60] * (
            end_round - 1
        ) + [end_round_time_seconds]
    elif format == "1 Rnd + OT (15-3)":
        return end_round_time_seconds + 15 * 30 * (end_round - 1), [15 * 30] * (
            end_round - 1
        ) + [end_round_time_seconds]
    elif format == "1 Rnd + 2OT (24-3-3)":
        if end_round == 1:
            return end_round_time_seconds, [end_round_time_seconds]
        else:
            return 24 * 60 + end_round_time_seconds + 3 * 60 * (end_round - 2), [
                24 * 60
            ] + [3 * 60] * (end_round - 2) + [end_round_time_seconds]
    elif format == "1 Rnd + 2OT (15-3-3)":
        if end_round == 1:
            return end_round_time_seconds, [end_round_time_seconds]
        else:
            return 15 * 60 + end_round_time_seconds + 3 * 60 * (end_round - 2), [
                15 * 60
            ] + [3 * 60] * (end_round - 2) + [end_round_time_seconds]
    else:
        raise ValueError(f"Unknown format: {format}")


def extract_landed_attempted(landed_attempted: str) -> Tuple[int, int]:
    """
    Extracts the landed and attempted strikes from a string
    """

    splitted = landed_attempted.split(" of ")
    return (int(splitted[0]), int(splitted[1]))


def ctrl_time(time: str) -> Optional[int]:
    """
    Converts a string of the form MM:SS to seconds for control time
    """

    if time == "--":
        return None
    else:
        temp = time.split(":")
        return 60 * int(temp[0]) + int(temp[1])


EVENTS_RECENT_GQL_QUERY = """
query EventsPromotionRecentQuery(
  $promotionSlug: String
  $dateLt: Date
  $after: String
  $first: Int
  $orderBy: String
) {
  promotion: promotionBySlug(slug: $promotionSlug) {
    ...EventsPromotionTabPanel_promotion_34GGrn
    id
  }
}

fragment EventCardList_events on EventNodeConnection {
  edges {
    node {
      ...EventCard_event
    }
  }
}

fragment EventCard_event on EventNode {
  name
  pk
  slug
  date
  venue
  city
}

fragment EventsPromotionTabPanel_promotion_34GGrn on PromotionNode {
  ...PromotionEventCardListInfiniteScroll_promotion_34GGrn
}

fragment PromotionEventCardListInfiniteScroll_promotion_34GGrn on PromotionNode {
  events(first: $first, after: $after, date_Lt: $dateLt, orderBy: $orderBy) {
    ...EventCardList_events
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""

FIGHTS_GQL_QUERY = """
query EventFightsQuery(
  $eventPk: Int
) {
  event: eventByPk(pk: $eventPk) {
    pk
    slug
    fights {
      ...EventTabPanelFights_fights
    }
    id
  }
}

fragment EventTabPanelFights_fights on FightNodeConnection {
  edges {
    node {
      id
    }
  }
  ...FightTable_fights
  ...FightCardList_fights
}

fragment FightCardList_fights on FightNodeConnection {
  edges {
    node {
      ...FightCard_fight
      id
    }
  }
}

fragment FightCard_fight on FightNode {
  id
  fighter1 {
    id
    firstName
    lastName
    slug
  }
  fighter2 {
    id
    firstName
    lastName
    slug
  }
  fighterWinner {
    id
  }
  order
  weightClass {
    weightClass
    weight
    id
  }
  fighter1Odds
  fighter2Odds
  fightType
  methodOfVictory1
  methodOfVictory2
  round
  duration
  slug
}

fragment FightTable_fights on FightNodeConnection {
  edges {
    node {
      id
      fighter1 {
        id
        firstName
        lastName
        slug
      }
      fighter2 {
        id
        firstName
        lastName
        slug
      }
      fighterWinner {
        id
        firstName
        lastName
        slug
      }
      order
      weightClass {
        weightClass
        weight
        id
      }
      isCancelled
      fightType
      methodOfVictory1
      methodOfVictory2
      round
      duration
      slug
    }
  }
}
"""

FIGHTERS_GQL_QUERY = """
query FighterQuery(
  $fighterSlug: String
) {
  fighter: fighterBySlug(slug: $fighterSlug) {
    ...FighterTabPanelInfo_fighter
  }
}

fragment FighterTabPanelInfo_fighter on FighterNode {
  ...FighterTableInfo_fighter
  ...FighterTableFightingStyle_fighter
}

fragment FighterTableFightingStyle_fighter on FighterNode {
  stance
}

fragment FighterTableInfo_fighter on FighterNode {
  firstName
  lastName
  birthDate
  nationality
  height
  reach
  legReach
  fightingStyle
}
"""
