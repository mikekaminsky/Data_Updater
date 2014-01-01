
import craigslist_scraper.cl_scrapper_class as csc

data_path = '/Users/casebook/Mike_Projects/craigslist_scraper/data/'

query_info = data_path + "query_info.csv"

cs = csc.cl_scraper()
cs.load_query_terms(query_info)

query_id = cs.query_list.ix[0,'ID']
query = cs.query_list.ix[0,'query']
location = cs.query_list.ix[0,'location']


cs.run_cl_query(location=location,query=query)
cs.extract_listings(rows=cs.rows,query=query,location=location,title_strict=True)

#Show all results from this query
print cs.cl_info
