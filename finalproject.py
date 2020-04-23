from bs4 import BeautifulSoup
import requests
import sys
import secrets

################## global vars ##############################
CACHE_FILENAME = "cache.json"
CACHE_DICT = {}

API_KEY = secrets.rapid_api_key
covid_url = "https://covid-193.p.rapidapi.com/statistics"
#############################################################

def get_wiki_data():
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
        cleaned_headings.append(h)
    # print(cleaned_headings)

    # find table columns
    with open('wiki_data.txt', 'w') as fo:
        for tr in countries_table[0].find_all('tr'):
            tds = tr.find_all('td')
            if not tds:
                continue
            # might want to figure out a better way to assign your data so you can add it to a dict
            for td in tds[:5]:
                cleaned_headings[0] = [td.text.strip()]
                print(cleaned_headings[0])
            # cleaned_headings[0], cleaned_headings[1], cleaned_headings[2], cleaned_headings[3], cleaned_headings[4] = [td.text.strip() for td in tds[:5]]
            # print('; '.join([cleaned_headings[0], cleaned_headings[1], cleaned_headings[2], cleaned_headings[3], cleaned_headings[4]]), file=fo)

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
    return response.json()

if __name__ == '__main__':
    ## light cleaning of the API json

    all_countries = make_request(covid_url)['response']
    for country in all_countries:
      print(country['country'])
      print(country['cases'])
    get_wiki_data()
    



