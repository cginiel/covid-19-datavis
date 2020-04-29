# SI 507 Final Project — COVID-19 statistics by country

COVID-19 statistics by country is a python script that allows users to search for basic data pertaining to
COVID-19 rates, such as number of new cases, active cases, new deaths, and total cases.

In their terminal, users can search for a country. The script will either open a web browser displaying
the relevant data via plotly, or, for one search method, it will simply print an output to the terminal.

## Packages required
```python
from bs4 import BeautifulSoup
import requests
import sqlite3
import plotly.graph_objects as go
```

There is also a secrets.py file that contains the key to make requests to the API.

## Usage
There are four main search functions this script can perform, all based on user entry via the terminal:
1. View COVID-19 cases across all countries (plotly)
2. View detailed COVID-19 information specific to a country (plotly)
3. View detailed COVID-19 information specific to a country, including country's total population (plotly)
4. View percentage of COVID-19 cases within a country's total population (terminal)
