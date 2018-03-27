import logging
import datetime

from datetime import timedelta
from fiz_scrapy.missing_place import MissingPlaceService
from .utils import is_exception_ssl_error, map_dict

from retrying import retry
from flickrapi import FlickrAPI

logger = logging.getLogger(__name__)
MAX_REQUESTS_PER_PROVIDER = 4


class FlickrMain():

    rate_limit = "3500/h"

    def pre_run(self, action, extra, *args, **kwargs):
        self.provider_name = 'flickr'

        extra_data = extra
        if extra_data:
            self.extra_data = extra_data

        self.flickr_public = self.extra_data['flickr_public']
        self.flickr_secret = self.extra_data['flickr_secret']

    def _map_pictures(self, obj):
        picture_keys = [
            ('provider', lambda object: self.provider_name),
            ('caption', lambda object: "Flickr"),
            ('photo_id', lambda object:item['id']),
            ('owner', lambda object:item['owner']),
            ('title', lambda object:item['title']),
            ('url', lambda object: item['url_o'] if 'url_o' in item else item['url_l']),
            # ('date', lambda object:self.parse_date(item['dateupload']))
        ]

        pictures = []
        if int(len(obj['photos']['photo'])) > 0:
            for item in obj['photos']['photo']:
                before_days = datetime.datetime.now().date()-timedelta(days=100)
                date_obj = self.parse_date(item['dateupload'])
                if before_days < date_obj < datetime.datetime.now().date():
                    pictures.append(map_dict(picture_keys, item))
        return pictures

    def parse_date(self, date_upload):
        upload_date = datetime.datetime.fromtimestamp(int(date_upload)).strftime('%Y-%m-%d %H:%M:%S')
        datetime_object = datetime.datetime.strptime(upload_date, '%Y-%m-%d %H:%M:%S')
        date_obj = datetime_object.date()
        # print 'DATE.....\n\n\n', date_obj
        return date_obj

    @retry(retry_on_exception=is_exception_ssl_error, stop_max_attempt_number=2)
    def places(self, params):
        lat = params['lat']
        log = params['lon']
        # third_party_id = params['pid']

        logger.info('{} - Searching places'.format(
            self.provider_name.title())
        )

        total_results = None
        places = []

        # Need do precalculate the offsets
        for i in range(MAX_REQUESTS_PER_PROVIDER):
            if total_results is None:
                flickr = FlickrAPI(self.flickr_public, self.flickr_secret, format='parsed-json')
                place_details = flickr.places.findByLatLon(lat=lat, lon=log)
                venues = place_details['places']['place']
                places += map(self._map, venues)

        for item in places[:2]:
            parameters = {'pids': [item['third_party_id']]}
            item['place_details'] = self.place_details(parameters)
            # scraped_data_list = self.scoring_data_fetch(item)
            # item['scraped_data_list'] = scraped_data_list
        return places

    def scoring_data_fetch(self, place):
        service = MissingPlaceService()
        scraped_data_list = []
        i = {
            'name': place['name'] if 'name' in place else None,
            'email': place['email'] if 'email' in place else None,
            'phone': place['phone'] if 'phone' in place else None,
            'address': place['place_details'][0]['address'] if 'address' in place['place_details'][0] else None,
            'category': place['types'] if 'types' in place else None,
            'rating': place['place_details'][0]['rating'] if 'rating' in place['place_details'][0] else None,
            'website': place['web'] if 'web' in place else None,
            'latitude': place['lat'] if 'lat' in place else None,
            'longitude': place['lon'] if 'lon' in place else None

        }
        scraped_data_list = service.third_party(i, scraped_data_list, place['name'])
        return scraped_data_list

    def fetch_images(self, third_party_id):
        license_included = '0,4,5,6,7,8,9,10'
        extras = 'url_o, views, date_upload, date_taken, url_l'
        flickr = FlickrAPI(self.flickr_public, self.flickr_secret, format='parsed-json')
        data = flickr.photos.search(place_id=third_party_id, format='parsed-json', extras=extras,
                                    license=license_included)
        keys = [('pictures', self._map_pictures)]
        result = map_dict(keys, data)
        return result

    def _map(self, obj):
        keys = [
            ('name', 'name'),
            ('lat', 'latitude'),
            ('lon', 'longitude'),
            ('phone', 'contact.formattedPhone'),
            ('third_party_id', 'place_id'),
            ('place_type', 'place_type'),
            ('woeid', 'woeid'),
        ]

        mapped_obj = map_dict(keys, obj)

        # Set Provider information
        mapped_obj['third_party_provider'] = self.provider_name

        logger.info(
            '{} - Place {}'.format(
                self.provider_name.title(),
                mapped_obj['third_party_id']
            )
        )

        return mapped_obj

    def place_details(self, params):

        third_party_id = params['pids']
        if third_party_id:
            self.third_party_id = third_party_id[0]
        license_included = '0,4,5,6,7,8,9,10'
        extras = 'url_o, views, date_upload, date_taken, url_l'
        flickr = FlickrAPI(self.flickr_public, self.flickr_secret, format='parsed-json')
        # flickr = flickrapi.FlickrAPI(self.flickr_public, self.flickr_secret)
        data = flickr.photos.search(place_id=self.third_party_id, format='parsed-json', extras=extras,
                                    license=license_included)
        cats = flickr.places.getInfo(place_id=self.third_party_id)
        longitude = cats['place'].get('longitude')
        latitude = cats['place'].get('latitude')
        name = cats['place'].get('name')
        keys = [
            ('web', lambda obj: "Not Provided"),
            ('description', lambda obj: "Not Provided"),
            ('rating', lambda obj: int(0)),
            ('twitter_url', lambda obj: "Not Provided"),
            ('phone', lambda obj: None),
            ('name', lambda obj: name),
            ('types', lambda obj: None),
            ('lat', lambda obj: longitude),
            ('lon', lambda obj: latitude),
            ('third_party_id', lambda obj: self.third_party_id),
            ('pictures', self._map_pictures),
            ('third_party_provider', lambda obj: self.provider_name)
        ]

        result = map_dict(keys, data)
        return [result]