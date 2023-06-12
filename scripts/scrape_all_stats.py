import pandas as pd
import numpy as np
import requests
import random
import time
from string import ascii_lowercase
from tqdm import tqdm
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from useragents import AGENT_LIST
from cleaning import clean_fighter_stats, clean_bout_stats

def get_fighter_urls_for_letter(letter):
    url = f"http://ufcstats.com/statistics/fighters?char={letter}&page=all"
    header = {"User-Agent": random.choice(AGENT_LIST)}
    source_code = requests.get(url, headers=header, allow_redirects=False)
    plain_text = source_code.text.encode("ascii", "replace")
    soup = BeautifulSoup(plain_text, "lxml")
    table = soup.find("tbody")
    names = table.findAll("a", {"class": "b-link b-link_style_black"}, href=True)
    res = []

    for i, name in enumerate(names):
        if (i + 1) % 3 == 0:
            res.append(name["href"])
    
    return res

def get_fighter_urls():
    fighter_urls = []
    letters = list(ascii_lowercase)
    with ThreadPoolExecutor(max_workers=10) as executor:
        for result in tqdm(executor.map(get_fighter_urls_for_letter, letters), total=len(letters), desc="Scraping fighter urls"):
            fighter_urls.extend(result)
    
    return fighter_urls

def get_info_from_fighter(fighter_url):
    header = {"User-Agent": random.choice(AGENT_LIST)}
    source_code = requests.get(fighter_url, headers=header, allow_redirects=False)
    plain_text = source_code.text.encode("ascii", "replace")
    soup = BeautifulSoup(plain_text, "lxml")
    
    # Ignore upcoming fights
    rows = soup.findAll("tr", {"class": "b-fight-details__table-row b-fight-details__table-row__hover js-fight-details-click"})
    events = []
    for row in rows:
        entry = []
        for i, atag in enumerate(row.findAll("a", {"class": "b-link b-link_style_black"}, href=True)):
            if i == 2:
                entry.append(atag["href"])
        for i, ptag in enumerate(row.findAll("p", {"class": "b-fight-details__table-text"})):
            if i == 11 or i == 12:
                entry.append(ptag.text.strip())
        events.append(entry)

    # Get fighter info
    name = soup.findAll("span", {"class": "b-content__title-highlight"})
    record = soup.findAll("span", {"class": "b-content__title-record"})
    divs = soup.findAll("li", {"class": "b-list__box-list-item b-list__box-list-item_type_block"})
    info = []
    if record and name:
        info.append(
            name[0].text.replace("  ", "")
                .replace("\n", "")
        )
        info.append(
            record[0].text.replace("  ", "")
                .replace("\n", "")
                .replace("Record: ", "")
        )
    else:
        print(soup.prettify())
        raise Exception("Name or record not found")
    
    for i, div in enumerate(divs):
        if i == 9:
            continue
        info.append(
            div.text.replace("  ", "")
                .replace("\n", "")
                .replace("Height:", "")
                .replace("Weight:", "")
                .replace("Reach:", "")
                .replace("STANCE:", "")
                .replace("DOB:", "")
                .replace("SLpM:", "")
                .replace("Str. Acc.:", "")
                .replace("SApM:", "")
                .replace("Str. Def:", "")
                .replace("TD Avg.:", "")
                .replace("TD Acc.:", "")
                .replace("TD Def.:", "")
                .replace("Sub. Avg.:", "")
        )

    return events, info


def get_event_urls_and_fighter_stats(fighter_urls):
    events = []
    fighter_stats = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        for result1, result2 in tqdm(executor.map(get_info_from_fighter, fighter_urls), total=len(fighter_urls), 
                                     desc="Scraping event urls and fighter stats"):
            events += result1
            fighter_stats.append(result2)
    
    df1 = pd.DataFrame(events, columns=["url", "event", "date"]).drop_duplicates(keep="first")
    df1["date"] = pd.to_datetime(df1["date"])
    df1 = df1.sort_values(by=["date", "event"]).reset_index(drop=True)

    df2 = pd.DataFrame(fighter_stats, columns=["Name", "Record", "Height", "Weight", "Reach", "Stance", "DOB", "SLpM", "Str. Acc.", 
                                               "SApM", "Str. Def.", "TD Avg.", "TD Acc.", "TD Def.", "Sub. Avg."])

    return df1, df2

