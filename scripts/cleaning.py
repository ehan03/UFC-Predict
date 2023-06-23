import pandas as pd
import numpy as np

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
        return 12 * int(feet[:-1]) + int(inches[:-1])
    else:
        return np.nan

def clean_fighter_stats(fighter_stats):
    concat_dict = {}
    df = fighter_stats.copy()
    concat_dict["Wins"], concat_dict["Losses"], concat_dict["Draws"], concat_dict["NC"] = zip(*df["Record"].apply(lambda x: extract_record(x)))
    df["Height"] = df["Height"].apply(lambda x: convert_height(x))
    df["Weight"] = df["Weight"].apply(lambda x: float(x.replace(" lbs.", "")) if x != "--" else np.nan)
    df["Reach"] = df["Reach"].apply(lambda x: float(x.replace("\"", "")) if x != "--" else np.nan)
    df["DOB"] = df["DOB"].apply(lambda x: pd.to_datetime(x) if x != "--" else np.nan)
    df["SLpM"] = df["SLpM"].astype(float)
    df["Str. Acc."] = df["Str. Acc."].str.replace(r"%", "", regex=True).astype(float).divide(100)
    df["SApM"] = df["SApM"].astype(float)
    df["Str. Def."] = df["Str. Def."].str.replace(r"%", "", regex=True).astype(float).divide(100)
    df["TD Avg."] = df["TD Avg."].astype(float)
    df["TD Acc."] = df["TD Acc."].str.replace(r"%", "", regex=True).astype(float).divide(100)
    df["TD Def."] = df["TD Def."].str.replace(r"%", "", regex=True).astype(float).divide(100)
    df["Sub. Avg."] = df["Sub. Avg."].astype(float)
    
    temp = pd.DataFrame.from_dict(concat_dict)
    df2 = pd.concat([df, temp], axis=1)
    
    df2 = df2.drop(columns=["Record"])
    cols = ["Name", "Wins", "Losses", "Draws", "NC", "Height", "Weight", "Reach", "Stance", "DOB", "SLpM", "Str. Acc.", "SApM", "Str. Def.", "TD Avg.", "TD Acc.", "TD Def.", "Sub. Avg."]
    df2 = df2[cols]

    return df2

def total_time(form, rnd, tm):
    nothing = {"No Time Limit", "1 Rnd (20)", "1 Rnd (30)", "1 Rnd (15)", "1 Rnd (18)", "1 Rnd (10)", "1 Rnd (12)", 
               "Unlimited Rnd (10)", "Unlimited Rnd  (15)", "Unlimited Rnd (20)"}
    thirty_OT = {"1 Rnd + OT (30-5)", "1 Rnd + OT (30-3)"}
    fifteen_OT = {"1 Rnd + OT (15-3)", "1 Rnd + OT (15-10)"}
    tens = {"3 Rnd (10-10-10)", "4 Rnd (10-10-10-10)", "2 Rnd (10-10)", "3 Rnd (10-10-5)", "2 Rnd (10-5)"}
    fives = {"2 Rnd (5-5)", "3 Rnd (5-5-5)", "5 Rnd (5-5-5-5-5)", "3 Rnd + OT (5-5-5-5)"}
    fours = {"3 Rnd (4-4-4)", "5 Rnd (4-4-4-4-4)"}
    threes = {"5 Rnd (3-3-3-3-3)", "3 Rnd (3-3-3)", "2 Rnd (3-3)"}
    
    
    if form in nothing:
        return tm
    elif form == "1 Rnd + OT (31-5)":
        return tm + 31*(rnd - 1)
    elif form in thirty_OT:
        return tm + 30*(rnd - 1)
    elif form == "1 Rnd + OT (27-3)":
        return tm + 27*(rnd - 1)
    elif form in fifteen_OT:
        return tm + 15*(rnd - 1)
    elif form == "1 Rnd + OT (12-3)":
        return tm + 12*(rnd - 1)
    elif form in tens:
        return tm + 10*(rnd - 1)
    elif form == "3 Rnd (8-8-8)":
        return tm + 8*(rnd - 1)
    elif form in fives:
        return tm + 5*(rnd - 1)
    elif form in fours:
        return tm + 4*(rnd - 1)
    elif form in threes:
        return tm + 3*(rnd - 1)
    elif form == "3 Rnd (2-2-2)":
        return tm + 2*(rnd - 1)
    elif form == "1 Rnd + 2OT (24-3-3)":
        if rnd == 1:
            return tm
        else:
            return 24 + tm + 3*(rnd - 2)
    elif form == "1 Rnd + 2OT (15-3-3)":
        if rnd == 1:
            return tm
        else:
            return 15 + tm + 3*(rnd - 2)
    elif form == "3 Rnd (10-5-5)":
        if rnd == 1:
            return tm
        else:
            return 10 + 5*(rnd - 2)

def extract_landed_attempted(x):
    if pd.isnull(x):
        return (np.nan, np.nan)
    else:
        splitted = x.split("of")
        return (int(splitted[0]), int(splitted[1]))
    
def string_percent(x):
    if not pd.isnull(x):
        if x == "---":
            return np.nan
        else:
            return int(x.replace("%", "")) / 100
        
def ctrl_time(x):
    if not pd.isnull(x):
        if x == "--":
            return np.nan
        else:
            temp = x.split(":")
            return int(temp[0]) + (int(temp[1]) / 60.0)

