import csv
import time
import settings
import requests
from bs4 import BeautifulSoup
from scraper import GoogleMapsClient
import time
from datetime import datetime

street2 = ''
phone2 = ''
email2 = ''
appfee2 = ''
web2 = ''
listing2 = ''
steret = ''
phone = ''
email = ''
appfee = ''
web = ''
listing = ''
neighborhoods = ''

with open('mgmt_office.csv', mode='w') as csv1:
 csv1_writer = csv.writer(csv1, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
 csv1_writer.writerow(['account', 'street', 'neighborhoods','phone', 'email', 'web', 'listing', 'application fee', 'website', 'type'])

resp = requests.get('https://www.nybits.com/managers/residential_property_managers.html')
if not resp.ok:
	print('error: {} {}'.format(resp.status_code, resp.text))
soup = BeautifulSoup(resp.content, 'html.parser')


for ultag in soup.find_all('ul', {'class': 'spacyul'}):
 for litag in ultag.find_all('li'):
  account = litag.find_all('a')[0].text
  website = litag.find_all('a')[0].get('href') 
  resp2 = requests.get(website)
  soup2 = BeautifulSoup(resp2.content, 'html.parser')
  table = soup2.find('table', id="summarytable")
  rows = table.findAll('tr')  
  for row in table.findAll('tr'):
   if "Address" in row.text:
    street = row.findAll('td')[1].text
   if "Phone" in row.text:
    phone = row.findAll('td')[1].text
   if "Email" in row.text:
    email = row.findAll('td')[1].text
   if "Application Fee" in row.text:
    appfee = row.findAll('td')[1].text
   if "Web" in row.text:
    web = row.findAll('td')[1].text
   if "Listing" in row.text:
    listing = row.findAll('td')[1].text

  with open('mgmt_office.csv', mode='a') as csv1:
   csv1_writer = csv.writer(csv1, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
   csv1_writer.writerow([account, street, '',phone, email, web, listing, appfee, website, 'Management Company'])

  for ultag2 in soup2.find_all('ul', {'class': 'spacyul'}):
   for litag2 in ultag2.find_all('li'):
    account2 = litag2.find_all('a')[0].text
    website2 = litag2.find_all('a')[0].get('href')
    print('website='+website2)
    time.sleep(1) 
    resp3 = requests.get(website2)
    soup3 = BeautifulSoup(resp3.content, 'html.parser')
    table2 = soup3.find('table', id="summarytable")
#    print (soup3)
    if table2 is None:
      print (website2)
      continue
    rows2 = table2.findAll('tr')

    for row2 in table2.findAll('tr'):
     if "Address" in row2.text:
      street2 = row2.findAll('td')[1]
      for e in street2.findAll('br'):
       e.extract()
      street2 = [item.strip() for item in street2 if str(item)]
      street2final = street2[0].replace(',','')
      code = street2[1]
     if "Phone" in row2.text:
      phone2 = row2.findAll('td')[1].text.strip()
     if "Email" in row2.text:
      email2 = row2.findAll('td')[1].text.strip()
     if "Application Fee" in row2.text:
      appfee2 = row2.findAll('td')[1].text.strip()
     if "Web" in row2.text:
      web2 = row2.findAll('td')[1].text.strip()
     if "Listing" in row2.text:
      listing2 = row2.findAll('td')[1].text.strip()
     if "Neighborhoods" in row2.text:
      neighborhoods = row2.findAll('td')[1].text.split(',',1)[0]
    
    with open('mgmt_office.csv', mode='a') as csv1:
     csv1_writer = csv.writer(csv1, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
     csv1_writer.writerow([account2, street2final, neighborhoods.rstrip(), phone2, email2, web2, listing2, appfee2, website2, 'Building'])

    street2 = ''
    phone2 = ''
    email2 = ''
    appfee2 = ''
    web2 = ''
    listing2 = ''
 
  steret = ''
  phone = ''
  email = ''
  appfee = ''
  web = ''
  listing = ''

exit (0)
for link in soup.find_all('a'):
    weblink = link.get('href')
    if "http" in weblink:
     resp2 = requests.get(weblink)
    if "managers" in weblink:    
     soup2 = BeautifulSoup(resp2.content, 'html.parser')    
     print (soup2.title)
     for link2 in soup2.find_all('a'):
      print (link2)
