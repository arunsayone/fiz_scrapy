import logging
import requests

from datetime import datetime
from .utils import map_dict

logger = logging.getLogger(__name__)


class InstagramAPI():

    rate_limit = None

    def pre_run(self, provider, action, *args, **kwargs):
        self.provider_name = provider.name

        extra_data = provider.extra_data.first()
        if extra_data:
            self.extra_data = extra_data.data

        self.access_token = self.extra_data['access_token']
        self.base_url = self.extra_data['base_url']

    def places(self, params):
        search_params = {
            'lat': params['lat'],
            'lng': params['lon'],
            'distance': params['radius'],
            'access_token': self.access_token
        }

        url = '{}/locations/search'.format(self.base_url)
        response = requests.get(url, params=search_params)

        logger.info('{} - Searching places'.format(
            self.provider_name.title())
        )

        return map(self.__map, response.json()['data'])

    # Map methods
    def __map(self, obj):
        keys = [
            'name',
            ('third_party_id', 'id'),
            ('lat', 'latitude'),
            ('lon', 'longitude'),
            ('third_party_provider', lambda obj: self.provider_name),
            ('types', lambda obj: [])
        ]
        mapped_obj = map_dict(keys, obj)
        logger.info(
            '{} - Place {}'.format(
                self.provider_name.title(),
                mapped_obj['third_party_id']
            )
        )
        return mapped_obj

    def _map_location_from(self, provider, pid):
        url_map_location = '{}/locations/search'.format(self.base_url)
        provider_dic = {
            'facebook': 'facebook_places_id',
            'foursquare': 'foursquare_v2_id'
        }

        params = {
            provider_dic[provider]: pid,
            'access_token': self.access_token
        }
        response = requests.get(url_map_location, params=params)
        id = None
        try:
            id = response.json()['data'][0]['id']
        except (KeyError, IndexError):
            pass
        return id

    def __get_image_url(self, obj):
        image_types = ['standard_resolution', 'low_resolution', 'thumbnail']
        url = None
        for image_type in image_types:
            if obj.get('images', {}).get(image_type) is not None:
                return obj.get('images', {}).get(image_type).get('url')
        return url

    def __get_image_caption(self, obj):
        if obj.get('caption') is not None:
            return obj.get('caption').get('text')
        return None

    def __get_image_date(self, obj):
        if obj.get('caption') is not None:
            created_time = obj.get('caption').get('created_time')
            if created_time:
                return datetime.fromtimestamp(float(created_time))
            return None
        return None

    def __get_image_author(self, obj):
        if obj.get('caption') is not None:
            if obj.get('caption').get('from') is not None:
                if obj.get('caption').get('from').get('username') is not None:
                    username = obj.get('caption').get('from').get('username')
                    return (username,
                            'https://instagram.com/{}'.format(username))
        return None, None

    def _map_picture_details(self, obj):
        author, author_url = self.__get_image_author(obj)
        keys = [
            ('likes', 'likes.count'),
            ('caption', self.__get_image_caption),
            ('url', self.__get_image_url),
            ('provider', lambda obj: self.provider_name),
            ('date', self.__get_image_date),
            ('author', lambda obj: author),
            ('author_profile_url', lambda obj: author_url),
        ]
        return map_dict(keys, obj)

    def _place_pictures(self, third_party_id=None):
        search_params = {
            'access_token': self.access_token
        }

        if third_party_id:
            url_media_recent = ('{}/locations/{}/media/recent'
                                .format(self.base_url, third_party_id))
        response_media = requests.get(url_media_recent, params=search_params)

        pictures = map(self._map_picture_details,
                       response_media.json()['data'])

        # Return images sorted by 'likes'
        pictures = sorted(pictures, key=lambda dic: dic['likes'], reverse=True)
        return pictures

    def _place_pictures_from(self, provider, third_party_id):
        instagram_pictures = []
        instagram_pid = self._map_location_from(provider,
                                                third_party_id)
        if instagram_pid:
            instagram_pictures = self._place_pictures(instagram_pid)
        return instagram_pictures

    def place_details(self, params):
        third_party_id = params.get('pid')
        url_location_info = '{}/locations/{}'.format(self.base_url,
                                                     third_party_id)
        search_params = {
            'access_token': self.access_token
        }

        response_location = requests.get(url_location_info,
                                         params=search_params)
        keys = [
            ('third_party_id', 'data.id'),
            ('name', 'data.name'),
            ('lat', 'data.latitude'),
            ('lon', 'data.longitude'),
            ('third_party_provider', lambda obj: self.provider_name),
            ('types', lambda obj: [])
        ]
        result = map_dict(keys, response_location.json())

        pictures = self._place_pictures(third_party_id)
        result['pictures'] = pictures

        return [result]
