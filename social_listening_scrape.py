import pandas as pd
from helium import *
import datetime
import time
import os

count = 1
while count<3:
    try:
        current_d = datetime.datetime.now()
        link = 'https://www.instagram.com/churchofjesuschrist/?hl=en'
        driver = start_chrome(url = link, headless=True)
        time.sleep(10)
        followers = find_all(S("span[class = 'x5n08af x1s688f']"))[1].web_element.get_attribute("title")

        insta = pd.DataFrame({
            'account':'churchofjesuschrist',
            'social':'instagram',
            'date':datetime.date(current_d.year, current_d.month, current_d.day),
            'followers':int(followers.replace(",",""))
        }, index = [0])
        count = 4
    except:
        time.sleep(3)
        kill_browser()
        if count == 3:
            insta = None
        count += 1

count = 1
while count<3:
    try:
        current_d = datetime.datetime.now()
        link = 'https://x.com/Ch_JesusChrist?ref_src=twsrc%5Egoogle%7Ctwcamp%5Eserp%7Ctwgr%5Eauthor'
        driver = start_chrome(url = link, headless=True)
        driver.maximize_window()
        time.sleep(10)
        driver.execute_script("window.scrollTo(0, 150)")
        time.sleep(10)
        hover("Followers")
        time.sleep(5)
        followers = find_all(S("span[style = 'text-overflow: unset;']", above="Affiliates", below="Followers"))[0].web_element.text

        twitter = pd.DataFrame({
            'account':'churchofjesuschrist',
            'social':'twitter',
            'date':datetime.date(current_d.year, current_d.month, current_d.day),
            'followers':int(followers.replace(",",""))
        }, index = [0])
        count = 4
    except:
        kill_browser()
        time.sleep(3)
        if count == 3:
            twitter = None
        count += 1

fpath = './data/social_count.csv'
if os.path.isfile(fpath):
    full_file = pd.read_csv(fpath)
    data = pd.concat([full_file, insta, twitter], ignore_index=True)
else:
    data = pd.concat([insta, twitter], ignore_index=True)

data.drop_duplicates(subset=['account', 'social', 'date'], inplace=True)

data.to_csv(fpath, index = False)
