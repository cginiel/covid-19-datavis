#############################################################
################    Name: Cameron Giniel       ##############
################    Uniqname: cginiel          ##############
#############################################################

from bs4 import BeautifulSoup
import requests
import sys
import secrets
import json
import sqlite3

################## global vars ##############################
CACHE_FILENAME = "covid_cache.json"
CACHE_DICT = {}

API_KEY = secrets.rapid_api_key
covid_url = "https://covid-193.p.rapidapi.com/statistics"

DB_NAME = 'covid_stats.sqlite'
########### data gathering and sorting #################

def scrape_wiki_data():
    '''Parses wikipedia page for table contents.

    params
    ------
    none

    returns
    -------
    dict
        countries organized by their population data
    '''
    wikipedia_url = "https://en.wikipedia.org/wiki/List_of_countries_by_population_(United_Nations)"
    response = requests.get(wikipedia_url)
    soup = BeautifulSoup(response.text, "html.parser")

    countries_table = soup.find_all('table', class_='sortable')

    # search through table for headings
    table = countries_table[0].find_all('th')
    all_headings = [th.text.strip() for th in table]
    top_headings = all_headings[:6]
    cleaned_headings = []
    for h in top_headings:
        if "[4]" in h:
            h = h[0:-3]
        if "(" in h:
            h2 = h.split("(")
            h3 = " (".join(h2)
        cleaned_headings.append(h)
        # print(f"H: {h}")
    # print(cleaned_headings)

    # find table columns
    col1 = []
    col2 = []
    col3 = []
    col4 = []
    col5 = []
    col6 = []
    with open('wiki_data.txt', 'w') as fo:
        for tr in countries_table[0].find_all('tr'):
            tds = tr.find_all('td')
            if not tds:
                continue
            # might want to figure out a better way to assign your data so you can add it to a dict
            for td in tds[:6]:
                if "[u]" in td:
                    # print(td)
                    td = td[0:-3]
                # print(f"TD: {td.text.strip()}")
            col1, col2, col3, col4, col5, col6 = [td.text.strip() for td in tds[:6]]
            print(', '.join([col1, col2, col3, col4, col5, col6]), file=fo)
    # to make dict: think about how you can create a dictionary using the cleaned_headings for keys and the rows of the txt doc for values.


def make_request(base_url):
    '''Calls the rapid api and returns a json 
    of coronavirus cases by country and by continent and even a cruise ship.

    parameters
    ----------
    base_url : str
        the url used to call the api

    returns
    -------
    dict
        a dictionary of countries and continents
    '''
    querystring = {"country" : "United States"}
    headers = {
        'x-rapidapi-host' : "covid-193.p.rapidapi.com",
        'x-rapidapi-key' : API_KEY
    }

    response = requests.request("GET", base_url, headers=headers)
    make_request_with_cache(base_url, response.json())

    return response.json()


def create_covid_cases_dict(covid_json):
    '''Pulls a json from the covid API and returns a cleaned dictonary.

    params
    ------
    None

    returns
    -------
    dict
        a cleaned dictionary with a country as the key and 
        the values as corresponding new cases, new deaths,
        active cases, and total cases
    '''
    # all_countries = make_request(covid_url)['response']
    all_countries = covid_json['response']
    make_request_with_cache(covid_url, all_countries)

    countries_list = []
    new_cases_list = []
    active_cases_list = []
    total_cases_list = []
    new_deaths_list = []

    # add our data to their own lists
    for country in all_countries:
        countries_list.append(country['country'])
        active_cases_list.append(country['cases']['active'])
        total_cases_list.append(country['cases']['total'])

        # clean the plus sign off of new cases
        new_cases = country['cases']['new']
        if new_cases != None:
            new_cases = new_cases[1:]
        new_cases_list.append(new_cases)

        # clean the plus sign off of new deaths
        new_deaths = country['deaths']['new']
        if new_deaths != None:
            new_deaths = new_deaths[1:]
        new_deaths_list.append(new_deaths)

    covid_dict = {}

    for i in range(len(countries_list)):
        covid_dict[countries_list[i]] = {
            'new cases': new_cases_list[i],
            'active cases': active_cases_list[i],
            'new deaths': new_deaths_list[i],
            'total cases': total_cases_list[i]
        }

    return covid_dict


###################### caching ##########################
def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    dict
        the opened cache
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict


def save_cache(cache_dict):
    ''' Saves the current state of the cache to disk
    
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    
    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close() 


def make_request_with_cache(key, value):
    '''Issues a request to the cache saved to the device.

    If the item exists in the cache, the program will pull from that data.
    If the item does not exist in the cache, the program will create a key/value
    pair and save it to the cache dictionary

    Parameters
    ----------
    key
        list
    value
        list

    '''

    if key in CACHE_DICT.keys():
        print("Using cache")
        return CACHE_DICT[key]
    else:
        print("Fetching")
        CACHE_DICT[key] = value
        save_cache(CACHE_DICT)
        return CACHE_DICT[key]


##################### database ##########################
def create_db():
    ''' Create a SQL database if it doesn't already exist and populate data in the tables.
    If the database already exists, the function writes over the existing data.
    
    Parameters
    ----------
    None
    
    Returns
    -------
    None
    '''
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    drop_covid_cases_sql = 'DROP TABLE IF EXISTS "Cases"'
    

    create_covid_cases_sql = '''
        CREATE TABLE IF NOT EXISTS "Cases" (
            "Id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "Country" TEXT NOT NULL,
            "NewCases" INTEGER NULL,
            "ActiveCases" INTEGER NULL,
            "NewDeaths" INTEGER NULL,
            "TotalCases" INTEGER NOT NULL
        )
    '''

    cur.execute(drop_covid_cases_sql)
    cur.execute(create_covid_cases_sql)
    conn.commit()
    conn.close()

def load_cases():
    covid_dict = create_covid_cases_dict(make_request(covid_url))

    insert_sql = '''
        INSERT INTO Cases
        VALUES (NULL, ?, ?, ?, ?, ?)
    '''

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    for k,v in covid_dict.items():
        cur.execute(insert_sql,[
            k,
            v['new cases'],
            v['active cases'],
            v['new deaths'],
            v['total cases']
            ]
        )
    conn.commit()
    conn.close()


if __name__ == '__main__':
    conn = sqlite3.connect(DB_NAME)
    CACHE_DICT = open_cache()
    covid_dict = create_covid_cases_dict(make_request(covid_url))
    create_db()
    load_cases()
    # print(covid_dict)
    


    

    



