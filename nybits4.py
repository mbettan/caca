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
    link = Column(String)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

def create_dbentry(name, website):
    # Create the listing object.
    listing = Listing(
        name=name,
        link=website
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

def parse_account(soup):
    account = {"name": '', "website": '', "street": '', "phone": '', "email": '', "appfee": '', "web": '', "listing": ''}

    for ultag in soup.find_all('ul', {'class': 'spacyul'}):
        for litag in ultag.find_all('li'):
            account['name'] = litag.find_all('a')[0].text
            account['website'] = litag.find_all('a')[0].get('href')
            resp2 = requests.get(account['website'])
            soup2 = BeautifulSoup(resp2.content, 'html.parser')
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
            test = account['name']
            listing = session.query(Listing).filter(Listing.name==test).first()
            if listing == None:
                create_dbentry(account['name'], account['website'])
    return (account)


with open('mgmt_office.csv', mode='w') as csv1:
    csv1_writer = csv.writer(csv1, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csv1_writer.writerow(['account', 'street', 'neighborhoods','phone', 'email', 'web', 'listing', 'application fee', 'website', 'type'])

resp = requests.get('https://www.nybits.com/managers/residential_property_managers.html')
if not resp.ok:
    print('error: {} {}'.format(resp.status_code, resp.text))
soup = BeautifulSoup(resp.content, 'html.parser')

account = parse_account(soup)

with open('mgmt_office.csv', mode='a') as csv1:
    csv1_writer = csv.writer(csv1, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csv1_writer.writerow([account['name'], account['street'], '',account['phone'], account['email'], account['web'], account['listing'], account['appfee'], account['website'], 'Management Company'])

#session.query(Listing).filter_by(cl_id=result["id"]).first()
#session.query(Listing)