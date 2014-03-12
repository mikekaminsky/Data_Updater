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

    def add_new_query(self, query_file, email_file,email, search_term, city,
                      area="", minprice="", maxprice="", category="sss",
                      pic=False, bedrooms=""):

        '''

       Add new query for emailing to database

        Parameters
        ----------
        query_file : string
        email_file : string
        email : string
            - Recipient email address
        search_term: string
            - e.g., "turntable", "'dog not included'"
        city : string.
            - City name. e.g., "newyork"
            - Must be a string that corresponds to a legitimate craigslist city
            - See : http://geo.craigslist.org/iso/us
        area : string
            - e.g., "brk" for Brooklyn or "nch" for north chicagoland
            - may need to pull this out of the url after querying
        minprice: string
            - e.g., "500"
            - The minimum value of the list price in the returned results
        maxprice: string
            - e.g., "1200"
            - The maximum value of the list price in the returned results
        category: string
            -"hhh" for housing
            -"bar" for barter
            -"mis" for missed conn]ctions
        bedrooms: string
            -"hhh" for housing
            -"bar" for barter
            -"mis" for missed connections
        pic: boolean
            -Requires that the post has a picture
        '''
        # Check to see if database exists
        if os.path.isfile(query_file) & os.path.isfile(email_file):
            #Read in the query_file
            query_list=read_csv(query_file,na_filter = False)

            query_list.bedrooms = query_list['bedrooms'].apply(str)
            query_list.minprice = query_list['minprice'].apply(str)
            query_list.maxprice = query_list['maxprice'].apply(str)

            #Check if there are already any observations for the same query
            original = query_list[
                    (query_list.search_term == search_term) & \
                    (query_list.city == city) & \
                    (query_list.area == area) & \
                    (query_list.minprice == minprice) & \
                    (query_list.maxprice == maxprice) & \
                    (query_list.category == category) & \
                    (query_list.bedrooms == bedrooms) & \
                    (query_list.pic == pic)]

            #if the 'original' dataframe is empty, add a new row to the database
            if original.empty:
                #find the max of the query_id
                new_id = max(query_list.id) + 1

                newquery=DataFrame({'id':new_id,'search_term':search_term, \
                    'city':city,'area':area, \
                    'minprice':minprice,'maxprice':maxprice, 'category':category, \
                    'bedrooms':bedrooms,'pic':pic}, index = [0])

                newquery.to_csv(query_file, mode = 'a',header=False, index=False)

            else:
                new_id = original['id'].irow(0)

            #Read in the query_file
            email_list=read_csv(email_file)
            #Check if there are already any observations for the same query
            original_email = email_list[(email_list.query_id == new_id) & \
                    (email_list.email == email)]

            #If there is not already a row for the query ID /email combo,
            #do nothing
            if original_email.empty:
                newemail=DataFrame({'query_id':new_id,'email':email}, index = [0])
                newemail.to_csv(email_file, mode = 'a',header=False, index=False)

        elif  os.path.isfile(query_file) and not os.path.isfile(email_file):
            print ("You must specify both a query and email file that exist.\n \
                    Database not updated.")

        elif  not os.path.isfile(query_file) and os.path.isfile(email_file):
            print ("You must specify both a query and email file that exist.\n \
                    Database not updated.")
        else:

            newquery=DataFrame({'id':1,'search_term':search_term, \
                'city':city,'area':area, \
                'minprice':minprice,'maxprice':maxprice, 'category':category, \
                'bedrooms':bedrooms,'pic':pic}, index = [0])

            newquery.to_csv(query_file, header=True, index=False)

            newemail=DataFrame({'query_id':1,'email':email}, index = [0])
            newemail.to_csv(email_file, header=True, index=False)

    def load_query_terms(self,query_file,header=True):
        '''
        load in query parameters and store as pandas dataframe

        Parameters
        ----------
        query_file : string
            -Matrix of query parameters
            -columns are ID, location and search term
        header : bool
            -assume that query_file has header for column

        '''
        if header:
            query_list=read_csv(query_file,na_filter = False)
        else:
            query_list=read_csv(query_file,na_filter = False,header=None)


        query_list.bedrooms = query_list['bedrooms'].apply(str)
        query_list.minprice = query_list['minprice'].apply(str)
        query_list.maxprice = query_list['maxprice'].apply(str)

        self.query_list = query_list

    def load_email_list(self,email_file,header=True):
        '''
        load in query parameters and store as pandas dataframe

        Parameters
        ----------
        email_file : string
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

        cl_info.to_csv(raw_search_history, mode = 'a',header=True, index=False,encoding = "utf-8")

        #################################
        #Add to unique search history
        #################################

        #if unique_search_history table exists,
        #read unique search history
        if os.path.isfile(unique_search_history):
            all_unique = read_csv(unique_search_history,encoding = "utf-8")
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
        if os.path.isfile(unique_search_history):
            unique_total = concat([unique,other_unique],axis=0)
        else:
            unique_total = unique
        unique_total.to_csv(unique_search_history,index=False,encoding = "utf-8")


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
            links = '<a href ="' + todays_results.url + '" target="_blank">'+ todays_results.date + ' - ' + todays_results.price + ' - ' + todays_results.title +  '</a> <br>'
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
        self.todays_results = todays_results

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

