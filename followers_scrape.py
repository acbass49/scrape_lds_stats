import pandas as pd
from helium import *
import datetime
import time
import os
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc


current_d = datetime.datetime.now()
user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 OPR/112.0.0.0'
link = 'https://www.instagram.com/churchofjesuschrist'
# options = Options()
# options.add_argument(f'user-agent={user_agent}')
driver = uc.Chrome(headless=True,use_subprocess=False)
time.sleep(10)
# followers = find_all(S("span[class = 'x5n08af x1s688f']"))[1].web_element.get_attribute("title")

# insta = pd.DataFrame({
#     'account':'churchofjesuschrist',
#     'social':'instagram',
#     'date':datetime.date(current_d.year, current_d.month, current_d.day),
#     'followers':int(followers.replace(",",""))
# }, index = [0])
driver.save_screenshot('./data/screen1.png')
driver.close() # `quit` to end all sessions

link = 'https://x.com/Ch_JesusChrist?ref_src=twsrc%5Egoogle%7Ctwcamp%5Eserp%7Ctwgr%5Eauthor'
options = Options()
options.add_argument(f'user-agent={user_agent}')
driver = start_chrome(url = link, headless=True,options=options)
time.sleep(10)
driver.execute_script("window.scrollTo(0, 150)")
time.sleep(10)
# hover("Followers")
# time.sleep(5)
# followers = find_all(S("span[style = 'text-overflow: unset;']", above="Affiliates", below="Followers"))[0].web_element.text
driver.save_screenshot('./data/screen2.png')
kill_browser()

# twitter = pd.DataFrame({
#     'account':'churchofjesuschrist',
#     'social':'twitter',
#     'date':datetime.date(current_d.year, current_d.month, current_d.day),
#     'followers':int(followers.replace(",",""))
# }, index = [0])
# count = 4

# fpath = './data/social_count.csv'
# if os.path.isfile(fpath):
#     full_file = pd.read_csv(fpath)
#     data = pd.concat([full_file, insta, twitter], ignore_index=True)
# else:
#     data = pd.concat([insta, twitter], ignore_index=True)

# data.drop_duplicates(subset=['account', 'social', 'date'], inplace=True)

# data.to_csv(fpath, index = False)
