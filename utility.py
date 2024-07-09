from bs4 import BeautifulSoup
import requests
import re

def get_links(base_link):
    '''Uses base link to get every state or country link on page
    '''
    res = requests.get(base_link)
    soup = BeautifulSoup(res.content, "html.parser")

    links = []
    base_str = "https://newsroom.churchofjesuschrist.org"
    for link in soup.find_all("li"):
        if link.select("a") and link.select("a")[0].has_attr("data-code"):
            tmp_link = link.select("a")[0].get("href")
            if len(tmp_link)>10:
                links.append(base_str + tmp_link)
    return links

def get_data(link):
    '''Given a link, parses text and return dictionary of data
    '''
    res = requests.get(link)
    soup = BeautifulSoup(res.content, "html.parser")
    data_string = _get_data_string(soup)

    data_dict = {}

    name = re.subn(r' - .+',"",soup.title.text)[0]
    print(name)

    data_dict['Name'] = name

    metrics = [
        'TotalChurchMembership',
        'Stakes',
        'Congregations',
        'Wards',
        'Branches',
        'FamilySearchCenters',
        'Temples',
        'Missions',
        'Districts'
    ]

    for metric in metrics:
        data_dict[metric] = \
            _get_data_in_string(data_string, metric)

    return data_dict


def _get_data_string(soup):
    '''Uses CSS selectors to parse text into manageable piece
    '''
    #Missions
    text1 = soup.select(".stat-line.one-fifth")[0].text
    text1 = text1.split()

    #Everything else
    text2 = soup.select(".stat-line.w-graph")[0].text
    text2 = re.subn(
        pattern = " ", 
        repl = "", 
        string = text2
    )[0]
    text2 = text2.split()

    text = text1 + text2

    return text

def _get_data_in_string(string, name):
    '''given a metric name, finds data for that name
    '''
    if name in string:
        idx = string.index(name) - 1
        data = re.subn(",", "", string[idx])[0]
        if data.isdigit():
            return int(data)
        else:
            return 0
    return 0
