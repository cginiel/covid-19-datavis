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
from flask import Flask, render_template, request
import plotly.graph_objects as go


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
    make_request_with_cache(wikipedia_url, soup.prettify())

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
            cleaned_headings.append(h3)
        cleaned_headings.append(h)
    cleaned_headings.remove(cleaned_headings[4])
    cleaned_headings.remove(cleaned_headings[5])

    countries_list = []
    UN_CR_list = []
    UN_SR_list = []
    pop_2018_list = []
    pop_2019_list = []
    change_list = []
    countries_pop_dict = {}

    countries_table = soup.find_all('table', class_='sortable')
    tbody = countries_table[0].find('tbody')
    trs = tbody.find_all('tr', recursive=False)

    for tr in trs: # we have to loop through each tr to get to the tds
        tds = tr.find_all('td') # here lie our tds
        if not tds: # ignore empty elements
            continue

        # we get our country name by indexing the tds (since there are many tds per tr)
        country_name = tds[0].text.strip() 
        if "[" in country_name:
            country_name = country_name[:-3] # cleaning the wikipedia notation off of the names
        countries_list.append(country_name)
        
        # add UN continental region data to list
        continental_region = tds[1].text.strip()
        UN_CR_list.append(continental_region)
        
        # add UN statistical region to list
        statistical_region = tds[2].text.strip()
        UN_SR_list.append(statistical_region)

        # add 2018 population, clean comma and convert to int
        pop_2018 = tds[3].text.strip()
        if ',' in pop_2018:
            pop_2018 = pop_2018.replace(',', '')
        pop_2018 = int(pop_2018)
        pop_2018_list.append(pop_2018)

        # add 2019 population, clean comma and convert to int
        pop_2019 = tds[4].text.strip()
        if ',' in pop_2019:
            pop_2019 = pop_2019.replace(',', '')
        pop_2019 = int(pop_2019)
        pop_2019_list.append(pop_2019)

        # add population change percentage
        change = tds[5].text.strip()
        change_list.append(change)

    for i in range(len(countries_list)):
        countries_pop_dict[countries_list[i]] = {
            'UN continental region': UN_CR_list[i],
            'UN statistical region': UN_SR_list[i],
            '2018 population': pop_2018_list[i],
            '2019 population': pop_2019_list[i],
            'percentage population change': change_list[i]
        }

    return countries_pop_dict


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
        # add countries
        c = country['country']
        if c == "USA":
            c = "United States"
        if c == "S-Korea":
            c = "South Korea"
        countries_list.append(c)

        # add active cases, convert None to 0
        active_cases = country['cases']['active']
        if active_cases == None:
            active_cases = 0
        active_cases_list.append(active_cases)

        # add total cases, convert None to 0
        total_cases = country['cases']['total']
        if total_cases == None:
            total_cases = 0
        total_cases_list.append(total_cases)

        # clean the plus sign off of new cases, convert None to 0
        new_cases = country['cases']['new']
        if new_cases != None:
            new_cases = new_cases[1:]
        if new_cases == None:
            new_cases = 0
        new_cases_list.append(new_cases)

        # clean the plus sign off of new deaths, convert None to 0
        new_deaths = country['deaths']['new']
        if new_deaths != None:
            new_deaths = new_deaths[1:]
        if new_deaths == None:
            new_deaths = 0
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
    drop_country_population_sql = 'DROP TABLE IF EXISTS "Population"'
    

    create_covid_cases_sql = '''
        CREATE TABLE IF NOT EXISTS "Cases" (
            "Id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "Country" TEXT NOT NULL,
            "NewCases" INTEGER NOT NULL,
            "ActiveCases" INTEGER NULL,
            "NewDeaths" INTEGER NOT NULL,
            "TotalCases" INTEGER NULL
        )
    '''

    create_country_population_sql = '''
        CREATE TABLE IF NOT EXISTS "Population" (
            "Id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "Country" TEXT NOT NULL,
            "UNContinentalRegion" TEXT NOT NULL,
            "UNStatisticalRegion" TEXT NOT NULL,
            "2018population" INTEGER NOT NULL,
            "2019population" INTEGER NOT NULL,
            "PopulationChange" TEXT NOT NULL
        )
    '''

    cur.execute(drop_covid_cases_sql)
    cur.execute(create_covid_cases_sql)
    cur.execute(drop_country_population_sql)
    cur.execute(create_country_population_sql)
    conn.commit()
    conn.close()


