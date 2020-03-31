from bs4 import BeautifulSoup
import requests
import sys

################## global vars ##############################
CACHE_FILENAME = "ers_bea_cache.json"
CACHE_DICT = {}
#############################################################


main_url = "https://www.ers.usda.gov"
response = requests.get(main_url)
soup = BeautifulSoup(response.text, "html.parser")

## homepage
homepage_soup = soup.find_all(class_='nav navbar-nav')
data_products_item = homepage_soup[0].find('a', href='/data-products/')

## data products page
data_products_url = main_url + data_products_item['href']

## finding county-level url
data_products_response = requests.get(data_products_url)
soup2 = BeautifulSoup(data_products_response.text, "html.parser")
data_products_soup = soup2.find_all(class_='dp-figure-list')

for item in data_products_soup:
	print(f"WHAT AM I: {item}\n\n\n")


# print(data_products_soup)

