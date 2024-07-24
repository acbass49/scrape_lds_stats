from bs4 import BeautifulSoup
import requests
import re
import pandas as pd

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

def get_temple_data():

    try: 
        base_link = "https://church-of-jesus-christ-facts.net/temple5/"

        res = requests.get(base_link)
        soup = BeautifulSoup(res.content, "html.parser")

        to_it = soup.select('pre')[1].text.replace("\xa0"," ").split('\r\n')
        to_it = [x for x in to_it if len(x)>0]

        pattern = re.compile(r"\s\s+")

        col_names = pattern.split(to_it[0])
        col_names = [x for x in col_names if len(x)>0]

        df = []
        for row in to_it[1:]:
            row = pattern.split(row)
            row = [x for x in row if len(x)>0]
            tmp_dict = {
                col_names[0] : row[0],
                col_names[1] : row[1],
                col_names[2] : row[2],
                col_names[3] : row[3],
                col_names[4] : row[4],
            }
            if len(row)>=6:
                tmp_dict[col_names[5]] = row[5]
            else:
                tmp_dict[col_names[5]] = ''
            df.append(tmp_dict)
            
        t_site_1 = pd.DataFrame(df) \
            .rename(columns = {'Name and location':'Temple'}) \
            .assign(Temple = lambda x:x.Temple.apply(_clean_names))
    except:
        raise Exception("church-of-jesus-christ-facts failed.")

    base_link = "https://churchofjesuschristtemples.org/statistics/dimensions/"
    res = requests.get(base_link)
    soup = BeautifulSoup(res.content, "html.parser")
    to_it = soup.select("tr")

    df = []
    for row in to_it[1:]:
        row = row.text.split("\n")
        row = [x for x in row if len(x)>0]
        tmp_dict = {
            'Temple' : row[0],
            'Instruction_Rooms' : row[1],
            'Sealing_Rooms' : row[2],
            'Baptismal_Fonts' : row[3],
            'Square_Footage' : row[4],
            'Acreage': row[5]
        }
        df.append(tmp_dict)

    t_site_2 = pd.DataFrame(df) \
        .assign(Temple = lambda x:x.Temple.apply(_clean_names))

    base_link = "https://churchofjesuschristtemples.org/statistics/features/"
    res = requests.get(base_link)
    soup = BeautifulSoup(res.content, "html.parser")
    to_it = soup.select("tr[class = 'clickable-row']")

    df = []
    for row in to_it:
        row = row.text.split("\n")
        row = [x for x in row if len(x)>0]
        tmp_dict = {
            'Temple' : row[0],
            'Num_Spires' : row[1],
            'Spire_Attached' : row[2],
            'Angel_Moroni' : row[3]
        }
        df.append(tmp_dict)

    t_site_3 = pd.DataFrame(df) \
        .assign(Temple = lambda x:x.Temple.apply(_clean_names))

    t_site_2 = pd.merge(t_site_3, t_site_2, how='inner',on='Temple')

    data = pd.merge(t_site_1, t_site_2, how='inner',on='Temple')

    return data

def _clean_names(name):
    return name.lower().strip().replace(".","") \
        .replace("á", "a") \
        .replace('é', 'e') \
        .replace('ó', 'o') \
        .replace('é', 'e') \
        .replace("ã", "a") \
        .replace("í", "i") \
        .replace("seoul korea temple", "seoul south korea temple") \
        .replace("mt timpanogos utah temple", "mount timpanogos utah temple") \
        .replace("bogota dc colombia temple", "bogota colombia temple") \
        .replace("trujillo mexico temple", "trujillo peru temple") \
        .replace("caracas df venezuela temple", "caracas venezuela temple") \
        .replace("kinshasa dem republic of congo temple", "kinshasa democratic republic of the congo temple") \
        .replace("merida yucatan mexico temple", "merida mexico temple") \
        .replace("mexico city df mexico temple", "mexico city mexico temple") \
        .replace("calgary alberta temple", "calgary canada temple")
