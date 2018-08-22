import csv
import settings
import requests
from bs4 import BeautifulSoup
from scraper import GoogleMapsClient
import time
from datetime import datetime

with open('mgmt_office.csv', mode='w') as csv1:
 csv1_writer = csv.writer(csv1, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
 csv1_writer.writerow(['Account', 'street', 'phone', 'email', 'web', 'listing', 'application fee', 'website'])

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
   csv1_writer.writerow([account, street, phone, email, web, listing, appfee, website])
  street = ''
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
