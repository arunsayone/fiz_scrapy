import scrapy
import json
from enum import Enum
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher

from fiz_scrapy import settings
from fiz_scrapy.producer import Publisher

from fiz_scrapy.providers._yelp import YelpMain
from fiz_scrapy.providers._google import Google
from fiz_scrapy.providers.eventful import Eventful
from fiz_scrapy.providers._flickr import FlickrMain
from fiz_scrapy.providers.wikipedia import Wikipedia
from fiz_scrapy.providers.panoramio import Panoramio
from fiz_scrapy.providers._facebook import FacebookMain
from fiz_scrapy.providers._foursquare import FoursquareMain


class MissingPlaceSpider(scrapy.Spider):
    name = "missing_place"
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

    def __init__(self, data=None, place=None, shub_id=None, job_id=None, job_type=None, *args, **kwargs):
        super(MissingPlaceSpider, self).__init__(*args, **kwargs)
        # dispatcher.connect(self.spider_closed, signals.spider_closed)
        self.final_data = []

        # self.data = json.loads(data)
        # self.action = ProviderActions.get_place_details
        # self.providers = self.data['providers']
        # self.shub_id = int(shub_id)
        # self.job_id = int(job_id)
        # self.job_type = job_type
        # self.place = place

        # Places
        self.action = ProviderActions.get_place_details
        self.providers = {"google": {"pids": ["ChIJ7cKcKNWh2UcRd-VAhGB97Mk"]}}
        # self.providers = {u'foursquare': {'pids': [u'5649b957498ef53f75b4a98e']}, u'google': {'pids': [u'ChIJFUQ4x6Oxe0gRLHCX6_XSEso']}, u'flickr': {'pids': [u'Dqd8n29TWrgqng']}}
        self.place = 'Jokers Comedy Club'
        self.shub_id = 294030
        self.job_id = 26
        self.job_type = 'missing'

        self.p = Publisher(self.shub_id, request_type=job_type, job_id=job_id)

    def parse(self, params):
        """
        :param params:
        :return:

        This function pass providers information to place-details for fetching information using the third-party ids.
        """
        if self.action:
            data = self.providers
            self.get_place_details(data, ProviderActions.get_place_details)

    def get_place_details(self, params, action):
        """
            Returns a list of place details' information,for the specified third party providers.

            Body parameters:
            * __providers__ (JSON): Object that indicates the providers to be used, and
                                for each one, a list of the categories to use as filters.
                * __providerName1__ (JSON): Object indicating to use the provider providerName1
                                       along with the categories specified within the object.
                * __providerName2__ (JSON): ...

            ---
        """
        result = []
        # Fetch Eventful place details
        eventful_extra_data_obj = {}
        eventful_extra_data_obj['app_key'] = settings.MP_EVENTFULL_APP_KEY
        eventful_extra_data_obj['base_url'] = settings.MP_EVENTFULL_BASE_URL
        if eventful_extra_data_obj:
            eventful = Eventful()
            if 'eventful' in params:
                eventful.pre_run(action, eventful_extra_data_obj)
                eventful_data = eventful.place_details(params["eventful"])
                result.append(eventful_data)
                # print '*******eventful_data*******', eventful_data

        # Fetch Google place details
        google_extra_data_obj = {}
        google_extra_data_obj['key'] = settings.MP_GOOGLE_TOKEN
        if google_extra_data_obj:
            google = Google()
            if 'google' in params:
                google.pre_run(action, google_extra_data_obj)
                google_data = google.place_details(params["google"])
                result.append(google_data)
                # print '*******google_data*******', google_data

        # Fetch Facebook place details
        facebook_extra_data_obj = {}
        facebook_extra_data_obj['app_id'] = settings.MP_FACEBOOK_APP_ID
        facebook_extra_data_obj['app_secret'] = settings.MP_FACEBOOK_APP_SECRET
        if facebook_extra_data_obj:
            facebook = FacebookMain()
            if 'facebook' in params:
                facebook.pre_run(action, facebook_extra_data_obj)
                facebook_data = facebook.place_details(params["facebook"])
                result.append(facebook_data)
                # print '*******facebook_data*******', facebook_data

        # Fetch Yelp place details
        yelp_extra_data_obj = {}
        yelp_extra_data_obj['app_id'] = settings.MP_YELP_APP_ID
        yelp_extra_data_obj['app_secret'] = settings.MP_YELP_APP_SECRET
        yelp_extra_data_obj['access_token'] = settings.MP_YELP_ACCESS_TOKEN

        yelp_extra_data_obj['consumer_key'] = settings.MP_YELP_CONSUMER_KEY
        yelp_extra_data_obj['consumer_secret'] = settings.MP_YELP_CONSUMER_SECRET
        yelp_extra_data_obj['access_token_key'] = settings.MP_YELP_TOKEN
        yelp_extra_data_obj['access_token_secret'] = settings.MP_YELP_TOKEN_SECRET

        if yelp_extra_data_obj:
            yelp = YelpMain()
            if 'yelp' in params:
                yelp.pre_run(action, yelp_extra_data_obj)
                yelp_data = yelp.place_details(params["yelp"])
                result.append(yelp_data)
                # print '*******yelp_data*******', yelp_data

        # Fetch Wikipedia place details
        wikipedia_extra_data_obj = {}
        wikipedia_extra_data_obj['base_url'] = settings.MP_WIKIPEDIA_BASE_URL
        if wikipedia_extra_data_obj:
            wikipedia = Wikipedia()
            if 'wikipedia' in params:
                wikipedia.pre_run(action, wikipedia_extra_data_obj)
                wikipedia_data = wikipedia.place_details(params["wikipedia"])
                result.append(wikipedia_data)
                print '*******wikipedia_data*******', wikipedia_data

        # Fetch Panoramio place details
        panoramio_extra_data_obj = {}
        panoramio_extra_data_obj['base_url'] = settings.MP_PANORAMAIO_BASE_URL
        if panoramio_extra_data_obj:
            panoramio = Panoramio()
            if 'panoramio' in params:
                panoramio.pre_run(action, panoramio_extra_data_obj)
                panoramio_data = panoramio.place_details(params["panoramio"])
                result.append(panoramio_data)
                # print '*******panoramio_data*******', panoramio_data

        # Fetch Foursquare place details
        foursquare_extra_data_obj = {}
        foursquare_extra_data_obj['client_id'] = settings.NEW_MP_FOURSQUARE_CLIENT_ID
        foursquare_extra_data_obj['client_secret'] = settings.NEW_MP_FOURSQUARE_CLIENT_SECRET
        foursquare_extra_data_obj['version'] = settings.NEW_MP_FOURSQUARE_VERSION
        if foursquare_extra_data_obj:
            foursquare = FoursquareMain()
            if 'foursquare' in params:
                foursquare.pre_run(action, foursquare_extra_data_obj)
                foursquare_data = foursquare.place_details(params["foursquare"])
                result.append(foursquare_data)
                # print '*******foursquare_data*******', foursquare_data

        # Fetch Flickr place details
        flickr_extra_data_obj = {}
        flickr_extra_data_obj['flickr_public'] = settings.MP_FLICKR_PUBLIC
        flickr_extra_data_obj['flickr_secret'] = settings.MP_FLICKR_SECRET
        if flickr_extra_data_obj:
            flickr = FlickrMain()
            if 'flickr' in params:
                flickr.pre_run(action, flickr_extra_data_obj)
                flickr_data = flickr.place_details(params["flickr"])
                result.append(flickr_data)
                # print '*******flickr_data*******', flickr_data

        final_data = [item for sublist in result for item in sublist]
        self.p.push_list([{'place': self.place, 'place_data': final_data}, ])
        self.p.pclose()


class ProviderActions(Enum):
    get_place_details = 'place_details'