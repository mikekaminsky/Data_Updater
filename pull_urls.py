######################
#Python Code to Pull URLs for a search term
#And organize database of past searches
#Started: 2013.11.24
#Last updated: 2013.12.11
#Michael Kaminsky
#######################


def cl_scraper(to_email,location,query,query_id):

             
    #The URL that returns the search results
    url = 'http://'+location+'.craigslist.org/search/sss?query='+query.replace(' ', '+')+'&zoomToPosting=&minAsk=&maxAsk=&sort=rel'


    #Initiate empty lists that will be filled in as the program iterates through the search 
    #results
    price_list = []
    date_list = []
    title_list = []
    url_list = []
    type_list = []

    ##############################################
    #Function to extract every available post from a craigslist search
    #Function is called while looping through search results
    ##############################################

    def extract_listings(rows):
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
         tester=0
         for terms in query.split():
             if terms.lower() in title_string.lower():
                 tester = 1
         if price is not None and tester == 1:
             #Append the price, date, title, type, and url to the list.
             price_list.append(unicode(price.contents[0]))
             date_list.append(unicode(date.contents[0]))
             title_list.append(unicode(title.contents[0]))
             type_list.append(unicode(type.contents[0]))
             url_list.append(location+'.craigslist.org'+url)
                     
    ####################################################
    #Loop through 10 pages, or until no 'next' button is found.
    ####################################################

    ploop = 0
    while ploop < 10:
     if ploop == 0:
         page = urllib2.urlopen(url)
     else:
         resultnum = str(ploop*100)
         next = 'http://'+location+'.craigslist.org/search/?s='+resultnum+'&areaID=3&catAbb=sss&query='+query.replace(' ', ',')+'&sort=rel'
         page = urllib2.urlopen(next)
     ploop = ploop+1
     soup = BeautifulSoup(page)
     rows = soup.find_all("p","row")
     #Here we extract the listings (defined above) for each page
     extract_listings(rows)
     next = soup.find(class_="button next")
     if 'href' not in str(next):
         ploop = 10      
           
    #Create dataframe by concatenating lists
    cl_info=DataFrame({'date':date_list,'title':title_list,'price':price_list, 'url':url_list,'type':type_list})
    cl_info['date_ran']=today
    cl_info['query_id']=query_id


    #################################
    #Add to raw history -- simply stacking all the results found with every search
    #################################

    cl_info.to_csv(raw_search_history, mode = 'a',header=False, index=False)

    #################################
    #Add to unique search history
    #################################

    #Read unique search history
    all_unique = read_csv(unique_search_history)
    #Append current results to unique history
    all_unique = all_unique.append(cl_info)



    all_unique['tempprice'] = all_unique.price.str.strip('$')
    all_unique['tempprice'] = all_unique.tempprice.str.replace(',','')
    all_unique['tempprice'] = all_unique.tempprice.str.strip()
    all_unique ['price_num'] = all_unique.tempprice.map(lambda x: x[0:]).astype('float')

    del all_unique ['tempprice']

    #Sort so that we take the oldest results when removing duplicates
    #May cause issues with URLs. May want to revisit sort order so newest
    #URLs are kept but oldest dates are kept.
    #How?
    sorted_unique=all_unique.sort(['query_id','title','price_num', 'date', 'date_ran'],ascending=False)



    #Remove duplicates by keys
    keys='query_id','title','price_num'
    unique=sorted_unique.drop_duplicates(cols=keys,take_last=True)

    del all_unique['price_num']
    #Write unique history back to CSV
    unique.to_csv(unique_search_history,index=False)

    #################################
    #Select ones where today = todays date
    #These should be unique instances where there was a new
    #post today.
    #################################

    #Subset to today's *new* results
    todays_results=unique[unique['date_ran'] == today]

    #Write today's new results to CSV
    todays_results.to_csv(new_results,index=False)

    #Now send the email updates
    execfile("send_email_updates.py")
