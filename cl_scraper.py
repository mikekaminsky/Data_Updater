'''
Craigslist Scraper
cl_scraper.py
https://github.com/mikekaminsky/craigslist_scraper

12/2013
'''

from bs4 import BeautifulSoup
import urllib2
import re
import os
import os.path
import time
from pandas import *
import numpy as np
import csv
import smtplib
import getpass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class cl_scraper(object):
    '''
    Class to serve as a container craigslist search. 

    Parameters
    ----------
    '''
    def __init__(self):
        '''
        Initialize a new instance of cl scrapper
        
        '''

    def load_query_terms(self,query_file,header=True):
        '''
        load in query parameters and store as pandas dataframe
        
        Parameters
        ----------
        query_file : string
            -Matrix of query parameters
            -columns are ID, location and search term
        header : bool
            -assume that query_file has header for columns

        '''
        if header:
            query_list=read_csv(query_file)
        else:
            query_list=read_csv(query_file,header=None)
        self.query_list = query_list
        
    def run_cl_query(self,location,query):
        '''
            1) Pull all of the html listings from craigslist
               using the URL to query.

        Parameters
        ----------
        location : string
            -valid craiglist location to search in
            -must be from the craigslist url
        query : string
            -search query. words separated by spaces.
        '''

        #The URL that returns the search results
        url = 'http://'+location+'.craigslist.org/search/sss?query='+query.replace(' ', '+')+'&zoomToPosting=&minAsk=&maxAsk=&sort=rel'
        ploop = 0
        while ploop < 1:
            if ploop == 0:
                page = urllib2.urlopen(url)
            else:
                resultnum = str(ploop*100)
                next = 'http://'+location+'.craigslist.org/search/?s='+resultnum+'&areaID=3&catAbb=sss&query='+query.replace(' ', ',')+'&sort=rel'
                page = urllib2.urlopen(next)
            ploop = ploop+1
            soup = BeautifulSoup(page)
            if ploop == 1:
                rows = soup.find_all("p","row")
            else:
                rows.append(soup.find_all("p","row"))
            #Here we extract the listings (defined above) for each page
            #rows.append(new_rows)
            next = soup.find(class_="button next")
            if 'href' not in str(next):
                ploop = 10      

        self.rows = rows 

    def extract_listings(self,rows,query,location,title_strict=True):
        '''
            1) Extract information from each listing from the 
               html.
            2) Return dataframe with all information from html

            Parameters
            ----------
            rows : BeautifulSoup object 
                - Contains 'row' class from html search results
            title_strict : boolean 
                -If title_strict == True then only results with at least one word from the
                query in the title will be saved.
        '''
        #Initiate empty lists that will be filled in as the program iterates through the search 
        #results
        price_list = []
        date_list = []
        title_list = []
        url_list = []
        type_list = []

        for row in rows:
            price = row.find(class_ = "price")
            date_title = row.find(class_ = "pl")
            date = date_title.find(class_ = "date")
            title = date_title.find('a')
            title_string = title.contents[0]
            url = unicode(date_title.find('a')['href'])
            type = row.find(class_="gc")
            #For each list, if one of the search terms is in the title
            #if price is not None and (term1 in title_string.lower() or term2 in title_string.lower()):
            if title_strict == True:
                tester=0
                for terms in query.split():
                    if terms.lower() in title_string.lower():
                        tester = 1
            else:
                tester = 1
            #Use 'http' not in url to limit to only local results.
            #Non-local results are formatted differently and we do not want to include
            if price is not None and tester == 1 and 'http' not in url:
                #Append the price, date, title, type, and url to the list.
                price_list.append(unicode(price.contents[0]))
                date_list.append(unicode(date.contents[0]))
                title_list.append(unicode(title.contents[0]))
                type_list.append(unicode(type.contents[0]))
                url_list.append(location+'.craigslist.org'+url)

        #Create dataframe by concatenating lists
        cl_info=DataFrame({'date':date_list,'title':title_list,'price':price_list, 'url':url_list,'type':type_list})

        self.cl_info = cl_info

    def update_database(self,data_path,query_id,cl_info):
        '''
            Create a 'results' table with 
                1) duplicates removed
                2) a 'date_pulled' with the earliest date result was returned

            Parameters
            ----------
            data_path : string
                - Path to folder where .csv data files are stored
            query_id : integer 
                - Unique ID for query+location combination 
            cl_info : Pandas dataframe 
                - Contains craigslist information from html search results 
        '''

        ###################################################
        #Permanent Data Tables
        raw_search_history = data_path + "raw_search_history.csv"
        unique_search_history = data_path + "unique_search_history.csv"
        new_results = data_path + "new_results.csv"
        query_info = data_path + "query_info.csv"
        ###################################################

        #Get the date
        #dd/mm/yyyy format
        today = time.strftime("%Y/%m/%d")

        cl_info['date_ran']=today
        cl_info['query_id']=query_id

        #################################
        #Add to raw history -- simply stacking all the results found with every search
        #################################

        cl_info.to_csv(raw_search_history, mode = 'a',header=False, index=False)

        #################################
        #Add to unique search history
        #################################

        #if unique_search_history table exists,
        #read unique search history
        if os.path.isfile(unique_search_history):
            all_unique = read_csv(unique_search_history)
            query_unique = all_unique[all_unique.query_id == query_id]
            other_unique = all_unique[all_unique.query_id != query_id]
            #Append current results to unique history
            query_unique = query_unique.append(cl_info)
        else:
            query_unique=cl_info


        #Clean price to get as number (i.e., remove $ and commas)
        query_unique['tempprice'] = query_unique.price.str.strip('$')
        query_unique['tempprice'] = query_unique.tempprice.str.replace(',','')
        query_unique['tempprice'] = query_unique.tempprice.str.strip()
        query_unique ['price_num'] = query_unique.tempprice.map(lambda x: x[0:]).astype('float')

        del query_unique ['tempprice']
        #Sort so that we take the oldest results when removing duplicates
        #May cause issues with URLs. May want to revisit sort order so newest
        #URLs are kept but oldest dates are kept.
        #How?
        sorted_unique=query_unique.sort(['query_id','title','price_num', 'date', 'date_ran'],ascending=False)

        #Remove duplicates by keys
        keys='query_id','title','price_num'
        unique=sorted_unique.drop_duplicates(cols=keys,take_last=True)

        #Write unique history back to CSV
        unique_total =concat([unique,other_unique],axis=0)
        unique_total.to_csv(unique_search_history,index=False)

    def build_emails(self,data_path,query_id):
        '''
            Build email with the 'new' results from craigslist

            Parameters
            ----------
            data_path : string
                - Path to folder where .csv data files are stored
            query_id : integer 
                - Unique ID for query+location combination 
        '''

        #Get the date
        #dd/mm/yyyy format
        today = time.strftime("%Y/%m/%d")

        #################################
        #Select ones where today = todays date
        #These should be unique instances where there was a new
        #post today.
        #################################

        all_unique = read_csv(unique_search_history)
        todays_results = all_unique[(all_unique.query_id == query_id) & (all_unique.date_ran == today)]

        if todays_results.empty:

            header1="""\
            <html>
            <head>
            </head>
            <body>
            <p>Sorry, there are no new search results for 
            """

            quote_query = '"%s"' % query


            header2="""\
            . Better luck next time!</p>
            </body>
            </html>
            """

            #Compile Automatically Generated HTML Code
            html = header1+quote_query+header2

        else:

            todays_results = todays_results.sort(['date','price_num'], ascending=[0,1])

            #Conve to HTML Links
            links = '<a href ="' + todays_results.url + '">'+ todays_results.date + ' - ' + todays_results.price + ' - ' + todays_results.title +  '</a> <br>'
            html_link_block = ''.join(links)

            header1="""\
            <html>
            <head>
            </head>
            <body>
            <p>Here are your new search results for 
            """

            quote_query = '"%s"' % query


            header2="""\
            , sorted by date (most recent first) and price (low to high):</p>
            <p>
            """

            tail="""\
                </p>
            </body>
            </html>
            """

            #Compile Automatically Generated HTML Code
            html = header1+quote_query+header2+html_link_block+tail

        # Create message container - the correct MIME type is multipart/alternative.
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "New Craigslist Postings!"

        # Record the MIME types of both parts - text/plain and text/html.
        part1 = MIMEText(html, 'html')

        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message, in this case
        # the HTML message, is best and preferred.
        msg.attach(part1)
        self.email_message = msg.as_string()


    def send_emails(self,email_message,from_email,to_email,password):
        '''
            Build email with the 'new' results from craigslist

            Parameters
            ----------
            data_path : string
                - Path to folder where .csv data files are stored
            query_id : integer 
                - Unique ID for query+location combination 
        '''
        server = 'smtp.gmail.com:587'

        # Send the message via local SMTP server.
        s = smtplib.SMTP(server)
        s.starttls()  
        s.login(from_email,password) 
        # sendmail function takes 3 arguments: sender's address, recipient's address
        # and message to send - here it is sent as one string.
        s.sendmail(from_email, to_email, email_message)
        s.quit()










