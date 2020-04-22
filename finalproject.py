from bs4 import BeautifulSoup
import requests
import sys
import secrets

################## global vars ##############################
CACHE_FILENAME = "ers_bea_cache.json"
CACHE_DICT = {}
#############################################################

########################## will prob delete soon ######################
# main_url = "https://www.ers.usda.gov"
# response = requests.get(main_url)
# soup = BeautifulSoup(response.text, "html.parser")

# ## homepage
# homepage_soup = soup.find_all(class_='nav navbar-nav')
# data_products_item = homepage_soup[0].find('a', href='/data-products/')

# ## data products page
# data_products_url = (main_url + data_products_item['href'])

# # print(f"URL: {data_products_url}")

# ## finding county-level url
# data_products_response = requests.get(data_products_url)
# soup2 = BeautifulSoup(data_products_response.text, "html.parser")
# print(f"SOUP: {soup2.prettify()}")
######################################################################
API_KEY = secrets.rapid_api_key
covid_url = "https://covid-193.p.rapidapi.com/statistics"
querystring = {"country" : "United States"}
headers = {
	'x-rapidapi-host' : "covid-193.p.rapidapi.com",
	'x-rapidapi-key' : API_KEY
}
def make_request(base_url):
	'''Calls the rapid api and returns a json of coronavirus cases across by country.

	parameters
	----------
	base_url : str
		the url used to call the api

	returns
	-------
	dict
		a dictionary of countries

	'''
	response = requests.request("GET", base_url, headers=headers)
	return response.json()

if __name__ == '__main__':
	all_countries = make_request(covid_url)['response']
	for country in all_countries:
		print(country['country'])
		print(country['cases'])


