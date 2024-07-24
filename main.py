# Title: Main Script To Scrape LDS Stats
from bs4 import BeautifulSoup
import requests
import re
import pandas as pd
from utility import get_data, get_links, get_temple_data
from datetime import date
import json

def main():

    # Country-Level Data: LDS.ORG
    base_link_for_countries = "https://newsroom.churchofjesuschrist.org/facts-and-statistics"
    country_links = get_links(base_link_for_countries)
    dict_data = [get_data(link) for link in country_links]
    country_data = pd.DataFrame(dict_data)

    # State-Level Data: LDS.ORG
    base_link_for_states = "https://newsroom.churchofjesuschrist.org/facts-and-statistics/country/united-states"
    state_links = get_links(base_link_for_states)
    state_links = [lnk for lnk in state_links if lnk not in country_links]
    dict_data = [get_data(link) for link in state_links]
    state_data = pd.DataFrame(dict_data)

    # Temple Data: LDS.ORG
    base_link_temples = "https://www.churchofjesuschrist.org/temples/list?lang=eng"
    res = requests.get(base_link_temples)
    soup = BeautifulSoup(res.content, "html.parser")
    script_json = soup.find_all("script")[15].text.strip()
    data = json.loads(script_json)
    temple_data = pd.json_normalize(data, ['props','pageProps','templeList'])

    current_date = date.today()
    country_data.to_csv(f"./data/country-{str(current_date)}.csv", index = False)
    state_data.to_csv(f"./data/state-{str(current_date)}.csv", index = False)
    temple_data.to_csv(f"./data/temple-{str(current_date)}.csv", index = False)
    
    # Temple Dimension Data: https://churchofjesuschristtemples.org
    # + https://church-of-jesus-christ-facts.net
    get_temple_data().to_csv(f"./data/temple-dim-{str(current_date)}.csv", index = False)

if __name__ == '__main__':
    main()
