'''
This program uses the cl_updater and the cl_scraper modules
to send emails with updates about new craigslist postings.

'''

my_email = 'kaminsky.michael@gmail.com'

import sys
sys.path.append('C:/Users/Michael/Documents/Code_Projects/Craigslist_Scraper')
sys.path.append('C:/Users/Michael/Documents/Code_Projects/Craigslist_Updater')

#import craigslist_scraper.cl_scraper as csc
from cl_scraper import cl_scraper
from cl_updater import cl_updater


data_path = 'C:/Users/Michael/Documents/Code_Projects/Craigslist_Updater/data/'
query_info = data_path + 'query_info.csv'
email_info = data_path + 'emails.csv'

cu_object = cl_updater()
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
     location = row['location']
     query = row['query']
     query_id = row['ID']
     #print query_id, location, query
     
     #Run craigslist scraper app to get results from query
     cs = cl_scraper(location=location,query=query)
     cs.run_cl_query()
     cs.extract_listings(title_strict=True)
     
     #print cs.craigslist_results.head()
     
     #Update database with results from this query
     cu_object.update_database(data_path=data_path,query_id=query_id,cl_info=cs.craigslist_results)
     cu_object.build_emails(data_path = data_path,query = query, query_id = query_id)
     email_message = cu_object.email_message
     #print cu_object.email_message

     #Pull to-emails from the users table based on the query id
     to_emails = cu_object.email_list[cu_object.email_list .query_id == query_id]
     #Send email to 
     for index2, row2 in to_emails.iterrows():
         to_email=row2['email']
         cu_object.send_emails(email_message = email_message ,from_email = my_email ,to_email = to_email ,password = )
     
     