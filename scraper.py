from mycraigslist import CraigslistParking
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean
from sqlalchemy.orm import sessionmaker
from dateutil.parser import parse
from util import post_listing_to_slack, find_points_of_interest
from slackclient import SlackClient
import time
import settings
import googlemaps
import os

engine = create_engine('sqlite:///listings.db', echo=False)

Base = declarative_base()

class Listing(Base):
    """
    A table to store data on craigslist listings.
    """

    __tablename__ = 'listings'

    id = Column(Integer, primary_key=True)
    link = Column(String, unique=True)
    created = Column(DateTime)
    geotag = Column(String)
    lat = Column(Float)
    lon = Column(Float)
    name = Column(String)
    price = Column(Float)
    location = Column(String)
    cl_id = Column(Integer, unique=True)
    area = Column(String)
    bart_stop = Column(String)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

class GoogleMapsClient:
    def __init__(self):
        self.client = googlemaps.Client(key=settings.GOOGLEMAPS_KEY)
    
    def min_walking_dist(self, loc, dests):
        ds = self.client.distance_matrix(loc, destinations=dests, mode='walking')
        d = min(ds['rows'][0]['elements'], key=lambda e: e['duration']['value'])
        #return "{}/{}".format(d['distance']['text'], d['duration']['text'])
        return d

    def pretty(self, d):
        return "{}/{}".format(d['distance']['text'], d['duration']['text'])


def scrape_area(area):
    """
    Scrapes craigslist for a certain geographic area, and finds the latest listings.
    :param area:
    :return: A list of results.
    """
    # filters = {'max_price': settings.MAX_PRICE, 'min_price': settings.MIN_PRICE}
    # if settings.MIN_BEDROOMS:
    #     print('filtering by bedrooms:', settings.MIN_BEDROOMS)
    #     filters['bedrooms'] = settings.MIN_BEDROOMS
    # if settings.NEIGHBORHOOD_CODE:
    #     print('filtering by neighborhood:', settings.NEIGHBORHOOD_CODE)
    #     filters['neighborhood_code'] = settings.NEIGHBORHOOD_CODE
    filters = {'nh': 21}

    cl_h = CraigslistParking(
        site=settings.CRAIGSLIST_SITE,
        area=area,
        # category=settings.CRAIGSLIST_HOUSING_SECTION,
        category='prk',
        filters=filters)
    
    gmap = GoogleMapsClient()
    
    results = []
    gen = cl_h.get_results(sort_by='newest', geotagged=True, limit=50)
    while True:
        try:
            result = next(gen)
        except StopIteration:
            break
        except Exception:
            continue
        listing = session.query(Listing).filter_by(cl_id=result["id"]).first()

        # Don't store the listing if it already exists.
        if listing is None:
            if result["where"] is None:
                # If there is no string identifying which neighborhood the result is from, skip it.
                continue
                        
            lat = 0
            lon = 0
            if result["geotag"] is not None:
                # Assign the coordinates.
                lat = result["geotag"][0]
                lon = result["geotag"][1]

                # Annotate the result with information about the area it's in and points of interest near it.
                geo_data = find_points_of_interest(result["geotag"], result["where"])
                result.update(geo_data)
                
                # Find walking distances
                loc = {'lat': result["geotag"][0], 'lng': result["geotag"][1]}
                shuttle_min = gmap.min_walking_dist(loc, settings.SHUTTLE_STOPS)
                if shuttle_min['duration']['value'] > settings.MAX_WALKING_TIME:
                    continue
                business_min = gmap.min_walking_dist(loc, settings.BUSINESSES)
                result["bart_dist"] = 'apple: {}, business: {}'.format(
                    gmap.pretty(shuttle_min),
                    gmap.pretty(business_min))
                
            else:
                result["area"] = ""
                result["bart"] = ""
                        
            # Try parsing the price.
            price = 0
            try:
                price = float(result["price"].replace("$", ""))
            except Exception:
                pass

            # Create the listing object.
            listing = Listing(
                link=result["url"],
                created=parse(result["datetime"]),
                lat=lat,
                lon=lon,
                name=result["name"],
                price=price,
                location=result["where"],
                cl_id=result["id"],
                area=result["area"],
                bart_stop=result["bart"]
            )

            # Save the listing so we don't grab it again.
            session.add(listing)
            session.commit()

            # Return the result if it's near a bart station, or if it is in an area we defined.
            if len(result["bart"]) > 0 or len(result["area"]) > 0:
                results.append(result)

    return results

def do_scrape():
    """
    Runs the craigslist scraper, and posts data to slack.
    """

    # Create a slack client.
    sc = SlackClient(settings.SLACK_TOKEN)

    # Get all the results from craigslist.
    all_results = []
    for area in settings.AREAS:
        all_results += scrape_area(area)

    print("{}: Got {} results".format(time.ctime(), len(all_results)))

    # Post each result to slack.
    for result in all_results:
        post_listing_to_slack(sc, result)
