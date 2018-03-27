import logging

from datetime import datetime
from fiz_scrapy.missing_place import MissingPlaceService
from .yelp_api import *
from .utils import map_dict

logger = logging.getLogger(__name__)
MAX_REQUESTS_YELP = 10


class YelpMain():
    rate_limit = "1000/h"

    def pre_run(self, action, extra, *args, **kwargs):
        self.provider_name = 'yelp'

        extra_data = extra
        if extra_data:
            self.extra_data = extra_data

        self.app_id = self.extra_data['app_id']
        self.app_secret = self.extra_data['app_secret']
        self.access_token = self.extra_data['access_token']

        logger.info('Connecting to {}'.format(self.provider_name.title()))
        # The API does not allow an offset bigger greater than 20
        self.offset = 20

    def places(self, params):
        """
        Sort mode: 0=Best matched (default), 1=Distance, 2=Highest Rated.
        If the mode is 1 or 2 a search may retrieve an additional 20 businesses
        past the initial limit of the first 20 results.
        This is done by specifying an offset and limit of 20.
        """
        self.offset = 0
        search_params = {
            'radius': int(float(params['radius'])),
            'latitude': params['lat'],
            'limit': 20,
            'offset': 0,
            'longitude': params['lon']
        }
        if params['categories']:
            search_params['category_filter'] = ','.join(params['categories'])

        logger.info('{} - Searching places'.format(
            self.provider_name.title())
        )
        places = []
        num_businesses = 0
        for i in range(MAX_REQUESTS_YELP):
            try:
                # data = {'grant_type': 'client_credentials',
                # 'client_id': self.app_id,
                #         'client_secret': self.app_secret}
                # token = requests.post('https://api.yelp.com/oauth2/token', data=data)
                # access_token = token.json()['access_token']
                url = 'https://api.yelp.com/v3/businesses/search'
                headers = {'Authorization': 'bearer %s' % self.access_token}
                response = requests.get(url=url, params=search_params, headers=headers)
                data = json.loads(response.text)

            except TypeError as e:
                logger.error('{} - Error on wrapper: {}'
                             .format(self.provider_name, e))
                break

            # search_params['offset'] += self.offset
            new_places = []
            for i, business in enumerate(data['businesses']):
                num_businesses += 1
                try:
                    new_places.append(self._map(business))
                except TypeError as e:
                    logger.error('{} - Error on place "{}": ({}){}'
                                 .format(self.provider_name,
                                         business.id,
                                         type(e).__name__,
                                         e)
                    )
            places += new_places
            if num_businesses >= len(data):
                break

        # for item in places:
        #     parameters = {'pid': item['third_party_id']}
        #     output = self.place_details(parameters)
        #     item['place_details'] = output
        #     scraped_data_list = self.scoring_data_fetch(item)
        #     item['scraped_data_list'] = scraped_data_list

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

    def place_details(self, params):
        if not params['pids']:
            raise ValueError('PID parameter must be defined')
        # return self._map_details(self.client.GetBusiness(params['pid']))
        third_party_id = params['pids']
        if third_party_id:
            third_party_id = third_party_id[0]
        business = get_business(self.client, third_party_id)
        reviews = get_reviews(self.client, third_party_id)
        business['reviews'] = reviews['reviews']
        return self._map_details(business)

    # Map methods

    # List
    def _map(self, obj):
        keys = [
            ('name', lambda obj: obj['name']),
            ('address',
             lambda obj: ', '.join(obj['location']['display_address'])),
            ('lat', lambda obj: obj['coordinates']['latitude']),
            ('lon', lambda obj: obj['coordinates']['longitude']),
            ('phone', 'display_phone'),
            ('third_party_id', lambda obj: obj['id']),
            # ('types', lambda obj: [cat[1]
            # for cat in obj['categories']]),
            ('web', 'url'),
        ]

        mapped_obj = map_dict(keys, obj)

        # Set Provider information
        mapped_obj['third_party_provider'] = self.provider_name

        logger.info(
            '{} - Place {}'.format(
                self.provider_name.title(),
                # UTF-8 encode id, since formar has troubles with unicodes
                mapped_obj['third_party_id'].encode('utf-8')
            )
        )

        return mapped_obj

    # Details
    def _map_pictures(self, obj):
        pictures = []
        if obj['image_url']:
            picture_keys = [
                ('provider', lambda obj: self.provider_name),
                ('url',
                 lambda obj: obj['image_url'].replace('ms.jpg', 'o.jpg')),
                # ('caption', ''),
                # ('date', '')
            ]
            pictures.append(map_dict(picture_keys, obj))

        return pictures

    def _map_reviews(self, obj):
        review_keys = {
            'rating',
            ('provider', lambda obj: self.provider_name),
            # ('url', 'rating_image_url'),
            ('url', lambda obj: obj['url']),
            ('author', lambda obj: obj['user']['name']),
            ('author_profile_url', lambda obj: obj['user']['image_url']),
            ('text', lambda obj: str(obj[u'text'].encode('utf-8'))),
            # ('date', lambda obj: datetime.fromtimestamp(obj[u'time_created']))
            ('date', lambda obj: datetime.strptime(obj[u'time_created'], "%Y-%m-%d %H:%M:%S"))
        }

        return [
            map_dict(review_keys, review) for review in obj['reviews']
        ]

    def _map_details(self, obj):
        keys = [
            ('name', 'name'),
            ('address',
             lambda obj: ', '.join(obj['location']['display_address'])),
            ('lat', lambda obj: obj['coordinates']['latitude']),
            ('lon', lambda obj: obj['coordinates']['longitude']),
            ('description', 'snippet_text'),
            ('phone', 'display_phone'),
            ('pictures', self._map_pictures),
            ('reviews', self._map_reviews),
            ('third_party_id', 'id'),
            ('types', lambda obj: [cat['title'] for cat in obj['categories']]),
            ('rating', lambda obj: obj['rating'] if 'rating' in obj else None),
            ('provider_url', 'url'),
            ('yelp_reviews_count', 'review_count'),
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

        return [mapped_obj]