def clean_bout_stats(bout_stats):
    concat_dict = {}
    df = bout_stats.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df["Location"] = df["Location"].apply(lambda x: np.nan if x == "" else x)
    df["Round"] = df["Round"].astype(int)
    df["Time"] = df["Time"].str.split(":").apply(lambda x: int(x[0]) + (int(x[1]) / 60.0))
    df["Total Time"] = df.apply(lambda x: total_time(x["Format"], x["Round"], x["Time"]), axis=1)

    # Overalls
    df["R_KD"] = df["R_KD"].astype(float)
    df["B_KD"] = df["B_KD"].astype(float)
    concat_dict["R_Total Str. Landed"], concat_dict["R_Total Str. Attempted"] = zip(*df["R_Total Str."].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Total Str. Landed"], concat_dict["B_Total Str. Attempted"] = zip(*df["B_Total Str."].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_TD Landed"], concat_dict["R_TD Attempted"] = zip(*df["R_TD"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_TD Landed"], concat_dict["B_TD Attempted"] = zip(*df["B_TD"].apply(lambda x: extract_landed_attempted(x)))
    df["R_TD %"] = df["R_TD %"].apply(lambda x: string_percent(x))
    df["B_TD %"] = df["B_TD %"].apply(lambda x: string_percent(x))
    df["R_Sub. Att"] = df["R_Sub. Att"].astype(float)
    df["B_Sub. Att"] = df["B_Sub. Att"].astype(float)
    df["R_Rev."] = df["R_Rev."].astype(float)
    df["B_Rev."] = df["B_Rev."].astype(float)
    df["R_Ctrl"] = df["R_Ctrl"].apply(lambda x: ctrl_time(x))
    df["B_Ctrl"] = df["B_Ctrl"].apply(lambda x: ctrl_time(x))

    # Overall stats by round
    df["R_KD_R1"] = df["R_KD_R1"].astype(float)
    df["B_KD_R1"] = df["B_KD_R1"].astype(float)
    concat_dict["R_Total Str. Landed_R1"], concat_dict["R_Total Str. Attempted_R1"] = zip(*df["R_Total Str._R1"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Total Str. Landed_R1"], concat_dict["B_Total Str. Attempted_R1"] = zip(*df["B_Total Str._R1"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_TD Landed_R1"], concat_dict["R_TD Attempted_R1"] = zip(*df["R_TD_R1"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_TD Landed_R1"], concat_dict["B_TD Attempted_R1"] = zip(*df["B_TD_R1"].apply(lambda x: extract_landed_attempted(x)))
    df["R_TD %_R1"] = df["R_TD %_R1"].apply(lambda x: string_percent(x))
    df["B_TD %_R1"] = df["B_TD %_R1"].apply(lambda x: string_percent(x))
    df["R_Sub. Att_R1"] = df["R_Sub. Att_R1"].astype(float)
    df["B_Sub. Att_R1"] = df["B_Sub. Att_R1"].astype(float)
    df["R_Rev._R1"] = df["R_Rev._R1"].astype(float)
    df["B_Rev._R1"] = df["B_Rev._R1"].astype(float)
    df["R_Ctrl_R1"] = df["R_Ctrl_R1"].apply(lambda x: ctrl_time(x))
    df["B_Ctrl_R1"] = df["B_Ctrl_R1"].apply(lambda x: ctrl_time(x))

    df["R_KD_R2"] = df["R_KD_R2"].astype(float)
    df["B_KD_R2"] = df["B_KD_R2"].astype(float)
    concat_dict["R_Total Str. Landed_R2"], concat_dict["R_Total Str. Attempted_R2"] = zip(*df["R_Total Str._R2"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Total Str. Landed_R2"], concat_dict["B_Total Str. Attempted_R2"] = zip(*df["B_Total Str._R2"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_TD Landed_R2"], concat_dict["R_TD Attempted_R2"] = zip(*df["R_TD_R2"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_TD Landed_R2"], concat_dict["B_TD Attempted_R2"] = zip(*df["B_TD_R2"].apply(lambda x: extract_landed_attempted(x)))
    df["R_TD %_R2"] = df["R_TD %_R2"].apply(lambda x: string_percent(x))
    df["B_TD %_R2"] = df["B_TD %_R2"].apply(lambda x: string_percent(x))
    df["R_Sub. Att_R2"] = df["R_Sub. Att_R2"].astype(float)
    df["B_Sub. Att_R2"] = df["B_Sub. Att_R2"].astype(float)
    df["R_Rev._R2"] = df["R_Rev._R2"].astype(float)
    df["B_Rev._R2"] = df["B_Rev._R2"].astype(float)
    df["R_Ctrl_R2"] = df["R_Ctrl_R2"].apply(lambda x: ctrl_time(x))
    df["B_Ctrl_R2"] = df["B_Ctrl_R2"].apply(lambda x: ctrl_time(x))

    df["R_KD_R3"] = df["R_KD_R3"].astype(float)
    df["B_KD_R3"] = df["B_KD_R3"].astype(float)
    concat_dict["R_Total Str. Landed_R3"], concat_dict["R_Total Str. Attempted_R3"] = zip(*df["R_Total Str._R3"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Total Str. Landed_R3"], concat_dict["B_Total Str. Attempted_R3"] = zip(*df["B_Total Str._R3"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_TD Landed_R3"], concat_dict["R_TD Attempted_R3"] = zip(*df["R_TD_R3"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_TD Landed_R3"], concat_dict["B_TD Attempted_R3"] = zip(*df["B_TD_R3"].apply(lambda x: extract_landed_attempted(x)))
    df["R_TD %_R3"] = df["R_TD %_R3"].apply(lambda x: string_percent(x))
    df["B_TD %_R3"] = df["B_TD %_R3"].apply(lambda x: string_percent(x))
    df["R_Sub. Att_R3"] = df["R_Sub. Att_R3"].astype(float)
    df["B_Sub. Att_R3"] = df["B_Sub. Att_R3"].astype(float)
    df["R_Rev._R3"] = df["R_Rev._R3"].astype(float)
    df["B_Rev._R3"] = df["B_Rev._R3"].astype(float)
    df["R_Ctrl_R3"] = df["R_Ctrl_R3"].apply(lambda x: ctrl_time(x))
    df["B_Ctrl_R3"] = df["B_Ctrl_R3"].apply(lambda x: ctrl_time(x))

    df["R_KD_R4"] = df["R_KD_R4"].astype(float)
    df["B_KD_R4"] = df["B_KD_R4"].astype(float)
    concat_dict["R_Total Str. Landed_R4"], concat_dict["R_Total Str. Attempted_R4"] = zip(*df["R_Total Str._R4"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Total Str. Landed_R4"], concat_dict["B_Total Str. Attempted_R4"] = zip(*df["B_Total Str._R4"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_TD Landed_R4"], concat_dict["R_TD Attempted_R4"] = zip(*df["R_TD_R4"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_TD Landed_R4"], concat_dict["B_TD Attempted_R4"] = zip(*df["B_TD_R4"].apply(lambda x: extract_landed_attempted(x)))
    df["R_TD %_R4"] = df["R_TD %_R4"].apply(lambda x: string_percent(x))
    df["B_TD %_R4"] = df["B_TD %_R4"].apply(lambda x: string_percent(x))
    df["R_Sub. Att_R4"] = df["R_Sub. Att_R4"].astype(float)
    df["B_Sub. Att_R4"] = df["B_Sub. Att_R4"].astype(float)
    df["R_Rev._R4"] = df["R_Rev._R4"].astype(float)
    df["B_Rev._R4"] = df["B_Rev._R4"].astype(float)
    df["R_Ctrl_R4"] = df["R_Ctrl_R4"].apply(lambda x: ctrl_time(x))
    df["B_Ctrl_R4"] = df["B_Ctrl_R4"].apply(lambda x: ctrl_time(x))

    df["R_KD_R5"] = df["R_KD_R5"].astype(float)
    df["B_KD_R5"] = df["B_KD_R5"].astype(float)
    concat_dict["R_Total Str. Landed_R5"], concat_dict["R_Total Str. Attempted_R5"] = zip(*df["R_Total Str._R5"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Total Str. Landed_R5"], concat_dict["B_Total Str. Attempted_R5"] = zip(*df["B_Total Str._R5"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_TD Landed_R5"], concat_dict["R_TD Attempted_R5"] = zip(*df["R_TD_R5"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_TD Landed_R5"], concat_dict["B_TD Attempted_R5"] = zip(*df["B_TD_R5"].apply(lambda x: extract_landed_attempted(x)))
    df["R_TD %_R5"] = df["R_TD %_R5"].apply(lambda x: string_percent(x))
    df["B_TD %_R5"] = df["B_TD %_R5"].apply(lambda x: string_percent(x))
    df["R_Sub. Att_R5"] = df["R_Sub. Att_R5"].astype(float)
    df["B_Sub. Att_R5"] = df["B_Sub. Att_R5"].astype(float)
    df["R_Rev._R5"] = df["R_Rev._R5"].astype(float)
    df["B_Rev._R5"] = df["B_Rev._R5"].astype(float)
    df["R_Ctrl_R5"] = df["R_Ctrl_R5"].apply(lambda x: ctrl_time(x))
    df["B_Ctrl_R5"] = df["B_Ctrl_R5"].apply(lambda x: ctrl_time(x))

    df["R_KD_R6"] = df["R_KD_R6"].astype(float)
    df["B_KD_R6"] = df["B_KD_R6"].astype(float)
    concat_dict["R_Total Str. Landed_R6"], concat_dict["R_Total Str. Attempted_R6"] = zip(*df["R_Total Str._R6"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Total Str. Landed_R6"], concat_dict["B_Total Str. Attempted_R6"] = zip(*df["B_Total Str._R6"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_TD Landed_R6"], concat_dict["R_TD Attempted_R6"] = zip(*df["R_TD_R6"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_TD Landed_R6"], concat_dict["B_TD Attempted_R6"] = zip(*df["B_TD_R6"].apply(lambda x: extract_landed_attempted(x)))
    df["R_TD %_R6"] = df["R_TD %_R6"].apply(lambda x: string_percent(x))
    df["B_TD %_R6"] = df["B_TD %_R6"].apply(lambda x: string_percent(x))
    df["R_Sub. Att_R6"] = df["R_Sub. Att_R6"].astype(float)
    df["B_Sub. Att_R6"] = df["B_Sub. Att_R6"].astype(float)
    df["R_Rev._R6"] = df["R_Rev._R6"].astype(float)
    df["B_Rev._R6"] = df["B_Rev._R6"].astype(float)
    df["R_Ctrl_R6"] = df["R_Ctrl_R6"].apply(lambda x: ctrl_time(x))
    df["B_Ctrl_R6"] = df["B_Ctrl_R6"].apply(lambda x: ctrl_time(x))

    # Significant Strikes
    concat_dict["R_Sig. Str. Landed"], concat_dict["R_Sig. Str. Attempted"] = zip(*df["R_Sig. Str."].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Sig. Str. Landed"], concat_dict["B_Sig. Str. Attempted"] = zip(*df["B_Sig. Str."].apply(lambda x: extract_landed_attempted(x)))
    df["R_Sig. Str. %"] = df["R_Sig. Str. %"].apply(lambda x: string_percent(x))
    df["B_Sig. Str. %"] = df["B_Sig. Str. %"].apply(lambda x: string_percent(x))
    concat_dict["R_Head Landed"], concat_dict["R_Head Attempted"] = zip(*df["R_Head"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Head Landed"], concat_dict["B_Head Attempted"] = zip(*df["B_Head"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Body Landed"], concat_dict["R_Body Attempted"] = zip(*df["R_Body"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Body Landed"], concat_dict["B_Body Attempted"] = zip(*df["B_Body"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Leg Landed"], concat_dict["R_Leg Attempted"] = zip(*df["R_Leg"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Leg Landed"], concat_dict["B_Leg Attempted"] = zip(*df["B_Leg"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Distance Landed"], concat_dict["R_Distance Attempted"] = zip(*df["R_Distance"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Distance Landed"], concat_dict["B_Distance Attempted"] = zip(*df["B_Distance"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Clinch Landed"], concat_dict["R_Clinch Attempted"] = zip(*df["R_Clinch"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Clinch Landed"], concat_dict["B_Clinch Attempted"] = zip(*df["B_Clinch"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Ground Landed"], concat_dict["R_Ground Attempted"] = zip(*df["R_Ground"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Ground Landed"], concat_dict["B_Ground Attempted"] = zip(*df["B_Ground"].apply(lambda x: extract_landed_attempted(x)))

    # Significant Strikes by round
    concat_dict["R_Sig. Str. Landed_R1"], concat_dict["R_Sig. Str. Attempted_R1"] = zip(*df["R_Sig. Str._R1"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Sig. Str. Landed_R1"], concat_dict["B_Sig. Str. Attempted_R1"] = zip(*df["B_Sig. Str._R1"].apply(lambda x: extract_landed_attempted(x)))
    df["R_Sig. Str. %_R1"] = df["R_Sig. Str. %_R1"].apply(lambda x: string_percent(x))
    df["B_Sig. Str. %_R1"] = df["B_Sig. Str. %_R1"].apply(lambda x: string_percent(x))
    concat_dict["R_Head Landed_R1"], concat_dict["R_Head Attempted_R1"] = zip(*df["R_Head_R1"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Head Landed_R1"], concat_dict["B_Head Attempted_R1"] = zip(*df["B_Head_R1"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Body Landed_R1"], concat_dict["R_Body Attempted_R1"] = zip(*df["R_Body_R1"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Body Landed_R1"], concat_dict["B_Body Attempted_R1"] = zip(*df["B_Body_R1"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Leg Landed_R1"], concat_dict["R_Leg Attempted_R1"] = zip(*df["R_Leg_R1"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Leg Landed_R1"], concat_dict["B_Leg Attempted_R1"] = zip(*df["B_Leg_R1"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Distance Landed_R1"], concat_dict["R_Distance Attempted_R1"] = zip(*df["R_Distance_R1"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Distance Landed_R1"], concat_dict["B_Distance Attempted_R1"] = zip(*df["B_Distance_R1"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Clinch Landed_R1"], concat_dict["R_Clinch Attempted_R1"] = zip(*df["R_Clinch_R1"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Clinch Landed_R1"], concat_dict["B_Clinch Attempted_R1"] = zip(*df["B_Clinch_R1"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Ground Landed_R1"], concat_dict["R_Ground Attempted_R1"] = zip(*df["R_Ground_R1"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Ground Landed_R1"], concat_dict["B_Ground Attempted_R1"] = zip(*df["B_Ground_R1"].apply(lambda x: extract_landed_attempted(x)))

    concat_dict["R_Sig. Str. Landed_R2"], concat_dict["R_Sig. Str. Attempted_R2"] = zip(*df["R_Sig. Str._R2"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Sig. Str. Landed_R2"], concat_dict["B_Sig. Str. Attempted_R2"] = zip(*df["B_Sig. Str._R2"].apply(lambda x: extract_landed_attempted(x)))
    df["R_Sig. Str. %_R2"] = df["R_Sig. Str. %_R2"].apply(lambda x: string_percent(x))
    df["B_Sig. Str. %_R2"] = df["B_Sig. Str. %_R2"].apply(lambda x: string_percent(x))
    concat_dict["R_Head Landed_R2"], concat_dict["R_Head Attempted_R2"] = zip(*df["R_Head_R2"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Head Landed_R2"], concat_dict["B_Head Attempted_R2"] = zip(*df["B_Head_R2"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Body Landed_R2"], concat_dict["R_Body Attempted_R2"] = zip(*df["R_Body_R2"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Body Landed_R2"], concat_dict["B_Body Attempted_R2"] = zip(*df["B_Body_R2"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Leg Landed_R2"], concat_dict["R_Leg Attempted_R2"] = zip(*df["R_Leg_R2"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Leg Landed_R2"], concat_dict["B_Leg Attempted_R2"] = zip(*df["B_Leg_R2"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Distance Landed_R2"], concat_dict["R_Distance Attempted_R2"] = zip(*df["R_Distance_R2"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Distance Landed_R2"], concat_dict["B_Distance Attempted_R2"] = zip(*df["B_Distance_R2"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Clinch Landed_R2"], concat_dict["R_Clinch Attempted_R2"] = zip(*df["R_Clinch_R2"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Clinch Landed_R2"], concat_dict["B_Clinch Attempted_R2"] = zip(*df["B_Clinch_R2"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Ground Landed_R2"], concat_dict["R_Ground Attempted_R2"] = zip(*df["R_Ground_R2"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Ground Landed_R2"], concat_dict["B_Ground Attempted_R2"] = zip(*df["B_Ground_R2"].apply(lambda x: extract_landed_attempted(x)))

    concat_dict["R_Sig. Str. Landed_R3"], concat_dict["R_Sig. Str. Attempted_R3"] = zip(*df["R_Sig. Str._R3"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Sig. Str. Landed_R3"], concat_dict["B_Sig. Str. Attempted_R3"] = zip(*df["B_Sig. Str._R3"].apply(lambda x: extract_landed_attempted(x)))
    df["R_Sig. Str. %_R3"] = df["R_Sig. Str. %_R3"].apply(lambda x: string_percent(x))
    df["B_Sig. Str. %_R3"] = df["B_Sig. Str. %_R3"].apply(lambda x: string_percent(x))
    concat_dict["R_Head Landed_R3"], concat_dict["R_Head Attempted_R3"] = zip(*df["R_Head_R3"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Head Landed_R3"], concat_dict["B_Head Attempted_R3"] = zip(*df["B_Head_R3"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Body Landed_R3"], concat_dict["R_Body Attempted_R3"] = zip(*df["R_Body_R3"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Body Landed_R3"], concat_dict["B_Body Attempted_R3"] = zip(*df["B_Body_R3"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Leg Landed_R3"], concat_dict["R_Leg Attempted_R3"] = zip(*df["R_Leg_R3"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Leg Landed_R3"], concat_dict["B_Leg Attempted_R3"] = zip(*df["B_Leg_R3"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Distance Landed_R3"], concat_dict["R_Distance Attempted_R3"] = zip(*df["R_Distance_R3"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Distance Landed_R3"], concat_dict["B_Distance Attempted_R3"] = zip(*df["B_Distance_R3"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Clinch Landed_R3"], concat_dict["R_Clinch Attempted_R3"] = zip(*df["R_Clinch_R3"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Clinch Landed_R3"], concat_dict["B_Clinch Attempted_R3"] = zip(*df["B_Clinch_R3"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Ground Landed_R3"], concat_dict["R_Ground Attempted_R3"] = zip(*df["R_Ground_R3"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Ground Landed_R3"], concat_dict["B_Ground Attempted_R3"] = zip(*df["B_Ground_R3"].apply(lambda x: extract_landed_attempted(x)))

    concat_dict["R_Sig. Str. Landed_R4"], concat_dict["R_Sig. Str. Attempted_R4"] = zip(*df["R_Sig. Str._R4"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Sig. Str. Landed_R4"], concat_dict["B_Sig. Str. Attempted_R4"] = zip(*df["B_Sig. Str._R4"].apply(lambda x: extract_landed_attempted(x)))
    df["R_Sig. Str. %_R4"] = df["R_Sig. Str. %_R4"].apply(lambda x: string_percent(x))
    df["B_Sig. Str. %_R4"] = df["B_Sig. Str. %_R4"].apply(lambda x: string_percent(x))
    concat_dict["R_Head Landed_R4"], concat_dict["R_Head Attempted_R4"] = zip(*df["R_Head_R4"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Head Landed_R4"], concat_dict["B_Head Attempted_R4"] = zip(*df["B_Head_R4"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Body Landed_R4"], concat_dict["R_Body Attempted_R4"] = zip(*df["R_Body_R4"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Body Landed_R4"], concat_dict["B_Body Attempted_R4"] = zip(*df["B_Body_R4"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Leg Landed_R4"], concat_dict["R_Leg Attempted_R4"] = zip(*df["R_Leg_R4"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Leg Landed_R4"], concat_dict["B_Leg Attempted_R4"] = zip(*df["B_Leg_R4"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Distance Landed_R4"], concat_dict["R_Distance Attempted_R4"] = zip(*df["R_Distance_R4"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Distance Landed_R4"], concat_dict["B_Distance Attempted_R4"] = zip(*df["B_Distance_R4"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Clinch Landed_R4"], concat_dict["R_Clinch Attempted_R4"] = zip(*df["R_Clinch_R4"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Clinch Landed_R4"], concat_dict["B_Clinch Attempted_R4"] = zip(*df["B_Clinch_R4"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Ground Landed_R4"], concat_dict["R_Ground Attempted_R4"] = zip(*df["R_Ground_R4"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Ground Landed_R4"], concat_dict["B_Ground Attempted_R4"] = zip(*df["B_Ground_R4"].apply(lambda x: extract_landed_attempted(x)))

    concat_dict["R_Sig. Str. Landed_R5"], concat_dict["R_Sig. Str. Attempted_R5"] = zip(*df["R_Sig. Str._R5"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Sig. Str. Landed_R5"], concat_dict["B_Sig. Str. Attempted_R5"] = zip(*df["B_Sig. Str._R5"].apply(lambda x: extract_landed_attempted(x)))
    df["R_Sig. Str. %_R5"] = df["R_Sig. Str. %_R5"].apply(lambda x: string_percent(x))
    df["B_Sig. Str. %_R5"] = df["B_Sig. Str. %_R5"].apply(lambda x: string_percent(x))
    concat_dict["R_Head Landed_R5"], concat_dict["R_Head Attempted_R5"] = zip(*df["R_Head_R5"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Head Landed_R5"], concat_dict["B_Head Attempted_R5"] = zip(*df["B_Head_R5"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Body Landed_R5"], concat_dict["R_Body Attempted_R5"] = zip(*df["R_Body_R5"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Body Landed_R5"], concat_dict["B_Body Attempted_R5"] = zip(*df["B_Body_R5"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Leg Landed_R5"], concat_dict["R_Leg Attempted_R5"] = zip(*df["R_Leg_R5"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Leg Landed_R5"], concat_dict["B_Leg Attempted_R5"] = zip(*df["B_Leg_R5"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Distance Landed_R5"], concat_dict["R_Distance Attempted_R5"] = zip(*df["R_Distance_R5"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Distance Landed_R5"], concat_dict["B_Distance Attempted_R5"] = zip(*df["B_Distance_R5"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Clinch Landed_R5"], concat_dict["R_Clinch Attempted_R5"] = zip(*df["R_Clinch_R5"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Clinch Landed_R5"], concat_dict["B_Clinch Attempted_R5"] = zip(*df["B_Clinch_R5"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Ground Landed_R5"], concat_dict["R_Ground Attempted_R5"] = zip(*df["R_Ground_R5"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Ground Landed_R5"], concat_dict["B_Ground Attempted_R5"] = zip(*df["B_Ground_R5"].apply(lambda x: extract_landed_attempted(x)))

    concat_dict["R_Sig. Str. Landed_R6"], concat_dict["R_Sig. Str. Attempted_R6"] = zip(*df["R_Sig. Str._R6"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Sig. Str. Landed_R6"], concat_dict["B_Sig. Str. Attempted_R6"] = zip(*df["B_Sig. Str._R6"].apply(lambda x: extract_landed_attempted(x)))
    df["R_Sig. Str. %_R6"] = df["R_Sig. Str. %_R6"].apply(lambda x: string_percent(x))
    df["B_Sig. Str. %_R6"] = df["B_Sig. Str. %_R6"].apply(lambda x: string_percent(x))
    concat_dict["R_Head Landed_R6"], concat_dict["R_Head Attempted_R6"] = zip(*df["R_Head_R6"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Head Landed_R6"], concat_dict["B_Head Attempted_R6"] = zip(*df["B_Head_R6"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Body Landed_R6"], concat_dict["R_Body Attempted_R6"] = zip(*df["R_Body_R6"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Body Landed_R6"], concat_dict["B_Body Attempted_R6"] = zip(*df["B_Body_R6"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Leg Landed_R6"], concat_dict["R_Leg Attempted_R6"] = zip(*df["R_Leg_R6"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Leg Landed_R6"], concat_dict["B_Leg Attempted_R6"] = zip(*df["B_Leg_R6"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Distance Landed_R6"], concat_dict["R_Distance Attempted_R6"] = zip(*df["R_Distance_R6"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Distance Landed_R6"], concat_dict["B_Distance Attempted_R6"] = zip(*df["B_Distance_R6"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Clinch Landed_R6"], concat_dict["R_Clinch Attempted_R6"] = zip(*df["R_Clinch_R6"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Clinch Landed_R6"], concat_dict["B_Clinch Attempted_R6"] = zip(*df["B_Clinch_R6"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["R_Ground Landed_R6"], concat_dict["R_Ground Attempted_R6"] = zip(*df["R_Ground_R6"].apply(lambda x: extract_landed_attempted(x)))
    concat_dict["B_Ground Landed_R6"], concat_dict["B_Ground Attempted_R6"] = zip(*df["B_Ground_R6"].apply(lambda x: extract_landed_attempted(x)))

    temp = pd.DataFrame.from_dict(concat_dict)
    df2 = pd.concat([df, temp], axis=1)

    # Drop original columns
    drop_cols = ["R_Total Str.", "B_Total Str.", "R_TD", "B_TD", 
                 "R_Total Str._R1", "B_Total Str._R1", "R_TD_R1", "B_TD_R1", 
                 "R_Total Str._R2", "B_Total Str._R2", "R_TD_R2", "B_TD_R2", 
                 "R_Total Str._R3", "B_Total Str._R3", "R_TD_R3", "B_TD_R3",
                 "R_Total Str._R4", "B_Total Str._R4", "R_TD_R4", "B_TD_R4",
                 "R_Total Str._R5", "B_Total Str._R5", "R_TD_R5", "B_TD_R5",
                 "R_Total Str._R6", "B_Total Str._R6", "R_TD_R6", "B_TD_R6",
                 "R_Sig. Str.", "B_Sig. Str.", "R_Head", "B_Head", "R_Body", "B_Body", "R_Leg", "B_Leg", "R_Distance", "B_Distance", "R_Clinch", "B_Clinch", "R_Ground", "B_Ground",
                 "R_Sig. Str._R1", "B_Sig. Str._R1", "R_Head_R1", "B_Head_R1", "R_Body_R1", "B_Body_R1", "R_Leg_R1", "B_Leg_R1", "R_Distance_R1", "B_Distance_R1", "R_Clinch_R1", "B_Clinch_R1", "R_Ground_R1", "B_Ground_R1",
                 "R_Sig. Str._R2", "B_Sig. Str._R2", "R_Head_R2", "B_Head_R2", "R_Body_R2", "B_Body_R2", "R_Leg_R2", "B_Leg_R2", "R_Distance_R2", "B_Distance_R2", "R_Clinch_R2", "B_Clinch_R2", "R_Ground_R2", "B_Ground_R2",
                 "R_Sig. Str._R3", "B_Sig. Str._R3", "R_Head_R3", "B_Head_R3", "R_Body_R3", "B_Body_R3", "R_Leg_R3", "B_Leg_R3", "R_Distance_R3", "B_Distance_R3", "R_Clinch_R3", "B_Clinch_R3", "R_Ground_R3", "B_Ground_R3",
                 "R_Sig. Str._R4", "B_Sig. Str._R4", "R_Head_R4", "B_Head_R4", "R_Body_R4", "B_Body_R4", "R_Leg_R4", "B_Leg_R4", "R_Distance_R4", "B_Distance_R4", "R_Clinch_R4", "B_Clinch_R4", "R_Ground_R4", "B_Ground_R4",
                 "R_Sig. Str._R5", "B_Sig. Str._R5", "R_Head_R5", "B_Head_R5", "R_Body_R5", "B_Body_R5", "R_Leg_R5", "B_Leg_R5", "R_Distance_R5", "B_Distance_R5", "R_Clinch_R5", "B_Clinch_R5", "R_Ground_R5", "B_Ground_R5",
                 "R_Sig. Str._R6", "B_Sig. Str._R6", "R_Head_R6", "B_Head_R6", "R_Body_R6", "B_Body_R6", "R_Leg_R6", "B_Leg_R6", "R_Distance_R6", "B_Distance_R6", "R_Clinch_R6", "B_Clinch_R6", "R_Ground_R6", "B_Ground_R6"]
    df2 = df2.drop(columns=drop_cols)

    cols = ["URL", "Event", "Date", "Location", "R_Name", "B_Name", "R_Result", "B_Result", "Bout Type", "Method", "Round", "Time", "Format", "Total Time", 
            "R_KD", "B_KD", "R_Total Str. Landed", "R_Total Str. Attempted", "B_Total Str. Landed", "B_Total Str. Attempted", "R_TD Landed", "R_TD Attempted", "B_TD Landed", "B_TD Attempted", "R_TD %", "B_TD %", "R_Sub. Att", "B_Sub. Att", "R_Rev.", "B_Rev.", "R_Ctrl", "B_Ctrl", 
            "R_KD_R1", "B_KD_R1", "R_Total Str. Landed_R1", "R_Total Str. Attempted_R1", "B_Total Str. Landed_R1", "B_Total Str. Attempted_R1", "R_TD Landed_R1", "R_TD Attempted_R1", "B_TD Landed_R1", "B_TD Attempted_R1", "R_TD %_R1", "B_TD %_R1", "R_Sub. Att_R1", "B_Sub. Att_R1", "R_Rev._R1", "B_Rev._R1", "R_Ctrl_R1", "B_Ctrl_R1",
            "R_KD_R2", "B_KD_R2", "R_Total Str. Landed_R2", "R_Total Str. Attempted_R2", "B_Total Str. Landed_R2", "B_Total Str. Attempted_R2", "R_TD Landed_R2", "R_TD Attempted_R2", "B_TD Landed_R2", "B_TD Attempted_R2", "R_TD %_R2", "B_TD %_R2", "R_Sub. Att_R2", "B_Sub. Att_R2", "R_Rev._R2", "B_Rev._R2", "R_Ctrl_R2", "B_Ctrl_R2",
            "R_KD_R3", "B_KD_R3", "R_Total Str. Landed_R3", "R_Total Str. Attempted_R3", "B_Total Str. Landed_R3", "B_Total Str. Attempted_R3", "R_TD Landed_R3", "R_TD Attempted_R3", "B_TD Landed_R3", "B_TD Attempted_R3", "R_TD %_R3", "B_TD %_R3", "R_Sub. Att_R3", "B_Sub. Att_R3", "R_Rev._R3", "B_Rev._R3", "R_Ctrl_R3", "B_Ctrl_R3",
            "R_KD_R4", "B_KD_R4", "R_Total Str. Landed_R4", "R_Total Str. Attempted_R4", "B_Total Str. Landed_R4", "B_Total Str. Attempted_R4", "R_TD Landed_R4", "R_TD Attempted_R4", "B_TD Landed_R4", "B_TD Attempted_R4", "R_TD %_R4", "B_TD %_R4", "R_Sub. Att_R4", "B_Sub. Att_R4", "R_Rev._R4", "B_Rev._R4", "R_Ctrl_R4", "B_Ctrl_R4",
            "R_KD_R5", "B_KD_R5", "R_Total Str. Landed_R5", "R_Total Str. Attempted_R5", "B_Total Str. Landed_R5", "B_Total Str. Attempted_R5", "R_TD Landed_R5", "R_TD Attempted_R5", "B_TD Landed_R5", "B_TD Attempted_R5", "R_TD %_R5", "B_TD %_R5", "R_Sub. Att_R5", "B_Sub. Att_R5", "R_Rev._R5", "B_Rev._R5", "R_Ctrl_R5", "B_Ctrl_R5",
            "R_KD_R6", "B_KD_R6", "R_Total Str. Landed_R6", "R_Total Str. Attempted_R6", "B_Total Str. Landed_R6", "B_Total Str. Attempted_R6", "R_TD Landed_R6", "R_TD Attempted_R6", "B_TD Landed_R6", "B_TD Attempted_R6", "R_TD %_R6", "B_TD %_R6", "R_Sub. Att_R6", "B_Sub. Att_R6", "R_Rev._R6", "B_Rev._R6", "R_Ctrl_R6", "B_Ctrl_R6",
            "R_Sig. Str. Landed", "R_Sig. Str. Attempted", "B_Sig. Str. Landed", "B_Sig. Str. Attempted", "R_Sig. Str. %", "B_Sig. Str. %", "R_Head Landed", "R_Head Attempted", "B_Head Landed", "B_Head Attempted", "R_Body Landed", "R_Body Attempted", "B_Body Landed", "B_Body Attempted", "R_Leg Landed", "R_Leg Attempted", "B_Leg Landed", "B_Leg Attempted", "R_Distance Landed", "R_Distance Attempted", "B_Distance Landed", "B_Distance Attempted", "R_Clinch Landed", "R_Clinch Attempted", "B_Clinch Landed", "B_Clinch Attempted", "R_Ground Landed", "R_Ground Attempted", "B_Ground Landed", "B_Ground Attempted",
            "R_Sig. Str. Landed_R1", "R_Sig. Str. Attempted_R1", "B_Sig. Str. Landed_R1", "B_Sig. Str. Attempted_R1", "R_Sig. Str. %_R1", "B_Sig. Str. %_R1", "R_Head Landed_R1", "R_Head Attempted_R1", "B_Head Landed_R1", "B_Head Attempted_R1", "R_Body Landed_R1", "R_Body Attempted_R1", "B_Body Landed_R1", "B_Body Attempted_R1", "R_Leg Landed_R1", "R_Leg Attempted_R1", "B_Leg Landed_R1", "B_Leg Attempted_R1", "R_Distance Landed_R1", "R_Distance Attempted_R1", "B_Distance Landed_R1", "B_Distance Attempted_R1", "R_Clinch Landed_R1", "R_Clinch Attempted_R1", "B_Clinch Landed_R1", "B_Clinch Attempted_R1", "R_Ground Landed_R1", "R_Ground Attempted_R1", "B_Ground Landed_R1", "B_Ground Attempted_R1",
            "R_Sig. Str. Landed_R2", "R_Sig. Str. Attempted_R2", "B_Sig. Str. Landed_R2", "B_Sig. Str. Attempted_R2", "R_Sig. Str. %_R2", "B_Sig. Str. %_R2", "R_Head Landed_R2", "R_Head Attempted_R2", "B_Head Landed_R2", "B_Head Attempted_R2", "R_Body Landed_R2", "R_Body Attempted_R2", "B_Body Landed_R2", "B_Body Attempted_R2", "R_Leg Landed_R2", "R_Leg Attempted_R2", "B_Leg Landed_R2", "B_Leg Attempted_R2", "R_Distance Landed_R2", "R_Distance Attempted_R2", "B_Distance Landed_R2", "B_Distance Attempted_R2", "R_Clinch Landed_R2", "R_Clinch Attempted_R2", "B_Clinch Landed_R2", "B_Clinch Attempted_R2", "R_Ground Landed_R2", "R_Ground Attempted_R2", "B_Ground Landed_R2", "B_Ground Attempted_R2",
            "R_Sig. Str. Landed_R3", "R_Sig. Str. Attempted_R3", "B_Sig. Str. Landed_R3", "B_Sig. Str. Attempted_R3", "R_Sig. Str. %_R3", "B_Sig. Str. %_R3", "R_Head Landed_R3", "R_Head Attempted_R3", "B_Head Landed_R3", "B_Head Attempted_R3", "R_Body Landed_R3", "R_Body Attempted_R3", "B_Body Landed_R3", "B_Body Attempted_R3", "R_Leg Landed_R3", "R_Leg Attempted_R3", "B_Leg Landed_R3", "B_Leg Attempted_R3", "R_Distance Landed_R3", "R_Distance Attempted_R3", "B_Distance Landed_R3", "B_Distance Attempted_R3", "R_Clinch Landed_R3", "R_Clinch Attempted_R3", "B_Clinch Landed_R3", "B_Clinch Attempted_R3", "R_Ground Landed_R3", "R_Ground Attempted_R3", "B_Ground Landed_R3", "B_Ground Attempted_R3",
            "R_Sig. Str. Landed_R4", "R_Sig. Str. Attempted_R4", "B_Sig. Str. Landed_R4", "B_Sig. Str. Attempted_R4", "R_Sig. Str. %_R4", "B_Sig. Str. %_R4", "R_Head Landed_R4", "R_Head Attempted_R4", "B_Head Landed_R4", "B_Head Attempted_R4", "R_Body Landed_R4", "R_Body Attempted_R4", "B_Body Landed_R4", "B_Body Attempted_R4", "R_Leg Landed_R4", "R_Leg Attempted_R4", "B_Leg Landed_R4", "B_Leg Attempted_R4", "R_Distance Landed_R4", "R_Distance Attempted_R4", "B_Distance Landed_R4", "B_Distance Attempted_R4", "R_Clinch Landed_R4", "R_Clinch Attempted_R4", "B_Clinch Landed_R4", "B_Clinch Attempted_R4", "R_Ground Landed_R4", "R_Ground Attempted_R4", "B_Ground Landed_R4", "B_Ground Attempted_R4",
            "R_Sig. Str. Landed_R5", "R_Sig. Str. Attempted_R5", "B_Sig. Str. Landed_R5", "B_Sig. Str. Attempted_R5", "R_Sig. Str. %_R5", "B_Sig. Str. %_R5", "R_Head Landed_R5", "R_Head Attempted_R5", "B_Head Landed_R5", "B_Head Attempted_R5", "R_Body Landed_R5", "R_Body Attempted_R5", "B_Body Landed_R5", "B_Body Attempted_R5", "R_Leg Landed_R5", "R_Leg Attempted_R5", "B_Leg Landed_R5", "B_Leg Attempted_R5", "R_Distance Landed_R5", "R_Distance Attempted_R5", "B_Distance Landed_R5", "B_Distance Attempted_R5", "R_Clinch Landed_R5", "R_Clinch Attempted_R5", "B_Clinch Landed_R5", "B_Clinch Attempted_R5", "R_Ground Landed_R5", "R_Ground Attempted_R5", "B_Ground Landed_R5", "B_Ground Attempted_R5",
            "R_Sig. Str. Landed_R6", "R_Sig. Str. Attempted_R6", "B_Sig. Str. Landed_R6", "B_Sig. Str. Attempted_R6", "R_Sig. Str. %_R6", "B_Sig. Str. %_R6", "R_Head Landed_R6", "R_Head Attempted_R6", "B_Head Landed_R6", "B_Head Attempted_R6", "R_Body Landed_R6", "R_Body Attempted_R6", "B_Body Landed_R6", "B_Body Attempted_R6", "R_Leg Landed_R6", "R_Leg Attempted_R6", "B_Leg Landed_R6", "B_Leg Attempted_R6", "R_Distance Landed_R6", "R_Distance Attempted_R6", "B_Distance Landed_R6", "B_Distance Attempted_R6", "R_Clinch Landed_R6", "R_Clinch Attempted_R6", "B_Clinch Landed_R6", "B_Clinch Attempted_R6", "R_Ground Landed_R6", "R_Ground Attempted_R6", "B_Ground Landed_R6", "B_Ground Attempted_R6"]
    df2 = df2[cols]

    return df2