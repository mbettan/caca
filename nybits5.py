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

engine = create_engine('sqlite:///accounts.db', echo=False)
Base = declarative_base()

class Listing(Base):
    """
    A table to store data on craigslist listings.
    """

    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    website = Column(String)
    street = Column(String)
    phone = Column(String)
    email = Column(String)
    appfee = Column(String)
    web = Column(String)
    listing = Column(String)
    typed = Column(String)
    neighborhoods = Column(String)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

def create_dbentry(account):
    print ('new entry ='+ account['typed'])
    # Create the listing object.
    listing = Listing(
        name=account['name'],
        website=account['website'],
        street=account['street'],
        phone=account['phone'],
        email=account['email'],
        appfee=account['appfee'],
        web=account['web'],
        listing=account['listing'],
        typed=account['typed'],
        neighborhoods=account['neighborhoods']
    )

    # Save the listing so we don't grab it again.
    session.add(listing)
    session.commit()


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

def slack_post(e):
    r = requests.post('https://hooks.slack.com/services/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',
                      json={
                          'username': 'Parking Bot',
                          'icon_emoji': ':car:',
                          'attachments': [{
                              'title': e['title'],
                              'title_link': e['url'],
                              'text': e['body'],
                              'fields': [
                                  {'title': 'Price', 'value': e['price'], 'short': True},
                                  {'title': 'Distance', 'value': e['dist'], 'short': True}
                              ]
                          }]
                      })
    if not r.ok:
        print('error: {} {}'.format(r.status_code, r.text))

def item_exist (website):
	listing = session.query(Listing).filter(Listing.website==website).first()
	if (listing == None):
		print ('no website')
		return (False)
	return (listing.website != None)

def parse_account(website, typed):
   #if (item_exist (website)):
   #     print ('exist in db')
   #     return (None)

   soup = get_page(website) 
   if '403 Forbidden' in soup.text:
     print ('403 Forbidden')   
     return (None)
   for ultag in soup.find_all('ul', {'class': 'spacyul'}):
        for litag in ultag.find_all('li'):
            account = {"name": '', "website": '', "street": '', "phone": '', "email": '', "appfee": '', "web": '', "listing": '', "typed": '', "neighborhoods": ''}
            account['name'] = litag.find_all('a')[0].text
            account['website'] = litag.find_all('a')[0].get('href')
            #soup2 = get_page(account['website'])
            if (item_exist (account['website'])):
                print ('Skip following website=' + account['website'])
                continue
            if not ('https://www.nybits.com/apartments' in account['website']):
                print ('Skip following website=' + account['website'])
                continue
            soup2 = get_page(account['website'])
            print ('Processing following website=' + account['website'])
            table = soup2.find('table', id="summarytable")
            rows = table.findAll('tr')
            for row in table.findAll('tr'):
                if "Address" in row.text:
                    account['street'] = row.findAll('td')[1].text
                if "Phone" in row.text:
                    account['phone'] = row.findAll('td')[1].text
                if "Email" in row.text:
                    account['email'] = row.findAll('td')[1].text
                if "Application Fee" in row.text:
                    account['appfee'] = row.findAll('td')[1].text
                if "Web" in row.text:
                    account['web'] = row.findAll('td')[1].text
                if "Listing" in row.text:
                    account['listing'] = row.findAll('td')[1].text
                account['typed'] = typed
            test = account['name']
            listing = session.query(Listing).filter(Listing.name==test).first()
            if listing == None:
                create_dbentry(account)
   return (account)

def parse_building(session):
	listing = session.query(Listing).filter(Listing.typed=='Management Company')
	if listing == None:
		print ('No Management Company in the database.')
	else:
		for item in listing:
			print ('mgmt='+item.website)
			parse_account(item.website, 'Building')

def get_page (website):
	hdr = {'User-Agent':'Mozilla/5.0'}
	resp = requests.get(website,headers={'user-agent': 'Mozilla/5.0'})
	if (resp.status_code != 200):
		time.sleep(360)
		resp = requests.get(website)
	if not resp.ok:
    		print('error: {} {}'.format(resp.status_code, resp.text))
	soup = BeautifulSoup(resp.content, 'html.parser')
	return (soup)

def write_csv (session):
	with open('mgmt_office.csv', mode='w') as csv1:
         csv1_writer = csv.writer(csv1, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
         csv1_writer.writerow(['name', 'website', 'street', 'phone', 'email', 'appfee', 'web', 'listing', 'typed', 'neighborhoods'])
         listing = session.query(Listing)
         for item in listing:
          csv1_writer.writerow([item.name, item.website, item.street, item.phone, item.email, item.appfee, item.web, item.listing, item.typed, item.neighborhoods])
	


#with open('mgmt_office.csv', mode='w') as csv1:
#    csv1_writer = csv.writer(csv1, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
#    csv1_writer.writerow(['account', 'street', 'neighborhoods','phone', 'email', 'web', 'listing', 'application fee', 'website', 'type'])

#soup = get_page('https://www.nybits.com/managers/residential_property_managers.html')
#parse_account('https://www.nybits.com/managers/residential_property_managers.html', 'Management Company')
#parse_building(session)
#with open('mgmt_office.csv', mode='a') as csv1:
#    csv1_writer = csv.writer(csv1, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
#    csv1_writer.writerow([account['name'], account['street'], '',account['phone'], account['email'], account['web'], account['listing'], account['appfee'], account['website'], 'Management Company'])

write_csv(session)

