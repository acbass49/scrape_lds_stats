import pandas as pd
from helium import *
import datetime
import time
import os
from selenium.webdriver.chrome.options import Options
import requests
import base64
import json
from bs4 import BeautifulSoup

def get_insta_followers_w_proxyscrape(handle, save_screenshot = False):
    
    attempts = 1
    while attempts < 50:
        
        #Set up URL
        url = f'https://www.instagram.com/{handle}/'
        
        # Set up json instructions for proxyscrape
        data = {
            "url": url,
            "browserHtml": True,
            "screenshot": True,
            "screenshotOptions": {
                "format": "jpeg",
                "fullPage": True
            },
            'actions' : [
                {
                    "action": "waitForTimeout",
                    "timeout": 10    
                },
                {
                    'action': 'click',
                    "selector": {
                        "type": "css",
                        "value": 'div[class="x1i10hfl xjqpnuy xa49m3k xqeqjp1 x2hbi6w xdl72j9 x2lah0s xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1q0g3np x1lku1pv x1a2a7pz x6s0dn4 xjyslct x1ejq31n xd10rxx x1sy0etr x17r0tee x9f619 x1ypdohk x1f6kntn xwhw2v2 xl56j7k x17ydfre x2b8uid xlyipyv x87ps6o xcdnw81 x1i0vuye xh8yej3 xjbqb8w xm3z3ea x1x8b98j x131883w x16mih1h x972fbf xcfux6l x1qhh985 xm0m39n xt7dq6l xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6 x1n5bzlp x173jzuc x1yc6y37 x3nfvp2"]'
                    }
                },
                {
                    "action": "waitForTimeout",
                    "timeout": 10    
                },         
            ]
        }
        
        headers = {
            'Content-Type': 'application/json',
            'X-Api-Key': os.environ.get('SCRAPERAPI_API_KEY')
        }
        
        response = requests.post('https://api.proxyscrape.com/v3/accounts/freebies/scraperapi/request', headers=headers, json=data)
        
        if response.status_code == 200:
            json_response = response.json()
            if 'browserHtml' in json_response['data']:
                res = json_response['data']['browserHtml']
        else:
            print(f'Attempt {attempts}: error:',response.status_code)
            print(response.text)
            attempts += 1
            continue
        
        if save_screenshot:
            if 'screenshot' in json_response['data']:
                screenshot = json_response['data']['screenshot']
                with open(f'./data/{attempts}_screenshot.jpeg', 'wb') as f:
                    f.write(base64.b64decode(screenshot))
            else:
                print(f'Attempt {attempts}: Screenshot not found')
        
        #grab follower count from the rendered html
        soup = BeautifulSoup(res, 'html.parser')
        
        if soup.select('span[class="x5n08af x1s688f"][title]'):
            followers = soup.select('span[class="x5n08af x1s688f"][title]')[0]['title']
            followers_cleaned = int(followers.replace(",", ""))
            break
        else:
            print(f'Attempt {attempts}: Page rendered but followers not found', soup.select('span[class="x5n08af x1s688f"][title]'))
            attempts += 1
            
    if attempts == 50:
        print('Failed to scrape followers')
        followers_cleaned = "Failed to scrape"
        raise Exception('Failed to scrape followers')
    
    print("Success on attempt", attempts)
    
    return {handle: followers_cleaned}

answer = get_insta_followers_w_proxyscrape('churchofjesuschrist', save_screenshot=False)

current_d = datetime.datetime.now()
insta = pd.DataFrame({
    'account':'churchofjesuschrist',
    'social':'instagram',
    'date':datetime.date(current_d.year, current_d.month, current_d.day),
    'followers': answer['churchofjesuschrist']
}, index = [0])

user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 OPR/112.0.0.0'
link = 'https://x.com/Ch_JesusChrist?ref_src=twsrc%5Egoogle%7Ctwcamp%5Eserp%7Ctwgr%5Eauthor'
options = Options()
options.add_argument(f'user-agent={user_agent}')
driver = start_chrome(url = link, headless=True,options=options)
time.sleep(10)
driver.execute_script("window.scrollTo(0, 150)")
time.sleep(10)
hover("Followers")
time.sleep(5)
followers = find_all(S("span[style = 'text-overflow: unset;']", above="Affiliates", below="Followers"))[0].web_element.text
driver.save_screenshot('./data/screen2.png')
kill_browser()

twitter = pd.DataFrame({
    'account':'churchofjesuschrist',
    'social':'twitter',
    'date':datetime.date(current_d.year, current_d.month, current_d.day),
    'followers':int(followers.replace(",",""))
}, index = [0])

fpath = './data/social_count.csv'
if os.path.isfile(fpath):
    full_file = pd.read_csv(fpath)
    data = pd.concat([full_file, insta, twitter], ignore_index=True)
else:
    data = pd.concat([insta, twitter], ignore_index=True)

data.drop_duplicates(subset=['account', 'social', 'date'], inplace=True)

data.to_csv(fpath, index = False)
