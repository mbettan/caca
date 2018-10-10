import os
import csv
import time
import settings
import requests
from bs4 import BeautifulSoup
from scraper import GoogleMapsClient
import time
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean
from sqlalchemy.orm import sessionmaker
from google.cloud import datastore


client = datastore.Client()
query = client.query(kind='search')

def create_dbentry(task2, website):
    datastore_client = datastore.Client()
    kind = 'search'
    name = website
    task_key = datastore_client.key(kind, name)
    task = datastore.Entity(key=task_key)
    task['website'] = task2['website']
    task['price'] = task2['price']
    task['name'] = task2['name']
    task['description'] = task2['description']
    task['fee'] = task2['fee']
    task['source'] = task2['source']
    datastore_client.put(task)

def requests_get(*args, **kwargs):
    """
    Retries if a RequestException is raised (could be a connection error or
    a timeout).
    """

    logger = kwargs.pop('logger', None)
    try:
        return requests.get(*args, **kwargs)
    except RequestException as exc:
        if logger:
            logger.warning('Request failed (%s). Retrying ...', exc)
        return requests.get(*args, **kwargs)

def slack_post(task):
    r = requests.post('https://hooks.slack.com/services/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',
     json={
           "text": "*New Listing* - " + task['description'],
           "attachments": [
            {
#             "title": task['description'],
             "color": "#FF0000",
             "fields":[  
              {  
                "title":"Source",
                "value":task['source'],
                "short":"true"
              },
              {  
                "title":"Fee",
                "value":task['fee'],
                "short":"true"
              },
              {
                "title":"Price",
                "value":task['price'],
                "short":"true"
              },
              {
                "title":"Size",
                "value":"2 Bedrooms",
                "short":"true"
              },
              {  
                "title":"Website",
                "value":task['website'],
                "short":"false"
              }
                       ] 
         }
                          ]
          })
    if not r.ok:
        print('error: {} {}'.format(r.status_code, r.text))


def item_exist (website):
	query = client.query(kind='search')
	query.add_filter('website', '=', website)
	building = list(query.fetch())
	return (len(building) >= 1)

def parse_nybits(website):
   soup = get_page(website)
   if '403 Forbidden' in soup.text:
     print ('403 Forbidden')
     return (None)
   task = {"name": '', "website": '', "street": '', "source": '', "email": '', "fee": '', "website": '', "listing": '', "description": '', "price": ''}
   for ultag in soup.find_all('div', {'class': 'sr_envelope'}):
     task['price'] = ultag.find_all('div')[0].text.replace("\n", "")
     apt = ultag.find_all('div')[1].find_all('a')[0]
     task['name'] = apt.text.replace("\n", "")
     task['website'] = apt.get('href')
     task['fee'] = ultag.find_all('div')[1].find_all('span')[0].text.replace("\n", "")
     task['description'] = ultag.find_all('div')[1].find_all('span')[1].text.replace(" - ", "")
     task['source'] = 'nybits'
     query = client.query(kind='search')
     query.add_filter('website', '=', task['website'])
     dblist = list(query.fetch())
     if (len(dblist) == 0):
      create_dbentry(task, task['website'])
      slack_post(task)

def parse_nestio(website):
   soup = get_page(website)
   if '403 Forbidden' in soup.text:
     print ('403 Forbidden')
     return (None)
   task = {"name": '', "website": '', "street": '', "source": '', "email": '', "fee": '', "website": '', "listing": '', "description": '', "price": ''}
   print(soup.text)
   for ultag in soup.find_all('div', {'class': 'sr_envelope'}):
     task['price'] = ultag.find_all('div')[0].text.replace("\n", "")
     apt = ultag.find_all('div')[1].find_all('a')[0]
     task['name'] = apt.text.replace("\n", "")
     task['website'] = apt.get('href')
     task['fee'] = ultag.find_all('div')[1].find_all('span')[0].text.replace("\n", "")
     task['description'] = ultag.find_all('div')[1].find_all('span')[1].text.replace(" - ", "")
     task['source'] = 'nybits'
     query = client.query(kind='search')
     query.add_filter('website', '=', task['website'])
     dblist = list(query.fetch())
     if (len(dblist) == 0):
      create_dbentry(task, task['website'])
      slack_post(task)

def parse_craigslist(website):
   soup = get_page(website)
   if '403 Forbidden' in soup.text:
     print ('403 Forbidden')
     return (None)
   task = {"name": '', "website": '', "street": '', "source": '', "email": '', "fee": '', "website": '', "listing": '', "description": '', "price": ''}
   for ultag in soup.find_all('li', {'class': 'result-row'}):
     result_title = ultag.find_all('a', {'class': 'result-title'})
     task['name'] = result_title[0].text
     task['description'] = result_title[0].text
     task['website'] = result_title[0].get('href')
     task['price'] = ultag.find_all('span', {'class': 'result-price'})[0].text
     task['fee'] = 'no fee'
     task['source'] = 'craigslist'
     query = client.query(kind='search')
     query.add_filter('website', '=', task['website'])
     dblist = list(query.fetch())
     if (len(dblist) == 0):
      query = client.query(kind='search')
      query.add_filter('description', '=', task['description'])
      dblist = list(query.fetch())
