import settings
import requests
from bs4 import BeautifulSoup
from scraper import GoogleMapsClient
import time
from datetime import datetime


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


settings.GOOGLEMAPS_KEY = 'AIzaSyAg5jHqxNK3gvFR-eBC_aAFu_W-uTnfiFc'
gmap = GoogleMapsClient()

aptgeo = gmap.client.geocode('216 Jersey St, San Francisco, CA 94114')
loc = aptgeo[0]['geometry']['location']
aptloc = (loc['lat'], loc['lng'])

already_seen = {}

while True:
    print(datetime.now())
    resp = requests.get('https://sfbay.craigslist.org/search/sfc/prk?sort=date&nh=21&availabilityMode=0')
    if not resp.ok:
        print('error: {} {}'.format(resp.status_code, resp.text))
    soup = BeautifulSoup(resp.content, 'html.parser')

    # %%
    entries = []
    for result in soup.find_all('p', {'class': 'result-info'}):
        entry = {}
        t = result.find('a', {'class': 'result-title'})
        if t:
            entry['title'] = t.text
            entry['url'] = t.attrs['href']

        t = result.find('span', {'class': 'result-price'})
        if t:
            entry['price'] = t.text

        t = result.find('span', {'class': 'result-hood'})
        if t:
            entry['neighborhood'] = t.text

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

    filtered_entries = []
    for e in entries:
        url = e.get('url', '')
        if url in already_seen:
            continue
        already_seen[url] = True

        loc = e['geotag']
        dist = gmap.min_walking_dist(loc, [aptloc])
        if dist['duration']['value'] > 10 * 60:  # filter any > 10m walk away
            continue

        e['dist'] = gmap.pretty(dist)
        # filtered_entries.append(e)
        print(e)
        slack_post(e)

    time.sleep(10 * 60)  # 10m
