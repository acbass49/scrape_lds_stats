from bs4 import BeautifulSoup
import requests
import re
import json
import pandas as pd

BASE_STR = "https://newsroom.churchofjesuschrist.org"

def get_links(base_link, base_str=BASE_STR):
    '''Uses base link to get every state or country link on page'''
    res = requests.get(base_link)
    soup = BeautifulSoup(res.content, "html.parser")

    # New format: extract from __NEXT_DATA__ JSON
    next_data_tag = soup.find("script", {"id": "__NEXT_DATA__"})
    if next_data_tag:
        raw = next_data_tag.text
        paths = re.findall(r'facts-and-statistics/(?:country|state)/[a-z0-9-]+', raw)
        return [base_str + "/" + p for p in sorted(set(paths))]

    # Old format: find links in HTML nav
    links = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/facts-and-statistics/country/" in href or "/facts-and-statistics/state/" in href:
            full = base_str + href
            if full not in seen:
                seen.add(full)
                links.append(full)
    return links


def get_data(link):
    '''Given a link, parses text and returns dictionary of data'''
    res = requests.get(link)
    soup = BeautifulSoup(res.content, "html.parser")

    data_dict = {}
    name = re.subn(r' - .+', "", soup.title.text)[0]
    name = re.sub(r'^The Church of Jesus Christ of Latter-day Saints in ', '', name)
    name = re.sub(r'^The Church in the ', '', name)
    name = re.sub(r'^The Church in ', '', name)
    name = re.sub(r'^The Church of Jesus Christ of Latter-day Saints ', '', name)
    name = name.strip()
    name = name.replace('\u02bb', '').replace('\u2018', '').replace('\u2019', '')
    name = name[0].upper() + name[1:] if name else name
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

    # New format: extract from __NEXT_DATA__ JSON
    next_data_tag = soup.find("script", {"id": "__NEXT_DATA__"})
    if next_data_tag:
        page_data = json.loads(next_data_tag.text)
        stats = _find_location_stats(page_data)
        if stats:
            data_dict['TotalChurchMembership'] = _safe_int(stats.get('churchMembership'))
            data_dict['Stakes'] = _safe_int(stats.get('stakes'))
            data_dict['Congregations'] = _safe_int(stats.get('congregations'))
            data_dict['Wards'] = _safe_int(stats.get('wards'))
            data_dict['Branches'] = _safe_int(stats.get('branches'))
            data_dict['FamilySearchCenters'] = _safe_int(stats.get('familyHistoryCenters'))
            data_dict['Temples'] = _safe_int(stats.get('temples'))
            data_dict['Missions'] = _safe_int(stats.get('missions'))
            data_dict['Districts'] = _safe_int(stats.get('districts'))
            return data_dict

    # Old format: use CSS selectors
    data_string = _get_data_string(soup)
    for metric in metrics:
        data_dict[metric] = _get_data_in_string(data_string, metric)
    return data_dict


def _safe_int(value):
    '''Converts a value to int, returning 0 if not numeric'''
    try:
        return int(str(value).replace(',', ''))
    except (ValueError, TypeError):
        return 0


def _find_location_stats(data):
    '''Finds the most specific location stats object in __NEXT_DATA__ JSON.
    Prioritizes stateProvinceStatistics > countryStatistics.'''
    state_results = []
    country_results = []

    def search(obj):
        if isinstance(obj, dict):
            model = obj.get('$model', '')
            if model == 'stateProvinceStatistics' and 'churchMembership' in obj:
                state_results.append(obj)
            elif model == 'countryStatistics' and 'churchMembership' in obj:
                country_results.append(obj)
            for v in obj.values():
                search(v)
        elif isinstance(obj, list):
            for item in obj:
                search(item)

    search(data)
    if state_results:
        return state_results[0]
    return country_results[0] if country_results else None


def _get_data_string(soup):
    '''Uses CSS selectors to parse text into manageable piece (old format pages)'''
    text1 = soup.select(".stat-line.one-fifth")[0].text
    text1 = text1.split()

    text2 = soup.select(".stat-line.w-graph")[0].text
    text2 = re.subn(pattern=" ", repl="", string=text2)[0]
    text2 = text2.split()

    return text1 + text2


def _get_data_in_string(string, name):
    '''Given a metric name, finds data for that name'''
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

        to_it = soup.select('pre')[1].text.replace("\xa0", " ").split('\r\n')
        to_it = [x for x in to_it if len(x) > 0]

        pattern = re.compile(r"\s\s+")

        col_names = pattern.split(to_it[0])
        col_names = [x for x in col_names if len(x) > 0]

        df = []
        for row in to_it[1:]:
            row = pattern.split(row)
            row = [x for x in row if len(x) > 0]
            tmp_dict = {
                col_names[0]: row[0],
                col_names[1]: row[1],
                col_names[2]: row[2],
                col_names[3]: row[3],
                col_names[4]: row[4],
            }
            if len(row) >= 6:
                tmp_dict[col_names[5]] = row[5]
            else:
                tmp_dict[col_names[5]] = ''
            df.append(tmp_dict)

        t_site_1 = pd.DataFrame(df) \
            .rename(columns={'Name and location': 'Temple'}) \
            .assign(Temple=lambda x: x.Temple.apply(_clean_names))
    except:
        raise Exception("church-of-jesus-christ-facts failed.")

    base_link = "https://churchofjesuschristtemples.org/statistics/dimensions/"
    res = requests.get(base_link)
    soup = BeautifulSoup(res.content, "html.parser")
    to_it = soup.select("tr")

    df = []
    for row in to_it[1:]:
        row = row.text.split("\n")
        row = [x for x in row if len(x) > 0]
        tmp_dict = {
            'Temple': row[0],
            'Instruction_Rooms': row[1],
            'Sealing_Rooms': row[2],
            'Baptismal_Fonts': row[3],
            'Square_Footage': row[4],
            'Acreage': row[5]
        }
        df.append(tmp_dict)

    t_site_2 = pd.DataFrame(df) \
        .assign(Temple=lambda x: x.Temple.apply(_clean_names))

    base_link = "https://churchofjesuschristtemples.org/statistics/features/"
    res = requests.get(base_link)
    soup = BeautifulSoup(res.content, "html.parser")
    to_it = soup.select("tr[class = 'clickable-row']")

    df = []
    for row in to_it:
        row = row.text.split("\n")
        row = [x for x in row if len(x) > 0]
        tmp_dict = {
            'Temple': row[0],
            'Num_Spires': row[1],
            'Spire_Attached': row[2],
            'Angel_Moroni': row[3]
        }
        df.append(tmp_dict)

    t_site_3 = pd.DataFrame(df) \
        .assign(Temple=lambda x: x.Temple.apply(_clean_names))

    t_site_2 = pd.merge(t_site_3, t_site_2, how='inner', on='Temple')
    data = pd.merge(t_site_1, t_site_2, how='inner', on='Temple')

    return data


def _clean_names(name):
    return name.lower().strip().replace(".", "") \
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