#      print (dblist)
      if (len(dblist) == 0):
       create_dbentry(task, task['website'])


def parse_streeteasy(website):
   with open("/root/parking/apartment-finder-master/streeteasy.html", encoding="utf8", errors='ignore') as f:
     resp = f.read()
   soup = BeautifulSoup(resp, 'html.parser')
   soup = get_page("https://s3.eu-west-3.amazonaws.com/hcm-geneva/newfile.html")
   if '403 Forbidden' in soup.text:
     print ('403 Forbidden')
     return (None)
 
   task = {"name": '', "website": '', "street": '', "source": '', "email": '', "fee": '', "website": '', "listing": '', "description": '', "price": ''}
   [s.extract() for s in soup('div', {'class': 'item_tools'})]
   for ultag in soup.find_all('div', {'class': 'details row'}):
#     print(ultag)
     result_title = ultag.find_all('h3', {'class': 'details-title'})
#     result_title2 = ultag.find('div', id="item_tools").decompose()
#     print(result_title2)
#     exit()
     task['name'] = result_title[0].text.replace("\n","")
     task['description'] = result_title[0].text.replace("\n","")
     task['street'] = result_title[0].text.replace("\n","")
     task['website'] = ("https://streeteasy.com" + ultag.find_all('a')[0].get('href'))
     task['price'] = ultag.find_all('li', {'class': 'price-info'})[0].find_all('span', {'class': 'price'})[0].text
     task['fee'] = 'no fee'
     task['source'] = 'streeteasy'
     query = client.query(kind='search')
     query.add_filter('website', '=', task['website'])
     dblist = list(query.fetch())
     if (len(dblist) == 0):
      query = client.query(kind='search')
      query.add_filter('description', '=', task['description'])
      dblist = list(query.fetch())
#      print (dblist)
      if (len(dblist) == 0):
       create_dbentry(task, task['website'])

def get_page (website):
	hdr = {'User-Agent':'Mozilla/5.0'}
	headers = requests.utils.default_headers()
	headers.update({
		'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0',
	})
	headers.update({
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
	})
	resp = requests.get(website,headers=headers)
	if (resp.status_code != 200):
		os.system("/etc/init.d/apache2 stop")
		time.sleep(360)
		resp = requests.get(website)
	if not resp.ok:
    		print('error: {} {}'.format(resp.status_code, resp.text))
	soup = BeautifulSoup(resp.content, 'html.parser')
	return (soup)

def write_csv ():
	with open('mgmt_office.csv', mode='w') as csv1:
		csv1_writer = csv.writer(csv1, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		csv1_writer.writerow(['name', 'website', 'street', 'phone', 'email', 'appfee', 'web', 'listing', 'typed', 'neighborhoods'])
	client = datastore.Client()
	query = client.query(kind='buildings')
	listing = list(query.fetch())
	for item in listing:
		csv1_writer.writerow(["test", item['website'], item['street'], item['phone'], item['email'], item['appfee'], item['web'], item['listing'], item['typed'], item['neighborhoods']])

def nestio_auth(website):
	client = requests.session()

	client.get(website)

	if 'csrftoken' in client.cookies:
		csrftoken = client.cookies['csrftoken']
	else:
    		csrftoken = client.cookies['csrf']


	login_data = dict(username="xxxx", password="xxx", csrfmiddlewaretoken=csrftoken, next='/')
	r = client.post(website, data=login_data, headers=dict(Referer=website))
	soup = BeautifulSoup(r.content, 'html.parser')
	#print (soup)
	#exit()
	headers = requests.utils.default_headers()
	headers.update({
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
	})
	r = client.get("https://nestiolistings.com/",headers=headers)
	soup = BeautifulSoup(r.content, 'html.parser')
	print (r)


parse_streeteasy("pipo")
exit()
nestio_auth("https://nestiolistings.com/login/")
#parse_nestio("https://nestiolistings.com/listings/?listing_type=10&n=128&layout_specific=30&min_price=3000&max_price=5250")
exit ()

parse_nybits("https://www.nybits.com/search/?_rid_=15&_ust_todo_=65733&_xid_=q9JUSTTsnf9iUY-1538940046&_a%21process=y&%21%21atypes=2br&%21%21rmin=4250&%21%21rmax=5000&doorman=on&elevator=on&%21%21fee=nofee&%21%21orderby=dateposted&%21%21nsearch=upper_west_side&submit=+SEARCH+RENTAL+APARTMENTS+")

parse_craigslist("https://newyork.craigslist.org/search/mnh/nfa?nh=138&min_price=4000&max_price=5200&min_bedrooms=2&availabilityMode=0&sale_date=all+dates")
exit ()


os.system("/etc/init.d/apache2 stop")