def get_bout_urls_from_event(event_url, event, date):
    header = {"User-Agent": random.choice(AGENT_LIST)}
    source_code = requests.get(event_url, headers=header, allow_redirects=False)
    plain_text = source_code.text.encode("ascii", "replace")
    soup = BeautifulSoup(plain_text, "lxml")
    rows = soup.findAll("tr", {"class": "b-fight-details__table-row b-fight-details__table-row__hover js-fight-details-click"})
    urls = []
    
    for row in rows:
        for i, atag in enumerate(row.findAll("a", {"class": "b-flag"}, href=True)):
            if i == 0:
                urls.append([atag["href"], date, event])

    return urls[::-1]

def get_bout_urls(event_urls):
    bout_urls = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        for result in tqdm(executor.map(get_bout_urls_from_event, event_urls["url"], event_urls["event"], event_urls["date"]), 
                           total=event_urls.shape[0], desc="Scraping bout urls"):
            bout_urls += result
    
    df = pd.DataFrame(bout_urls, columns=["url", "date", "event"])
    df["date"] = pd.to_datetime(df["date"])
    df = df.drop_duplicates(keep="first").reset_index(drop=True)
    return df

def get_bout_stats_from_bout(bout_url, event, date):
    header = {"User-Agent": random.choice(AGENT_LIST)}
    source_code = requests.get(bout_url, headers=header, allow_redirects=False)
    plain_text = source_code.text.encode("ascii", "replace")
    soup = BeautifulSoup(plain_text, "lxml")
    bout = [bout_url, event, date]

    # Names
    names = soup.findAll("h3", {"class": "b-fight-details__person-name"})
    for name in names:
        bout.append(name.text.strip())
        
    # Results
    results = soup.findAll("i", {"class": "b-fight-details__person-status"})
    for result in results:
        bout.append(result.text.strip())

    # Bout Type
    typ = soup.findAll("i", {"class": "b-fight-details__fight-title"})
    if not typ:
        print(bout_url)
        raise Exception("Cannot find bout type")
    bout.append(typ[0].text.strip())

    # Method
    method = soup.findAll("i", {"class": "b-fight-details__text-item_first"})
    bout.append(method[0].text.replace("Method:", "").strip())

    # Round, Time, Format
    ptags = soup.findAll("p", {"class": "b-fight-details__text"})
    details = ptags[0].findAll("i", {"class": "b-fight-details__text-item"})
    for i, d in enumerate(details):
        if i != 3:
            bout.append(d.text.replace("Round:", "")
                        .replace("Time:", "")
                        .replace("Time format:", "")
                        .strip())

    tables = soup.findAll("tbody", {"class": "b-fight-details__table-body"})
    if tables:
        if len(tables) != 4:
            print(bout_url)
            raise Exception("Cannot find all tables")
        
        # Totals
        totals = []
        ptags1 = tables[0].findAll("p", {"class": "b-fight-details__table-text"})
        for i, p1 in enumerate(ptags1):
            if i not in {0, 1, 4, 5, 6, 7}:
                totals.append(p1.text.strip())

        # Totals (Per round)
        totals_per = []
        rows1 = tables[1].findAll("tr", {"class": "b-fight-details__table-row"})
        for r1 in rows1:
            ptags2 = r1.findAll("p", {"class": "b-fight-details__table-text"})
            for i, p2 in enumerate(ptags2):
                if i not in {0, 1, 4, 5, 6, 7}:
                    totals_per.append(p2.text.strip())
        excess1 = (6 - len(rows1)) * 14
        totals_per.extend([np.nan for _ in range(excess1)])

        # Significant Strikes
        sig_str = []
        ptags3 = tables[2].findAll("p", {"class": "b-fight-details__table-text"})
        for i, p3 in enumerate(ptags3):
            if i >= 2:
                sig_str.append(p3.text.strip())

        # Significant Strikes (Per round)
        sig_str_per = []
        rows2 = tables[3].findAll("tr", {"class": "b-fight-details__table-row"})
        for r2 in rows2:
            ptags4 = r2.findAll("p", {"class": "b-fight-details__table-text"})
            for i, p4 in enumerate(ptags4):
                if i >= 2:
                    sig_str_per.append(p4.text.strip())
        excess2 = (6 - len(rows2)) * 16
        sig_str_per.extend([np.nan for _ in range(excess2)])
        
        bout.extend(totals + totals_per + sig_str + sig_str_per)
    else:
        # For fights without round by round stats
        bout.extend([np.nan for i in range(210)])

    if len(bout) != 222:
        print(bout_url)
        raise Exception("Incorrect number of stats")
    
    return bout

