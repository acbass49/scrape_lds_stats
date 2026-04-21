"""
Targeted fix for state-2012-08-13.csv (2011 data):
1. Re-scrapes 8 states that have all-zero membership data
2. Fixes District of Columbia capitalization (Of → of)

Uses CDX API to find the closest Wayback snapshot to the original 20120813 date.
"""

import re
import csv
import time
import requests
from bs4 import BeautifulSoup

WAYBACK_BASE = "https://web.archive.org"
TARGET_TS = "20120813085138"
TARGET_DATE = "2012-08-13"
STATE_FILE = f"./data/state-{TARGET_DATE}.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

LABEL_MAP = {
    "Total Church Membership": "TotalChurchMembership",
    "Congregations":           "Congregations",
    "Temples":                 "Temples",
    "Missions":                "Missions",
    "Family History Centers":  "FamilySearchCenters",
    "Stakes":                  "Stakes",
    "Wards":                   "Wards",
    "Branches":                "Branches",
    "Districts":               "Districts",
}

MISSING_STATES = {
    "New Hampshire":   "new-hampshire",
    "New Jersey":      "new-jersey",
    "New Mexico":      "new-mexico",
    "North Carolina":  "north-carolina",
    "North Dakota":    "north-dakota",
    "South Carolina":  "south-carolina",
    "South Dakota":    "south-dakota",
    "West Virginia":   "west-virginia",
    "District of Columbia": "district-of-columbia",
}

METRICS = ['TotalChurchMembership', 'Stakes', 'Congregations', 'Wards',
           'Branches', 'FamilySearchCenters', 'Temples', 'Missions', 'Districts']

FIELDNAMES = ['Name'] + METRICS


def fetch_with_retry(url, max_retries=6):
    for attempt in range(max_retries):
        try:
            res = requests.get(url, headers=HEADERS, timeout=60)
            res.raise_for_status()
            return res
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait = 60 * (2 ** attempt)
            print(f"    retry {attempt+1}/{max_retries}: {e.__class__.__name__}. Waiting {wait}s...")
            time.sleep(wait)


def find_best_snapshot(slug):
    """Find the latest 2012 snapshot (before Apr 2013 stats release) for a state page.

    The Church publishes prior-year stats in April, so any snapshot before Apr 2013
    should still contain 2011 data. We prefer the latest available to maximise the
    chance of the page being populated.
    """
    path = f"http://www.mormonnewsroom.org/facts-and-statistics/country/united-states/state/{slug}"
    cdx_url = (
        f"http://web.archive.org/cdx/search/cdx"
        f"?url={path}&output=json&fl=timestamp,statuscode"
        f"&from=20120101&to=20130401&filter=statuscode:200"
    )
    try:
        res = requests.get(cdx_url, timeout=30)
        data = res.json()
        if len(data) > 1:
            # Return the LAST (latest) snapshot in the range
            return data[-1][0]
    except Exception as e:
        print(f"    CDX lookup failed: {e}")
    return None


def parse_state_page(soup, name):
    data = {'Name': name, **{m: 0 for m in METRICS}}

    # Structure 0: .stat-line.one-fifth / .stat-line.w-graph
    one_fifth = soup.select('.stat-line.one-fifth')
    w_graph = soup.select('.stat-line.w-graph')
    if one_fifth and w_graph:
        try:
            text1 = one_fifth[0].text.split()
            text2 = re.sub(r' ', '', w_graph[0].text).split()
            data_string = text1 + text2
            for metric in METRICS:
                if metric in data_string:
                    idx = data_string.index(metric) - 1
                    val = data_string[idx].replace(',', '')
                    data[metric] = int(val) if val.isdigit() else 0
        except Exception:
            pass
        return data

    # Structure 3a: h2#state-header → facts_stats_table
    state_header = soup.find('h2', id='state-header')
    if state_header:
        table = state_header.find_next('table', class_='facts_stats_table')
        if table:
            for row in table.find_all('tr'):
                label_td = row.find('td', class_=lambda c: not c or 'stats_numbers' not in (c or ''))
                val_td = row.find('td', class_='stats_numbers')
                if label_td and val_td:
                    label = label_td.get_text(strip=True)
                    val_text = val_td.get_text(strip=True).replace(',', '')
                    if val_text.isdigit() and label in LABEL_MAP:
                        data[LABEL_MAP[label]] = int(val_text)
        return data

    return data


def scrape_state(name, slug):
    ts = find_best_snapshot(slug)
    if not ts:
        print(f"  {name}: no CDX snapshot found, trying original timestamp")
        ts = TARGET_TS

    url = f"{WAYBACK_BASE}/web/{ts}/http://www.mormonnewsroom.org/facts-and-statistics/country/united-states/state/{slug}"
    print(f"  {name}: fetching {url}")

    res = fetch_with_retry(url)
    soup = BeautifulSoup(res.content, "html.parser")
    data = parse_state_page(soup, name)

    membership = data['TotalChurchMembership']
    print(f"    → membership={membership}, congregations={data['Congregations']}, temples={data['Temples']}")
    return data


def load_csv():
    rows = []
    with open(STATE_FILE, newline='') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(dict(row))
    return rows


def save_csv(rows):
    with open(STATE_FILE, 'w', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {STATE_FILE}")


def main():
    rows = load_csv()

    # Step 1: fix DC capitalization (Of → of)
    dc_fixed = False
    for row in rows:
        if row['Name'].strip() == 'District Of Columbia':
            row['Name'] = 'District of Columbia'
            dc_fixed = True
            print("Fixed DC capitalization: 'District Of Columbia' → 'District of Columbia'")
    if not dc_fixed:
        print("DC capitalization already correct or not found")

    # Build lookup by name
    row_by_name = {r['Name'].strip(): r for r in rows}

    # Step 2: re-scrape zero-membership states
    for name, slug in MISSING_STATES.items():
        existing = row_by_name.get(name)
        if existing and int(existing.get('TotalChurchMembership', 0)) != 0:
            print(f"  {name}: already has data (membership={existing['TotalChurchMembership']}), skipping")
            continue

        try:
            new_data = scrape_state(name, slug)
            if int(new_data['TotalChurchMembership']) > 0:
                if existing:
                    existing.update(new_data)
                else:
                    rows.append(new_data)
                    row_by_name[name] = rows[-1]
                save_csv(rows)
            else:
                print(f"    Still zero — Wayback may not have this page captured")
        except Exception as e:
            print(f"  {name}: FAILED — {e}")

        time.sleep(10)

    print("\nDone.")


if __name__ == "__main__":
    main()
