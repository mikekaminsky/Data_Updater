'''
This program uses the cl_updater and the cl_scraper modules
to send emails with updates about new craigslist postings.

'''

my_email = 'kaminsky.michael@gmail.com'
#passes = "C:/Users/Michael/Desktop/passwords.txt"
#fileHandle = open ( passes, 'r' )
#password = fileHandle.read()

import sys
sys.path.append('C:/Users/Michael/Documents/Code_Projects/Craigslist_Scraper')
sys.path.append('C:/Users/Michael/Documents/Code_Projects/Craigslist_Updater')

#import craigslist_scraper.cl_scraper as csc
from cl_scraper import cl_scraper
#from cl_updater import cl_updater
execfile("cl_updater.py")

data_path = '/Users/casebook/Mike_Projects/craigslist_updater/data/'
query_info = data_path + 'query_info.csv'
email_info = data_path + 'emails.csv'


#Initiate cu_object
cu_object = cl_updater()

'''
Add new lines to the query_info and emails file

'''

mike_and_jed = {"kaminsky.michael@gmail.com","john.e.dougherty@gmail.com"}

for jedormike in mike_and_jed:
    cu_object.add_new_query(query_file = query_info, 
        email_file = email_info,
        email = "kaminsky.michael@gmail.com", 
        search_term = "morgan", city = "newyork",
        area="brk", minprice="", 
        maxprice="6000", category="hhh", 
        pic=False, bedrooms="4")




'''
query_file = query_info 
email_file = email_info
email = "kaminsky.michael@gmail.com"
search_term = "morgan"
city = "newyork"
area="brk"
minprice="" 
maxprice="6000"
category="hhh"
pic=False
bedrooms="4"

'''


stop()

cu_object.load_query_terms(query_file=query_info)
print (cu_object.query_list)

cu_object.load_email_list(email_file = email_info)
print (cu_object.email_list)


''' For each row in the query_list table,
    1) execute the craigslist scraper
    2) update the database
    3) send emails to the relevant people
'''

for index, row in cu_object.query_list.iterrows():
     search_term = row['search_term']
     city = row['city']
     area = row['area']
     query_id = row['id']
     minprice = str(row['minprice'])
     maxprice = str(row['maxprice'])
     category = row['category']
     pic = row['pic']
     bedrooms = str(row['bedrooms'])


     #print query_id, location, query

     #Run craigslist scraper app to get results from query
     cs = cl_scraper(search_term = search_term,
                     city = city,
                     area = area,
                     minprice = minprice,
                     maxprice = maxprice,
                     category = category,
                     pic = pic,
                     bedrooms = bedrooms)

     cs.build_cl_url()
     cs.run_cl_query()
     cs.extract_listings(title_strict=False)

     #print cs.craigslist_results.head()

     #Update database with results from this query
     cu_object.update_database(data_path=data_path,query_id=query_id,cl_info=cs.craigslist_results)
     cu_object.build_emails(data_path = data_path,query = search_term, query_id = query_id)
     email_message = cu_object.email_message
     #print cu_object.email_message

     #Pull to-emails from the users table based on the query id
     to_emails = cu_object.email_list[cu_object.email_list .query_id == query_id]
     #Send email to
     for index2, row2 in to_emails.iterrows():
        to_email=row2['email']
        cu_object.send_emails(email_message = email_message ,from_email = my_email ,to_email = to_email ,password = password)

