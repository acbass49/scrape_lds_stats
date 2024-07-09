# Title: Main Script To Scrape LDS Stats
from bs4 import BeautifulSoup
import requests
import re
import pandas as pd
from utility import get_data, get_links
from datetime import date

def main():

    # Country-Level Data
    base_link_for_countries = "https://newsroom.churchofjesuschrist.org/facts-and-statistics"
    country_links = get_links(base_link_for_countries)
    dict_data = [get_data(link) for link in country_links]
    country_data = pd.DataFrame(dict_data)

    # State-Level Data
    base_link_for_states = "https://newsroom.churchofjesuschrist.org/facts-and-statistics/country/united-states"
    state_links = get_links(base_link_for_states)
    dict_data = [get_data(link) for link in state_links]
    state_data = pd.DataFrame(dict_data)

    current_date = date.today()
    country_data.to_csv(f"./data/country-{str(current_date)}.csv", index = False)
    state_data.to_csv(f"./data/state-{str(current_date)}.csv", index = False)

if __name__ == '__main__':
    main()
