'''
Craigslist Updater
cl_updater.py
https://github.com/mikekaminsky/craigslist_updater

12/2013
'''

import re
import os
import os.path
import time
from pandas import *
import numpy as np
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class cl_updater(object):
    '''
    Class to serve as a container for the craigslist updater app
    '''
    def __init__(self):
        '''
        Initialize a new instance of cl_data_cleaner
        
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
        
    def load_email_list(self,email_file,header=True):
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
            email_list=read_csv(email_file)
        else:
            email_list=read_csv(email_file,header=None)
        self.email_list = email_list
        
        
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
        

    def build_emails(self,data_path,query,query_id):
        '''
            Build email with the 'new' results from craigslist

            Parameters
            ----------
            data_path : string
                - Path to folder where .csv data files are stored
            query : string
                - Search term for craigslist
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
        unique_search_history = data_path + "unique_search_history.csv"


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














