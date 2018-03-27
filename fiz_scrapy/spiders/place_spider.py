import json
import scrapy

from enum import Enum
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher

from fiz_scrapy import settings
from fiz_scrapy.providers._yelp import YelpMain
from fiz_scrapy.providers._google import Google
from fiz_scrapy.providers.eventful import Eventful
from fiz_scrapy.providers._flickr import FlickrMain
from fiz_scrapy.providers.wikipedia import Wikipedia
from fiz_scrapy.providers.panoramio import Panoramio
from fiz_scrapy.providers._facebook import FacebookMain
from fiz_scrapy.providers._foursquare import FoursquareMain

from fiz_scrapy.producer import Publisher


class PlaceSpider(scrapy.Spider):
    name = "place"
    start_urls = ['http://www.fiz.com/']
    PROVIDERS = [
        'google',
        'facebook',
        'foursquare',
        'yelp',
        'wikipedia',
        'eventful',
        'flickr'
    ]
    MAX_NEARBY_DISTANCE = 40000

    def __init__(self, lat=None, lon=None, radius=None, job_id=None, job_type=None, shub_id=None, index=1,  *args, **kwargs):
        super(PlaceSpider, self).__init__(*args, **kwargs)
        # dispatcher.connect(self.spider_closed, signals.spider_closed)
        self.final_data = []
        self.result_place_details = []
        self.action = None

        self.lat = float(lat)
        self.lon = float(lon)
        self.radius = float(radius)
        self.job_id = int(job_id)
        self.shub_id = int(shub_id)
        self.job_type = job_type

        # Places
        # self.lat = float(52.09153)
        # self.lon = float(1.31714)
        # self.job_id = 58
        # self.shub_id = 234
        # self.job_type = 'populate'
        # self.radius = float(100)

        self.p = Publisher(self.shub_id, request_type=self.job_type,
                           job_id=self.job_id, index=int(index))

    def parse(self, data):
        """
        :param data:
        :return:
        This function pass locational parameters to Place class for fetching place id's from different providers.
        """
        params = {
            'lat': self.lat,
            'lon': self.lon,
            'radius': self.radius,
            'provider': [provider for provider in self.PROVIDERS],
            'categories': None,
            'offset': None
        }

        data = json.dumps(params)
        self.get_place_details(data, ProviderActions.get_places)

    def get_place_details(self, data, action):
        """
            Returns a list of places' information, given geographic coordinates
            and a radius, from the specified third party providers.

            Body parameters:
            * __lat__ (number): Latitude of the center of coordinates.
            * __lon__ (number): Longitude of the center of coordinates.
            * __radius__ (number): Radius, in meters, of the center of coordinates where to look for places.
            * __providers__ (JSON): Object that indicates the providers to be used, and
                                for each one, a list of the categories to use as filters.
                * __providerName1__ (JSON): Object indicating to use the provider providerName1
                                       along with the categories specified within the object.
                * __providerName2__ (JSON): ...

            ---
        """
        params = json.loads(data)

        # Fetch Eventful place details
        eventful_extra_data_obj = {}
        eventful_extra_data_obj['app_key'] = settings.MP_EVENTFULL_APP_KEY
        eventful_extra_data_obj['base_url'] = settings.MP_EVENTFULL_BASE_URL
        try:
            if eventful_extra_data_obj:
                eventful = Eventful()
                eventful.pre_run(action, eventful_extra_data_obj)
                eventful_data = eventful.places(params)
                self.p.push_list(eventful_data)
                # [ for x in [eventful_data[i:i+size] for i in range(0, len(eventful_data), size)]]
        except: pass

        # Fetch Google place details
        google_extra_data_obj = {}
        google_extra_data_obj['key'] = settings.MP_GOOGLE_TOKEN
        try:
            if google_extra_data_obj:
                google = Google()
                google.pre_run(action, google_extra_data_obj)
                google_data = google.places(params)
                self.p.push_list(google_data)
        except :pass

        # Fetch Facebook place details
        facebook_extra_data_obj = {}
        facebook_extra_data_obj['app_id'] = settings.MP_FACEBOOK_APP_ID
        facebook_extra_data_obj['app_secret'] = settings.MP_FACEBOOK_APP_SECRET
        try:
            if facebook_extra_data_obj:
                facebook = FacebookMain()
                facebook.pre_run(action, facebook_extra_data_obj)
                facebook_data = facebook.places(params)
                self.p.push_list(facebook_data)
        except:pass

        # Fetch Yelp place details
        yelp_extra_data_obj = {}
        yelp_extra_data_obj['app_id'] = settings.MP_YELP_APP_ID
        yelp_extra_data_obj['app_secret'] = settings.MP_YELP_APP_SECRET
        yelp_extra_data_obj['access_token'] = settings.MP_YELP_ACCESS_TOKEN

        yelp_extra_data_obj['consumer_key'] = settings.MP_YELP_CONSUMER_KEY
        yelp_extra_data_obj['consumer_secret'] = settings.MP_YELP_CONSUMER_SECRET
        yelp_extra_data_obj['access_token_key'] = settings.MP_YELP_TOKEN
        yelp_extra_data_obj['access_token_secret'] = settings.MP_YELP_TOKEN_SECRET
        try:
            if yelp_extra_data_obj:
                yelp = YelpMain()
                yelp.pre_run(action, yelp_extra_data_obj)
                yelp_data = yelp.places(params)
                self.p.push_list(yelp_data)
        except:pass

        # Fetch Wikipedia place details
        wikipedia_extra_data_obj = {}
        wikipedia_extra_data_obj['base_url'] = settings.MP_WIKIPEDIA_BASE_URL
        try:
            if wikipedia_extra_data_obj:
                wikipedia = Wikipedia()
                wikipedia.pre_run(action, wikipedia_extra_data_obj)
                wikipedia_data = wikipedia.places(params)
                self.p.push_list(wikipedia_data)
        except:pass

        # Fetch Panoramio place details
        panoramio_extra_data_obj = {}
        panoramio_extra_data_obj['base_url'] = settings.MP_PANORAMAIO_BASE_URL
        try:
            if panoramio_extra_data_obj:
                panoramio = Panoramio()
                panoramio.pre_run(action, panoramio_extra_data_obj)
                panoramio_data = panoramio.places(params)
                self.p.push_list(panoramio_data)
        except:pass

        # Fetch Foursquare place details
        foursquare_extra_data_obj = {}
        foursquare_extra_data_obj['client_id'] = settings.NEW_MP_FOURSQUARE_CLIENT_ID
        foursquare_extra_data_obj['client_secret'] = settings.NEW_MP_FOURSQUARE_CLIENT_SECRET
        foursquare_extra_data_obj['version'] = settings.NEW_MP_FOURSQUARE_VERSION
        try:
            if foursquare_extra_data_obj:
                foursquare = FoursquareMain()
                foursquare.pre_run(action, foursquare_extra_data_obj)
                foursquare_data = foursquare.places(params)
                self.p.push_list(foursquare_data )
        except:pass

        # Fetch Flickr place details
        flickr_extra_data_obj = {}
        flickr_extra_data_obj['flickr_public'] = settings.MP_FLICKR_PUBLIC
        flickr_extra_data_obj['flickr_secret'] = settings.MP_FLICKR_SECRET
        try:
            if flickr_extra_data_obj:
                flickr = FlickrMain()
                flickr.pre_run(action, flickr_extra_data_obj)
                flickr_data = flickr.places(params)
                self.p.push_list(flickr_data)
        except:pass
        self.p.pclose()


class ProviderActions(Enum):
    get_places = 'places'
