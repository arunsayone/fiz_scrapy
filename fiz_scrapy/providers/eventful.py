import logging
import requests

from datetime import datetime
from .utils import format_fields, map_dict, strip_html_tags

from fiz_scrapy.missing_place import MissingPlaceService

logger = logging.getLogger(__name__)

MAX_REQUESTS_PER_PROVIDER = 4


class Eventful:

    rate_limit = "1250/h"

    def pre_run(self, action, extra, *args, **kwargs):
        self.provider_name = 'eventful'

        extra_data = extra
        if extra_data:
            self.extra_data = extra_data

        self.app_key = self.extra_data['app_key']
        self.base_url = self.extra_data['base_url']

    def _map_address(self, obj):
        return format_fields([obj.get('address'), obj.get('city_name'),
                              obj.get('region_name'), obj.get('country_name')])

    def __map(self, obj):

        keys = [
            ('name', 'venue_name'),
            ('lat', 'latitude'),
            ('lon', 'longitude'),
            ('provider_url', 'venue_url'),
            ('third_party_id', 'venue_id'),
            ('address', 'venue_address'),
            ('third_party_provider', lambda obj: self.provider_name),
            ('types', lambda obj: []),
        ]

        mapped_obj = map_dict(keys, obj)

        logger.info(
            '{} - Place {}'.format(
                self.provider_name.title(),
                mapped_obj['third_party_id']
            )
        )

        return mapped_obj

    def places(self, params):
        url = '{}events/search'.format(self.base_url)
        search_params = {
            'app_key': self.app_key,
            'location': '{},{}'.format(params['lat'], params['lon']),
            'within': float(params['radius']) / 1000,
            'page_size': 50
        }

        page_count = None
        places = []
        for i in range(MAX_REQUESTS_PER_PROVIDER):

            if page_count is None or i < page_count:

                response = requests.get(url, params=search_params)
                response_json = response.json()

                # Only useful in first iteration
                page_count = int(response_json.get('page_count', 0))
                current_page = int(response_json.get('page_number', 1))

                search_params['page_number'] = current_page + 1
                if (response_json.get('events') is not None and
                   response_json.get('events').get('event') is not None):
                    venues = response_json.get('events', {}).get('event', [])
                else:
                    venues = []

                places += map(self.__map, venues)

        ids = [place['third_party_id'] for place in places]
        print "Eventful all: {} vs Unique {}".format(len(ids),
                                                     len(list(set(ids))))
        # Remove repeated places
        dic = {place['third_party_id']: place for place in places}
        places = dic.values()
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

    def fetch_images(self, third_party_id):
        url = '{}venues/get'.format(self.base_url)

        search_params = {
            'app_key': self.app_key,
            'id': third_party_id
        }
        response = requests.get(url, params=search_params)
        keys = [
            'name',
            ('lat', 'latitude'),
            ('lon', 'longitude'),
            ('provider_url', 'url'),
            ('third_party_id', 'id'),
            ('address', self._map_address_detail),
            ('pictures', self._map_pictures_detail),
            ('reviews', self._map_reviews_detail),
            ('events', self._map_events_detail),
            ('tips', lambda obj: []),
            ('description', lambda obj: strip_html_tags(
                obj.get('description')
            )),
            ('third_party_provider', lambda obj: self.provider_name),
            ('types', lambda obj: ([obj.get('venue_type')]
                                   if obj.get('venue_type') is not None
                                   else []))
        ]
        result = map_dict(keys, response.json())
        return result

    def _map_pictures_detail(self, obj):
        pictures = []
        image_types = ['medium', 'small', 'thumb']
        if obj.get('images'):
            if obj.get('images').get('image'):
                # for image in obj.get('images', {}).get('image'):
                    picture = {}
                    for image_type in image_types:
                        if isinstance(obj.get('images').get('image'), (list)):
                            if obj.get('images').get('image')[0].get(image_type):
                                picture['url'] = obj.get('images').get('image')[0].get(image_type)['url']
                                picture['provider'] = self.provider_name
                                break
                        elif obj.get('images').get('image').get(image_type):
                            picture['url'] = obj.get('images').get('image').get(image_type)['url']
                            picture['provider'] = self.provider_name
                            break
                        else:
                            pass

                    pictures.append(picture)
        return pictures

    def _map_address_detail(self, obj):
        return format_fields([obj.get('address'), obj.get('city'),
                              obj.get('region'), obj.get('country')])

    def _map_reviews_detail(self, obj):
        comments_list = []
        reviews = []
        comments = obj.get('comments')
        if comments is not None:
            if isinstance(comments, list):
                comments_list = comments
            elif comments.get('comment') is not None:
                if isinstance(comments.get('comment'), dict):
                    comments_list = [comments.get('comment')]
                elif isinstance(comments.get('comment'), list):
                    comments_list = comments.get('comment')

            # At this point, isinstance(comments, list) == True
            for comment in comments_list:
                try:
                    reviews.append({
                        'text': comment['text'],
                        'provider': self.provider_name,
                        'date': datetime.strptime(comment['time'],
                                                  '%Y-%m-%d %H:%M:%S'),
                        'author': comment['username']
                    })
                except: pass

        return reviews

    def _map_events_detail(self, obj):
        events = []
        if obj.get('events'):
            if obj.get('events').get('event'):
                obj_events = obj.get('events').get('event')
                if isinstance(obj_events, dict):
                    obj_events = [obj_events]
                for evt in obj_events:
                    # if evt.get('start_time'):
                    #     start_time = datetime.strptime(evt['start_time'],
                    #                                    '%Y-%m-%d %H:%M:%S')
                    # else:
                    #     start_time = None
                    # if evt.get('stop_time'):
                    #     stop_time = datetime.strptime(evt['stop_time'],
                    #                                   '%Y-%m-%d %H:%M:%S')
                    # else:
                    #     stop_time = None
                    stop_time = start_time = None
                    events.append({
                        'start_time': start_time,
                        'stop_time': stop_time,
                        'title': evt['title'],
                        'url': evt['url'],
                        'description': strip_html_tags(evt['description']),
                        'provider': self.provider_name,
                        'third_party_id': evt['id']
                    })
        return events

    def place_details(self, params):
        url = '{}venues/get'.format(self.base_url)
        third_party_id = params['pids']
        if third_party_id:
            third_party_id = third_party_id[0]
        search_params = {
            'app_key': self.app_key,
            'id': third_party_id
        }
        response = requests.get(url, params=search_params)

        keys = [
            'name',
            ('lat', 'latitude'),
            ('lon', 'longitude'),
            ('provider_url', 'url'),
            ('third_party_id', 'id'),
            ('address', self._map_address_detail),
            ('pictures', self._map_pictures_detail),
            ('reviews', self._map_reviews_detail),
            ('events', self._map_events_detail),
            ('tips', lambda obj: []),
            ('description', lambda obj: strip_html_tags(
                obj.get('description')
            )),
            ('third_party_provider', lambda obj: self.provider_name),
            ('types', lambda obj: ([obj.get('venue_type')]
                                   if obj.get('venue_type') is not None
                                   else []))
        ]

        result = map_dict(keys, response.json())

        return [result]
