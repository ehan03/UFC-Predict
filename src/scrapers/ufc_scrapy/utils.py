# standard library imports
from typing import Optional, Tuple

# local imports

# third party imports


def extract_record(record: str) -> Tuple[int, int, int, int]:
    """
    Extracts the wins, losses, draws, and no contests from a record string
    """

    splitted = record.split(r" (")
    nc = 0
    if len(splitted) == 2:
        nc = int(splitted[1].replace(r" NC)", ""))
    wins, losses, draws = [int(x) for x in splitted[0].split("-")]

    return (wins, losses, draws, nc)


def convert_height(height: str) -> Optional[float]:
    """
    Converts a height string to inches
    """

    if height != "--":
        feet, inches = height.split()
        return 12.0 * float(feet[:-1]) + float(inches[:-1])
    else:
        return None


def total_time(format: str, end_round: int, end_round_time_seconds: int) -> int:
    """
    Calculates the total time of a bout in seconds
    """

    nothing = {
        "No Time Limit",
        "1 Rnd (20)",
        "1 Rnd (30)",
        "1 Rnd (15)",
        "1 Rnd (18)",
        "1 Rnd (10)",
        "1 Rnd (12)",
        "Unlimited Rnd (10)",
        "Unlimited Rnd  (15)",
        "Unlimited Rnd (20)",
    }
    thirty_OT = {"1 Rnd + OT (30-5)", "1 Rnd + OT (30-3)"}
    fifteen_OT = {"1 Rnd + OT (15-3)", "1 Rnd + OT (15-10)"}
    tens = {
        "3 Rnd (10-10-10)",
        "4 Rnd (10-10-10-10)",
        "2 Rnd (10-10)",
        "3 Rnd (10-10-5)",
        "2 Rnd (10-5)",
    }
    fives = {
        "2 Rnd (5-5)",
        "3 Rnd (5-5-5)",
        "5 Rnd (5-5-5-5-5)",
        "3 Rnd + OT (5-5-5-5)",
    }
    fours = {"3 Rnd (4-4-4)", "5 Rnd (4-4-4-4-4)"}
    threes = {"5 Rnd (3-3-3-3-3)", "3 Rnd (3-3-3)", "2 Rnd (3-3)"}

    if format in nothing:
        return end_round_time_seconds
    elif format == "1 Rnd + OT (31-5)":
        return end_round_time_seconds + 31 * 60 * (end_round - 1)
    elif format in thirty_OT:
        return end_round_time_seconds + 30 * 60 * (end_round - 1)
    elif format == "1 Rnd + OT (27-3)":
        return end_round_time_seconds + 27 * 60 * (end_round - 1)
    elif format in fifteen_OT:
        return end_round_time_seconds + 15 * 60 * (end_round - 1)
    elif format == "1 Rnd + OT (12-3)":
        return end_round_time_seconds + 12 * 60 * (end_round - 1)
    elif format in tens:
        return end_round_time_seconds + 10 * 60 * (end_round - 1)
    elif format == "3 Rnd (8-8-8)":
        return end_round_time_seconds + 8 * 60 * (end_round - 1)
    elif format in fives:
        return end_round_time_seconds + 5 * 60 * (end_round - 1)
    elif format in fours:
        return end_round_time_seconds + 4 * 60 * (end_round - 1)
    elif format in threes:
        return end_round_time_seconds + 3 * 60 * (end_round - 1)
    elif format == "3 Rnd (2-2-2)":
        return end_round_time_seconds + 2 * 60 * (end_round - 1)
    elif format == "1 Rnd + 2OT (24-3-3)":
        if end_round == 1:
            return end_round_time_seconds
        else:
            return 24 * 60 + end_round_time_seconds + 3 * 60 * (end_round - 2)
    elif format == "1 Rnd + 2OT (15-3-3)":
        if end_round == 1:
            return end_round_time_seconds
        else:
            return 15 * 60 + end_round_time_seconds + 3 * 60 * (end_round - 2)
    elif format == "3 Rnd (10-5-5)":
        if end_round == 1:
            return end_round_time_seconds
        else:
            return 10 * 60 + 5 * 60 * (end_round - 2)
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
        return (int(temp[0]) * 60) + int(temp[1])


def get_missing_fightmatrix_stats():
    pass