def get_bout_stats(bout_urls):
    bout_stats = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        for result in tqdm(executor.map(get_bout_stats_from_bout, bout_urls["url"], bout_urls["event"], bout_urls["date"]), 
                           total=bout_urls.shape[0], desc="Scraping bout stats"):
            bout_stats.append(result)
    
    columns = ["URL", "Event", "Date", "R_Name", "B_Name", "R_Result", "B_Result", "Bout Type", "Method", "Round", "Time", "Format", 
               "R_KD", "B_KD", "R_Total Str.", "B_Total Str.", "R_TD", "B_TD", "R_TD %", "B_TD %", "R_Sub. Att", "B_Sub. Att", "R_Rev.", "B_Rev.", "R_Ctrl", "B_Ctrl", 
               "R_KD_R1", "B_KD_R1", "R_Total Str._R1", "B_Total Str._R1", "R_TD_R1", "B_TD_R1", "R_TD %_R1", "B_TD %_R1", "R_Sub. Att_R1", "B_Sub. Att_R1", "R_Rev._R1", "B_Rev._R1", "R_Ctrl_R1", "B_Ctrl_R1", 
               "R_KD_R2", "B_KD_R2", "R_Total Str._R2", "B_Total Str._R2", "R_TD_R2", "B_TD_R2", "R_TD %_R2", "B_TD %_R2", "R_Sub. Att_R2", "B_Sub. Att_R2", "R_Rev._R2", "B_Rev._R2", "R_Ctrl_R2", "B_Ctrl_R2", 
               "R_KD_R3", "B_KD_R3", "R_Total Str._R3", "B_Total Str._R3", "R_TD_R3", "B_TD_R3", "R_TD %_R3", "B_TD %_R3", "R_Sub. Att_R3", "B_Sub. Att_R3", "R_Rev._R3", "B_Rev._R3", "R_Ctrl_R3", "B_Ctrl_R3", 
               "R_KD_R4", "B_KD_R4", "R_Total Str._R4", "B_Total Str._R4", "R_TD_R4", "B_TD_R4", "R_TD %_R4", "B_TD %_R4", "R_Sub. Att_R4", "B_Sub. Att_R4", "R_Rev._R4", "B_Rev._R4", "R_Ctrl_R4", "B_Ctrl_R4", 
               "R_KD_R5", "B_KD_R5", "R_Total Str._R5", "B_Total Str._R5", "R_TD_R5", "B_TD_R5", "R_TD %_R5", "B_TD %_R5", "R_Sub. Att_R5", "B_Sub. Att_R5", "R_Rev._R5", "B_Rev._R5", "R_Ctrl_R5", "B_Ctrl_R5", 
               "R_KD_R6", "B_KD_R6", "R_Total Str._R6", "B_Total Str._R6", "R_TD_R6", "B_TD_R6", "R_TD %_R6", "B_TD %_R6", "R_Sub. Att_R6", "B_Sub. Att_R6", "R_Rev._R6", "B_Rev._R6", "R_Ctrl_R6", "B_Ctrl_R6",
               "R_Sig. Str.", "B_Sig. Str.", "R_Sig. Str. %", "B_Sig. Str. %", "R_Head", "B_Head", "R_Body", "B_Body", "R_Leg", "B_Leg", "R_Distance", "B_Distance", "R_Clinch", "B_Clinch", "R_Ground", "B_Ground", 
               "R_Sig. Str._R1", "B_Sig. Str._R1", "R_Sig. Str. %_R1", "B_Sig. Str. %_R1", "R_Head_R1", "B_Head_R1", "R_Body_R1", "B_Body_R1", "R_Leg_R1", "B_Leg_R1", "R_Distance_R1", "B_Distance_R1", "R_Clinch_R1", "B_Clinch_R1", "R_Ground_R1", "B_Ground_R1", 
               "R_Sig. Str._R2", "B_Sig. Str._R2", "R_Sig. Str. %_R2", "B_Sig. Str. %_R2", "R_Head_R2", "B_Head_R2", "R_Body_R2", "B_Body_R2", "R_Leg_R2", "B_Leg_R2", "R_Distance_R2", "B_Distance_R2", "R_Clinch_R2", "B_Clinch_R2", "R_Ground_R2", "B_Ground_R2", 
               "R_Sig. Str._R3", "B_Sig. Str._R3", "R_Sig. Str. %_R3", "B_Sig. Str. %_R3", "R_Head_R3", "B_Head_R3", "R_Body_R3", "B_Body_R3", "R_Leg_R3", "B_Leg_R3", "R_Distance_R3", "B_Distance_R3", "R_Clinch_R3", "B_Clinch_R3", "R_Ground_R3", "B_Ground_R3", 
               "R_Sig. Str._R4", "B_Sig. Str._R4", "R_Sig. Str. %_R4", "B_Sig. Str. %_R4", "R_Head_R4", "B_Head_R4", "R_Body_R4", "B_Body_R4", "R_Leg_R4", "B_Leg_R4", "R_Distance_R4", "B_Distance_R4", "R_Clinch_R4", "B_Clinch_R4", "R_Ground_R4", "B_Ground_R4", 
               "R_Sig. Str._R5", "B_Sig. Str._R5", "R_Sig. Str. %_R5", "B_Sig. Str. %_R5", "R_Head_R5", "B_Head_R5", "R_Body_R5", "B_Body_R5", "R_Leg_R5", "B_Leg_R5", "R_Distance_R5", "B_Distance_R5", "R_Clinch_R5", "B_Clinch_R5", "R_Ground_R5", "B_Ground_R5", 
               "R_Sig. Str._R6", "B_Sig. Str._R6", "R_Sig. Str. %_R6", "B_Sig. Str. %_R6", "R_Head_R6", "B_Head_R6", "R_Body_R6", "B_Body_R6", "R_Leg_R6", "B_Leg_R6", "R_Distance_R6", "B_Distance_R6", "R_Clinch_R6", "B_Clinch_R6", "R_Ground_R6", "B_Ground_R6"]
    
    df = pd.DataFrame(bout_stats, columns=columns)
    return df

