# Title: Scrape LDS Stats from news-uk.churchofjesuschrist.org
# This domain has more up-to-date data than newsroom.churchofjesuschrist.org.
# Country links come from the news-uk seed page (old HTML format).
# State links are discovered via the newsroom US page (__NEXT_DATA__) but
# fetched from news-uk, which has the same state pages.

from bs4 import BeautifulSoup
import requests
import pandas as pd
from utility import get_data, get_links
from datetime import date

UK_BASE = "https://news-uk.churchofjesuschrist.org"
NEWSROOM_BASE = "https://newsroom.churchofjesuschrist.org"

def main():

    # Country-Level Data: news-uk
    base_link_for_countries = f"{UK_BASE}/facts-and-statistics/country/antigua-and-barbuda"
    country_links = get_links(base_link_for_countries, base_str=UK_BASE)
    print(f"Found {len(country_links)} country links")
    dict_data = [get_data(link) for link in country_links]
    country_data = pd.DataFrame(dict_data)

    # State-Level Data: discover state paths from newsroom (has __NEXT_DATA__),
    # but prefix with UK_BASE so the actual fetch hits news-uk.
    base_link_for_states = f"{NEWSROOM_BASE}/facts-and-statistics/country/united-states"
    state_links = get_links(base_link_for_states, base_str=UK_BASE)
    state_links = [lnk for lnk in state_links if lnk not in country_links]

    hawaii_link = f"{UK_BASE}/facts-and-statistics/state/hawaii"
    if hawaii_link not in state_links:
        state_links.append(hawaii_link)

    print(f"Found {len(state_links)} state links")
    dict_data = [get_data(link) for link in state_links]
    state_data = pd.DataFrame(dict_data)

    current_date = date.today()
    country_data.to_csv(f"./data/country-{str(current_date)}.csv", index=False)
    state_data.to_csv(f"./data/state-{str(current_date)}.csv", index=False)
    print(f"Saved country-{current_date}.csv and state-{current_date}.csv")

if __name__ == '__main__':
    main()
