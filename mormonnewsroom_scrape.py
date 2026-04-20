import re
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

WAYBACK_BASE = "https://web.archive.org"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

# Snapshots from mormonnewsroom.org (old domain, used before 2019 rebrand).
# Scrape date → data represents prior year (e.g. 2018-06-13 = 2017 stats).
SNAPSHOTS = [
    "https://web.archive.org/web/20180613151711/https://www.mormonnewsroom.org/facts-and-statistics",  # 2017 stats
    "https://web.archive.org/web/20170622025619/http://www.mormonnewsroom.org/facts-and-statistics",   # 2016 stats
    "https://web.archive.org/web/20160617172526/http://www.mormonnewsroom.org/facts-and-statistics",   # 2015 stats
    "https://web.archive.org/web/20150813152617/http://www.mormonnewsroom.org/facts-and-statistics",   # 2014 stats
    "https://web.archive.org/web/20140821145907/http://www.mormonnewsroom.org/facts-and-statistics/",  # 2013 stats
    "https://web.archive.org/web/20130725150921/http://www.mormonnewsroom.org/facts-and-statistics/",  # 2012 stats — no real state data
    "https://web.archive.org/web/20120813085138/http://www.mormonnewsroom.org/facts-and-statistics",   # 2011 stats — no real state data
]

NO_STATE_DATA = set()  # all years have real state data via h2#state-header

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
            print(f"    [{attempt+1}/{max_retries}] {e.__class__.__name__} on {url.split('/')[-1]}. Waiting {wait}s...")
            time.sleep(wait)


def get_wayback_links(snapshot_url):
    res = fetch_with_retry(snapshot_url)
    soup = BeautifulSoup(res.content, "html.parser")

    links = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/facts-and-statistics/country/" in href:
            full = WAYBACK_BASE + href if href.startswith("/web/") else href
            if full not in seen:
                seen.add(full)
                links.append(full)
    return links


def get_state_links(snapshot_url):
    """Extract state links from the US country page for this snapshot.

    State pages live at /facts-and-statistics/country/united-states/state/<slug>
    on the old domain (not /facts-and-statistics/state/<slug>). The US country
    page embeds links to all 51 state/DC pages with the correct Wayback timestamp.
    """
    ts_match = re.search(r'/web/(\d+)/(https?://[^/]+)', snapshot_url)
    if not ts_match:
        return []
    ts, domain = ts_match.group(1), ts_match.group(2)
    us_url = f"{WAYBACK_BASE}/web/{ts}/{domain}/facts-and-statistics/country/united-states"

    print(f"  Fetching US country page for state links: {us_url}")
    res = fetch_with_retry(us_url)
    soup = BeautifulSoup(res.content, "html.parser")
    time.sleep(10)

    links = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/facts-and-statistics/country/united-states/state/" in href:
            full = WAYBACK_BASE + href if href.startswith("/web/") else href
            if full not in seen:
                seen.add(full)
                links.append(full)
    return links


def slug_to_name(url):
    """Extract a properly capitalised state name from a Wayback state URL."""
    slug = url.rstrip("/").split("/")[-1]
    return " ".join(w.capitalize() for w in slug.split("-"))


