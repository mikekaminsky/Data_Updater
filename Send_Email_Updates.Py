#######################
#Python Code to Send Email Updates
#After pull_urls.py is run
#Started: 2013.12.09
#Last updated: 2013.12.11
#Michael Kaminsky
#######################


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# me == my email address
me = "kaminsky.michael@gmail.com"
# you == recipient's email address
you=to_email

#Get passwords
#password = getpass.getpass()
fileHandle = open ( passes, 'r' )
password = fileHandle.read()

# Create message container - the correct MIME type is multipart/alternative.
msg = MIMEMultipart('alternative')
msg['Subject'] = "New Craigslist Postings!"
msg['From'] = me
msg['To'] = you


#Read in CSV with new links to send in email
new_results = read_csv(new_results)
new_results = new_results[new_results['query_id'] == query_id]
#new_results ['price_num'] = new_results.price.map(lambda x: x[1:]).astype('float')
new_results = new_results.sort(['date','price_num'], ascending=[0,1])

#Conve to HTML Links
links = '<a href ="' + new_results.url + '">'+ new_results.date + ' - ' + new_results.price + ' - ' + new_results.title +  '</a> <br>'
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

# Record the MIME types of both parts - text/plain and text/html.
part1 = MIMEText(html, 'html')

# Attach parts into message container.
# According to RFC 2046, the last part of a multipart message, in this case
# the HTML message, is best and preferred.
msg.attach(part1)

# Send the message via local SMTP server.
s = smtplib.SMTP('smtp.gmail.com:587')
s.starttls()  
s.login(me,password) 
# sendmail function takes 3 arguments: sender's address, recipient's address
# and message to send - here it is sent as one string.
s.sendmail(me, you, msg.as_string())
s.quit()