def main():
    start = time.time()

    # Scrape fighter urls
    fighter_urls = get_fighter_urls()
    print(f"Found {len(fighter_urls)} fighter urls, now scraping event urls and fighter stats...")
    time.sleep(10)
    
    # Scrape event urls + fighter stats
    event_urls, fighter_stats = get_event_urls_and_fighter_stats(fighter_urls)
    print(f"Found {event_urls.shape[0]} event urls and statistics for {len(fighter_urls)} fighters, now scraping bout urls...")
    time.sleep(10)

    # Scrape bout urls
    bout_urls = get_bout_urls(event_urls)
    print(f"Found {bout_urls.shape[0]} bout urls, now scraping bout stats...")
    time.sleep(10)

    # Scrape bout stats
    bout_stats = get_bout_stats(bout_urls)
    print(f"Found statistics for {bout_stats.shape[0]} bouts, now cleaning data...")

    # Clean data
    fighter_stats_clean = clean_fighter_stats(fighter_stats)
    bout_stats_clean = clean_bout_stats(bout_stats)
    print("Finished cleaning data, now saving to csv...")

    # Save data to csv
    fighter_stats_clean.to_csv("../data/fighter_stats.csv", index=False)
    bout_stats_clean.to_csv("../data/bout_stats.csv", index=False)

    end = time.time()
    print(f"Finished in {end - start} seconds")


if __name__ == "__main__":
    main()