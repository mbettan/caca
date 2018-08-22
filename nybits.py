import settings
import requests
from bs4 import BeautifulSoup
from scraper import GoogleMapsClient
import time
from datetime import datetime

resp = requests.get('https://www.nybits.com/managers/residential_property_managers.html')
if not resp.ok:
	print('error: {} {}'.format(resp.status_code, resp.text))
soup = BeautifulSoup(resp.content, 'html.parser')

for link in soup.find_all('a'):
    weblink = link.get('href')
    if "http" in weblink:
     resp2 = requests.get(weblink)
    if "managers" in weblink:    
     soup2 = BeautifulSoup(resp2.content, 'html.parser')    
     print (soup2.title)
     for link2 in soup2.find_all('a'):
      print (link2)
     exit (0)
entries = []
for result in soup.find_all('u1', {'class': 'spacyul'}):
        entry = {}
        print ('ici')
        t = result.find('li', {'class': 'standardli'})
        print (result)
        if t:
            entry['title'] = t.text
            entry['url'] = t.attrs['href']

        if 'url' in entry and len(entry['url']) > 0:
            resp = requests.get(entry['url'])
            if resp.ok:
                soup = BeautifulSoup(resp.content, 'html.parser')
                body = soup.find(id='postingbody')
                if body:
                    entry['body'] = body.text

                m = soup.find('div', {'id': 'map'})
                if m:
                    lat, lon = float(m.attrs['data-latitude']), float(m.attrs['data-longitude'])
                    entry['geotag'] = (lat, lon)

        entries.append(entry)

print('found {} entries'.format(len(entries)))

