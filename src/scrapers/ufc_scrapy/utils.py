# standard library imports

# local imports

# third party imports


def extract_record(record):
    splitted = record.split(r" (")
    nc = 0
    if len(splitted) == 2:
        nc = int(splitted[1].replace(r" NC)", ""))
    wins, losses, draws = [int(x) for x in splitted[0].split("-")]

    return (wins, losses, draws, nc)


def convert_height(height):
    if height != "--":
        feet, inches = height.split()
        return 12.0 * float(feet[:-1]) + float(inches[:-1])
    else:
        return None


def total_time(form, rnd, tm):
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

    if form in nothing:
        return tm
    elif form == "1 Rnd + OT (31-5)":
        return tm + 31 * (rnd - 1)
    elif form in thirty_OT:
        return tm + 30 * (rnd - 1)
    elif form == "1 Rnd + OT (27-3)":
        return tm + 27 * (rnd - 1)
    elif form in fifteen_OT:
        return tm + 15 * (rnd - 1)
    elif form == "1 Rnd + OT (12-3)":
        return tm + 12 * (rnd - 1)
    elif form in tens:
        return tm + 10 * (rnd - 1)
    elif form == "3 Rnd (8-8-8)":
        return tm + 8 * (rnd - 1)
    elif form in fives:
        return tm + 5 * (rnd - 1)
    elif form in fours:
        return tm + 4 * (rnd - 1)
    elif form in threes:
        return tm + 3 * (rnd - 1)
    elif form == "3 Rnd (2-2-2)":
        return tm + 2 * (rnd - 1)
    elif form == "1 Rnd + 2OT (24-3-3)":
        if rnd == 1:
            return tm
        else:
            return 24 + tm + 3 * (rnd - 2)
    elif form == "1 Rnd + 2OT (15-3-3)":
        if rnd == 1:
            return tm
        else:
            return 15 + tm + 3 * (rnd - 2)
    elif form == "3 Rnd (10-5-5)":
        if rnd == 1:
            return tm
        else:
            return 10 + 5 * (rnd - 2)


def extract_landed_attempted(x):
    splitted = x.split(" of ")
    return (int(splitted[0]), int(splitted[1]))


def ctrl_time(x):
    if x == "--":
        return None
    else:
        temp = x.split(":")
        return int(temp[0]) + (int(temp[1]) / 60.0)