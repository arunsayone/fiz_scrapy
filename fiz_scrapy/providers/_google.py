import logging
import datetime

import googleplaces
from time import sleep

from .utils import map_dict
from fiz_scrapy.missing_place import MissingPlaceService

logger = logging.getLogger(__name__)
MAX_REQUESTS_PER_PROVIDER = 4


class Google():

    rate_limit = "6250/h"

    def pre_run(self, action, extra, *args, **kwargs):
        self.provider_name = 'google'

        extra_data = extra
        if extra_data:
            self.extra_data = extra_data

        logger.info('Connecting to {}'.format(self.provider_name.title()))
        self.client = googleplaces.GooglePlaces(self.extra_data['key'])

    # @retry(retry_on_exception=is_exception_urlerror, stop_max_attempt_number=2)
    def places(self, params):
        search_params = {
            'lat_lng': {
                'lat': params['lat'],
                'lng': params['lon']
            },
            'radius': params['radius'],
            'types': params['categories'] or [],
        }

        logger.info('{} - Searching places'.format(
            self.provider_name.title())
        )

        places = []
        for i in range(MAX_REQUESTS_PER_PROVIDER):
            if i == 0:
                response = self.client.nearby_search(**search_params)
                # The 'sleep' was here because supposedly, the next_page_token
                # took a few seconds to 'become valid'. Hasn't happened though.
            else:
                # Since the googleplaces wrapper function nearby_search
                # does not accept the keyword param 'pagetoken' we need to
                # do the search ourselves.
                search_params['key'] = self.extra_data['key']
                _, raw_response = googleplaces._fetch_remote_json(
                    googleplaces.GooglePlaces.NEARBY_SEARCH_API_URL,
                    search_params
                )
                response = googleplaces.GooglePlacesSearchResult(self.client,
                                                                 raw_response)

            search_params['pagetoken'] = (response.raw_response
                                                  .get('next_page_token'))
            more_places = map(
                self.__map,
                response.places
            )
            places += more_places

            # If there's no next page, then stop making requests
            if response.raw_response.get('next_page_token') is None:
                break
            else:
                # Need to wait for the token to be valid
                # http://stackoverflow.com/questions/14056488/
                sleep(1.2)

        ids = [place['third_party_id'] for place in places]
        print "ALL: {}, UNIQUE {}".format(len(ids), len(list(set(ids))))

        for item in places:
            parameters = {'pids': [item['third_party_id']]}
            output = self.place_details(parameters)
            item['place_details'] = output
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

    # Map methods
    def __map(self, obj):
        keys = [
            ('name', '_name'),
            ('lat', '_geo_location.lat'),
            ('lon', '_geo_location.lng'),
            ('phone', '_formatted_address'),
            ('third_party_id', '_place_id'),
            ('types', '_types'),
            ('web', '_website'),
            ('provider_url', '_url')
        ]

        mapped_obj = map_dict(keys, obj.__dict__)

        # Set Provider information
        mapped_obj['third_party_provider'] = self.provider_name

        logger.info(
            '{} - Place {}'.format(
                self.provider_name.title(),
                mapped_obj['third_party_id']
            )
        )

        return mapped_obj

    def _map_reviews_detail(self, obj):
        keys = [
            'rating',
            'text',
            ('author', 'author_name'),
            ('author_profile_url', 'author_url'),
            ('provider', lambda obj: self.provider_name),
            # ('date', lambda obj: datetime.datetime
            #                              .fromtimestamp(obj['time']))
        ]
        if 'reviews' in obj:
            keys = [keys for review in obj['reviews']]
            return map(map_dict, keys, obj['reviews'])
        return None

    def _map_pictures_detail(self, obj):
        # TODO: Store base url in extra_data on DB?
        images_base_url = 'https://maps.googleapis.com/maps/api/place/photo'
        image_url = ('{}?maxwidth={}&maxheight={}'
                     '&photoreference={}&key={}')
        keys = [
            ('url', (lambda img: image_url.format(images_base_url,
                                                  img['width'],
                                                  img['height'],
                                                  img['photo_reference'],
                                                  self.extra_data['key'],))),
            ('provider', lambda img: self.provider_name),
            ('html_attributions', (lambda img: img['html_attributions']))
        ]
        if 'photos' in obj:
            keys = [keys for photo in obj['photos']]
            return map(map_dict, keys, obj['photos'])
        else:
            pass

    def __format_place_time(self, timestring, format='%H:%M:%S'):
        """
        Example:
        input -> '1750'
        output -> '17:50:00'
        """
        return datetime.time(int(timestring) / 100, int(timestring) % 100, 0)

    def _map_openingtimes_detail(self, obj):
        opening_times = {}
        # if 'opening_hours' in obj.keys():
            # for period in obj['opening_hours']['periods']:
            #     day = str(period['open']['day'])
            #     open_time = self.__format_place_time(period['open']['time'])
            #     if 'close' in period:
            #         close_time = self.__format_place_time(period['close']['time'])
            #     else:
            #         close_time = None
            #     opening_times[day] = [(open_time, close_time)]
            #
            # opening_times['extra_info'] = {
            #     'open_now': obj['opening_hours']['open_now']
            # }

        return opening_times

    def place_details(self, params):
        third_party_id = params['pids']
        if third_party_id:
            third_party_id = third_party_id[0]
        place = self.client.get_place(third_party_id)
        place_details = place.details
        place_details['phone'] = (place.international_phone_number or
                                  place.local_phone_number or
                                  '')
        keys = [
            'name',
            'phone',
            'rating',
            ('provider_url', 'url'),
            ('types', 'types'),
            ('ref', 'reference'),
            ('address', 'formatted_address'),
            ('lat', 'geometry.location.lat'),
            ('lon', 'geometry.location.lng'),
            ('reviews', self._map_reviews_detail),
            ('pictures', self._map_pictures_detail),
            ('third_party_id', lambda obj: third_party_id),
            ('third_party_provider', lambda obj: self.provider_name),
            ('opening_times', self._map_openingtimes_detail)
        ]
        result = map_dict(keys, place_details)
        return [result]
