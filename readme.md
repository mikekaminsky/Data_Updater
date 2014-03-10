Craigslist Updater
===================================

This is a repository for the Craigslist Updater app.

This app utilizes the [Craigslist Scraper](https://github.com/mikekaminsky/craigslist_scraper) app to:

1. Pull all results from Craigslist from a given location with a given query,
2. Determine which posts are 'new',
3. Save the results in a database, and
4. Deliver emails to recipients containing the new postings.


How to Use
-----------------------------------
1. Download the [Craigslist Scraper](https://github.com/mikekaminsky/craigslist_scraper)
2. Download the [Craigslist Updater](https://github.com/mikekaminsky/craigslist_updater)
3. Initiate your database as shown below:

    ```
    from cl_scraper import cl_scraper

    cu_object = cl_updater()


    cu_object.add_new_query("path/to/query/file.csv", "path/to/email/file.csv",test@test.com, 
                            "whozits", newyork, area="", minprice="", maxprice="", category="sss", 
                            pic=False, bedrooms="")
    ```


4. Execute the scraper and updater for every line in the query database.


    ```

    cu_object.load_query_terms(query_file=query_info)
    cu_object.load_email_list(email_file = email_info)

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

         #Update database with results from this query
         cu_object.update_database(data_path=data_path,query_id=query_id,cl_info=cs.craigslist_results)
         cu_object.build_emails(data_path = data_path,query = search_term, query_id = query_id)
         email_message = cu_object.email_message

         #Pull to-emails from the users table based on the query id
         to_emails = cu_object.email_list[cu_object.email_list .query_id == query_id]
         #Send email to
         for index2, row2 in to_emails.iterrows():
            to_email=row2['email']
            cu_object.send_emails(email_message = email_message ,from_email = my_email ,to_email = to_email ,password = password)
    ```
