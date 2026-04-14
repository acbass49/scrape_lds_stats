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

# One snapshot URL per year. Timestamp date is used for the output filename.
# Stats shown reflect the prior year (e.g. 2019-11-21 snapshot = 2018 annual stats).
SNAPSHOTS = [
    "https://web.archive.org/web/20191121205419/https://newsroom.churchofjesuschrist.org/facts-and-statistics",   # 2018 stats
    "https://web.archive.org/web/20201001032844/https://newsroom.churchofjesuschrist.org/facts-and-statistics",   # 2019 stats
    "https://web.archive.org/web/20220428213823/https://newsroom.churchofjesuschrist.org/facts-and-statistics",   # 2021 stats
    "https://web.archive.org/web/20230629231006/https://newsroom.churchofjesuschrist.org/facts-and-statistics",   # 2022 stats
]


def fetch_with_retry(url, max_retries=6):
    """Fetch a URL with exponential backoff on failure."""
    for attempt in range(max_retries):
        try:
            res = requests.get(url, headers=HEADERS, timeout=60)
            res.raise_for_status()
            return res
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait = 60 * (2 ** attempt)  # 60, 120, 240, 480, 960 seconds
            print(f"    [{attempt+1}/{max_retries}] {e.__class__.__name__} on {url.split('/')[-1]}. Waiting {wait}s...")
            time.sleep(wait)


def get_wayback_links(snapshot_url):
    """Get all country/state links from a Wayback Machine snapshot page."""
    res = fetch_with_retry(snapshot_url)
    soup = BeautifulSoup(res.content, "html.parser")

    links = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/facts-and-statistics/country/" in href or "/facts-and-statistics/state/" in href:
            full = WAYBACK_BASE + href if href.startswith("/web/") else href
            if full not in seen:
                seen.add(full)
                links.append(full)
    return links


def get_data(link):
    """Fetch and parse a country/state page, handling old-format CSS selectors."""
    import re as _re
    res = fetch_with_retry(link)
    soup = BeautifulSoup(res.content, "html.parser")

    name = _re.subn(r' - .+', "", soup.title.text)[0]
    name = _re.sub(r'^The Church of Jesus Christ of Latter-day Saints in ', '', name)
    name = _re.sub(r'^The Church in the ', '', name)
    name = _re.sub(r'^The Church in ', '', name)
    name = _re.sub(r'^The Church of Jesus Christ of Latter-day Saints ', '', name)
    name = name.strip()
    name = name.replace('\u02bb', '').replace('\u2018', '').replace('\u2019', '')
    name = name[0].upper() + name[1:] if name else name
    print(name)

    data_dict = {'Name': name}
    metrics = [
        'TotalChurchMembership', 'Stakes', 'Congregations', 'Wards',
        'Branches', 'FamilySearchCenters', 'Temples', 'Missions', 'Districts'
    ]

    try:
        text1 = soup.select(".stat-line.one-fifth")[0].text.split()
        text2 = _re.subn(pattern=" ", repl="", string=soup.select(".stat-line.w-graph")[0].text)[0].split()
        data_string = text1 + text2
        for metric in metrics:
            if metric in data_string:
                idx = data_string.index(metric) - 1
                val = _re.subn(",", "", data_string[idx])[0]
                data_dict[metric] = int(val) if val.isdigit() else 0
            else:
                data_dict[metric] = 0
    except (IndexError, Exception):
        for metric in metrics:
            data_dict[metric] = 0

    return data_dict


def extract_date(snapshot_url):
    """Extract YYYY-MM-DD from a Wayback Machine URL timestamp."""
    match = re.search(r'/web/(\d{8})', snapshot_url)
    return datetime.strptime(match.group(1), "%Y%m%d").strftime("%Y-%m-%d")


def main():
    for snapshot_url in SNAPSHOTS:
        date_str = extract_date(snapshot_url)
        timestamp = re.search(r'/web/(\d+)/', snapshot_url).group(1)
        print(f"\n=== Scraping snapshot {date_str} ===")

        # Country links from the index page
        country_links = get_wayback_links(snapshot_url)
        print(f"  {len(country_links)} country links found")

        # State links from the archived US page
        us_url = f"{WAYBACK_BASE}/web/{timestamp}/https://newsroom.churchofjesuschrist.org/facts-and-statistics/country/united-states"
        state_links = [l for l in get_wayback_links(us_url) if "/facts-and-statistics/state/" in l]
        print(f"  {len(state_links)} state links found")

        # Scrape countries (resume if file already exists)
        country_file = f"./data/country-{date_str}.csv"
        country_rows = pd.read_csv(country_file).to_dict('records') if pd.io.common.file_exists(country_file) else []
        remaining_countries = country_links[len(country_rows):]
        if country_rows:
            print(f"  Resuming countries from {len(country_rows)}/{len(country_links)}")
        print("  Scraping countries...")
        for i, link in enumerate(remaining_countries):
            country_rows.append(get_data(link))
            print(f"    {len(country_rows)}/{len(country_links)} countries done")
            pd.DataFrame(country_rows).to_csv(country_file, index=False)
            time.sleep(15)

        # Scrape states (resume if file already exists)
        state_file = f"./data/state-{date_str}.csv"
        state_rows = pd.read_csv(state_file).to_dict('records') if pd.io.common.file_exists(state_file) else []
        remaining_states = state_links[len(state_rows):]
        if state_rows:
            print(f"  Resuming states from {len(state_rows)}/{len(state_links)}")
        print("  Scraping states...")
        for i, link in enumerate(remaining_states):
            state_rows.append(get_data(link))
            print(f"    {len(state_rows)}/{len(state_links)} states done")
            pd.DataFrame(state_rows).to_csv(state_file, index=False)
            time.sleep(15)

        print(f"  Saved country-{date_str}.csv and state-{date_str}.csv")


if __name__ == "__main__":
    main()
