#######################
#Python Code to Pull URLs for a search term
#And organize database of past searches
#Started: 2013.12.11
#Last updated: 2013.12.11
#Michael Kaminsky
#######################

from bs4 import BeautifulSoup
import urllib2
import re
import os
import time
from pandas import *
import numpy as np
import csv
import smtplib
import getpass

#Get the date
#dd/mm/yyyy format
today = time.strftime("%Y/%m/%d")

data_path = "/Users/casebook/Mike_Projects/craigslist_scraper/data/"
passes = "C:/Users/Michael/Desktop/passwords.txt"

###################################################
#Permanent Data Tables
raw_search_history = data_path + "raw_search_history.csv"
unique_search_history = data_path + "unique_search_history.csv"
new_results = data_path + "new_results.csv"
query_info = data_path + "query_info.csv"
###################################################
execfile("pull_urls.py")


query_list=read_csv(query_info)


for index, row in query_list.iterrows():
     location = row['location']
     query = row['query']
     to_email = row['to_email']
     query_id = row['ID']
     print location, query, to_email
     cl_scraper(to_email = to_email, location = location, query = query, query_id=query_id)


     
     
     
     
     
     
     
     