def get_data(link, name_hint=None):
    res = fetch_with_retry(link)
    soup = BeautifulSoup(res.content, "html.parser")

    # Extract name from page title: "Mexico - LDS Statistics and Church Facts | ..."
    name = re.sub(r' - .+', '', soup.title.text).strip() if soup.title else ""
    name = re.sub(r'^The Church of Jesus Christ of Latter-day Saints in ', '', name)
    name = re.sub(r'^The Church in the ', '', name)
    name = re.sub(r'^The Church in ', '', name)
    name = re.sub(r'^The Church of Jesus Christ of Latter-day Saints ', '', name)
    name = re.sub(r'^USA-', '', name)  # state pages: "USA-Utah" → "Utah"
    name = name.replace('\u02bb', '').replace('\u2018', '').replace('\u2019', '').strip()
    if name:
        name = name[0].upper() + name[1:]
    # Fall back to URL-derived name when title doesn't contain it
    if not name or 'Statistics' in name or 'LDS' in name:
        name = name_hint or ""
    print(name)

    metrics = ['TotalChurchMembership', 'Stakes', 'Congregations', 'Wards',
               'Branches', 'FamilySearchCenters', 'Temples', 'Missions', 'Districts']
    data_dict = {'Name': name, **{m: 0 for m in metrics}}

    # --- Structure 0: state pages (all years) ---
    # Same .stat-line.one-fifth / .stat-line.w-graph format as newsroom.churchofjesuschrist.org
    one_fifth = soup.select('.stat-line.one-fifth')
    w_graph = soup.select('.stat-line.w-graph')
    if one_fifth and w_graph:
        try:
            text1 = one_fifth[0].text.split()
            text2 = re.sub(r' ', '', w_graph[0].text).split()
            data_string = text1 + text2
            for metric in metrics:
                if metric in data_string:
                    idx = data_string.index(metric) - 1
                    val = data_string[idx].replace(',', '')
                    data_dict[metric] = int(val) if val.isdigit() else 0
        except Exception:
            pass
        return data_dict

    # --- Structure 1: 2017-2018 ---
    # div.stat-line > div.stat-block with concatenated text: "1,417,011Total Church Membership"
    first_stat_line = soup.find('div', class_='stat-line')
    if first_stat_line:
        for block in first_stat_line.find_all('div', class_='stat-block'):
            text = block.get_text(strip=True)
            match = re.match(r'^([\d,]+)(.+)$', text)
            if match:
                val = int(match.group(1).replace(',', ''))
                label = match.group(2).strip()
                if label in LABEL_MAP:
                    data_dict[LABEL_MAP[label]] = val
        return data_dict

    # --- Structure 2: 2013-2016 ---
    # div.stat-blocks.FAS-country > div.stat-block with h3.stat-num / p.stat-label pairs
    fas_block = soup.find('div', class_='FAS-country')
    if fas_block:
        nums = fas_block.find_all('h3', class_='stat-num')
        labels = fas_block.find_all('p', class_='stat-label')
        for h3, p in zip(nums, labels):
            val_text = re.sub(r'[,\s]', '', h3.get_text())
            label = p.get_text(strip=True)
            if val_text.isdigit() and label in LABEL_MAP:
                data_dict[LABEL_MAP[label]] = int(val_text)
        return data_dict

    # --- Structure 3a: 2012-2013 state pages ---
    # h2#state-header → facts_stats_table with state-specific data.
    # These pages also contain h2#country-header with US national totals below it,
    # so we must check state-header first.
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
                        data_dict[LABEL_MAP[label]] = int(val_text)
        return data_dict

    # --- Structure 3b: 2012 country pages ---
    # Table immediately following h2#country-header with alternating label/value cells
    country_header = soup.find('h2', id='country-header')
    if country_header:
        table = country_header.find_next('table', class_='facts_stats_table')
        if table:
            # Each row: td[label link] | td.stats_numbers[value] | td[arrow img]
            for row in table.find_all('tr'):
                label_td = row.find('td', class_=lambda c: not c or 'stats_numbers' not in (c or ''))
                val_td = row.find('td', class_='stats_numbers')
                if label_td and val_td:
                    label = label_td.get_text(strip=True)
                    val_text = val_td.get_text(strip=True).replace(',', '')
                    if val_text.isdigit() and label in LABEL_MAP:
                        data_dict[LABEL_MAP[label]] = int(val_text)

    return data_dict


def extract_date(snapshot_url):
    match = re.search(r'/web/(\d{8})', snapshot_url)
    return datetime.strptime(match.group(1), "%Y%m%d").strftime("%Y-%m-%d")


def main():
    for snapshot_url in SNAPSHOTS:
        date_str = extract_date(snapshot_url)
        print(f"\n=== Scraping snapshot {date_str} ===")

        country_links = get_wayback_links(snapshot_url)
        print(f"  {len(country_links)} country links found")

        # Scrape countries
        country_file = f"./data/country-{date_str}.csv"
        country_rows = pd.read_csv(country_file).to_dict('records') if pd.io.common.file_exists(country_file) else []
        remaining = country_links[len(country_rows):]
        if country_rows:
            print(f"  Resuming countries from {len(country_rows)}/{len(country_links)}")
        print("  Scraping countries...")
        for link in remaining:
            country_rows.append(get_data(link))
            print(f"    {len(country_rows)}/{len(country_links)} countries done")
            pd.DataFrame(country_rows).to_csv(country_file, index=False)
            time.sleep(10)

        # Scrape states
        if date_str in NO_STATE_DATA:
            print(f"  Skipping states for {date_str} — old site returned US totals instead of per-state figures")
            continue

        state_links = get_state_links(snapshot_url)
        print(f"  {len(state_links)} state links found on US country page")

        state_file = f"./data/state-{date_str}.csv"
        state_rows = pd.read_csv(state_file).to_dict('records') if pd.io.common.file_exists(state_file) else []
        remaining = state_links[len(state_rows):]
        if state_rows:
            print(f"  Resuming states from {len(state_rows)}/{len(state_links)}")
        print("  Scraping states...")
        for link in remaining:
            name_hint = slug_to_name(link)
            state_rows.append(get_data(link, name_hint=name_hint))
            print(f"    {len(state_rows)}/{len(state_links)} states done")
            pd.DataFrame(state_rows).to_csv(state_file, index=False)
            time.sleep(10)

        print(f"  Saved country-{date_str}.csv and state-{date_str}.csv")


if __name__ == "__main__":
    main()