def load_cases():
    '''Loads covid cases into a SQL database.

    params
    ------
    None

    returns
    -------
    None
    '''
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
    

def load_population():
    '''Loads countries' population data into a SQL database.

    params
    ------
    None

    returns
    -------
    None
    '''
    pop_dict = scrape_wiki_data()

    insert_sql = '''
        INSERT INTO Population
        VALUES (NULL, ?, ?, ?, ?, ?, ?)
    '''

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    for k,v in pop_dict.items():
        cur.execute(insert_sql,[
            k,
            v['UN continental region'],
            v['UN statistical region'],
            v['2018 population'],
            v['2019 population'],
            v['percentage population change']
            ]
        )
    conn.commit()
    conn.close()


##################### user entry ##########################
def access_cases_table(country):
    '''Selects a country's COVID-19 data from the SQL database to display based on user entry.

    Params
    ------
    country : str
        A country to search for in the database.

    Returns
    -------
    list
        A country's corresponding COVID-19 data.
    '''
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    if country.lower() == "all":
        q = f'''
            SELECT Country, TotalCases
            FROM Cases
            ORDER BY TotalCases DESC
        '''

    else:
        q = f'''
            SELECT NewCases, ActiveCases, NewDeaths, TotalCases
            FROM Cases
            WHERE Country = "{country}"
        '''
    result = cur.execute(q).fetchall()
    conn.close()
    return result


def access_population_table(country):
    '''Selects a country's population from the SQL database to display based on user entry.

    Params
    ------
    country : str
        A country to search for in the database.

    Returns
    -------
    list
        A country's corresponding population data.
    '''
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    q = f'''
        SELECT "2019population"
        FROM Population
        WHERE Country = "{country}"
    '''
    result = cur.execute(q).fetchall()
    conn.close()
    return result


##################### data vis ############################
def create_and_display_graphs(user_input):
    '''Uses plotly to make a bar graph out of user selected data. Launches the plotly graph in the user's browser.

    params
    ------
    user_input : str
        the information the user searches for

    returns
    -------
    none
    '''
    if user_input.lower() == "all":

        xvals = []
        yvals = []
        for d in access_cases_table(user_input):
            xvals.append(d[0])
            yvals.append(d[1])

        bar_data = go.Bar(x=xvals, y=yvals)

        basic_layout = go.Layout(title=f"Combined New, Active, and Former COVID-19 cases across the globe",
            xaxis_title = "Country",
            yaxis_title = "No. People Infected",
            font=dict(
                family="Roboto Slab, monospace",
                size=14,
                color="#000"
                ),
            )
        

    else:
        xvals = ['New Cases', 'Active Cases', 'New Deaths', 'Total Cases']
        yvals = []

        for d in access_cases_table(user_input):
            yvals.append(d[0])
            yvals.append(d[1])
            yvals.append(d[2])
            yvals.append(d[3]) 

        bar_data = go.Bar(x=xvals, y=yvals)

        basic_layout = go.Layout(title=f"COVID-19 cases in {user_input.title()}",
            xaxis_title = "Types of cases",
            yaxis_title = "People Infected/Affected",
            font=dict(
                family="Roboto Slab, monospace",
                size=14,
                color="#000"
            ),
            margin_b=125, #increase the bottom margin to have space for caption
            annotations=[dict(xref='paper',
                yref='paper',
                x=0.5,
                y=-0.25,
                showarrow=False,
                font=dict(size=15, color="black"),
                # text=f"The gap between the average living wage in {user_input.title()} and state minimum wage is"
                )]
            )

    fig = go.Figure(data=bar_data, layout=basic_layout)
    return fig.show()


if __name__ == '__main__':
    CACHE_DICT = open_cache()
    create_covid_cases_dict(make_request(covid_url))
    scrape_wiki_data()
    create_db()
    load_cases()
    load_population()

    create_and_display_graphs("all")
    
    # while True:
    #     view_data = input(f'''
    #         View COVID-19 statistics by country.\n
    #         To view a list of all recorded countries, type "view"\n
    #         Otherwise, type in a country (e.g. USA, Japan, Brazil), or \"exit\" to quit:\n''') 
    #     view_data = view_data.lower()
    #     if view_data == 'exit':
    #         sys.exit()
    #     elif view_data == "view":
    #         pass
    #     else:
    #         pass
    


    

    



