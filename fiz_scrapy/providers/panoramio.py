import logging
import requests

from datetime import datetime

from utils import map_dict

logger = logging.getLogger(__name__)


class Panoramio():

    rate_limit = None

    def pre_run(self, action,extra, *args, **kwargs):
        self.provider_name = 'panoramio'
        extra_data = extra
        if extra_data:
            self.extra_data = extra_data

        logger.info('Connecting to {}'.format(self.provider_name.title()))
        self.base_url = self.extra_data['base_url']

    def places(self, params):
        # For the time being, Panoramio does not return places
        return []

    def place_details(self, params):
        # For the time being, Panoramio does not return place details
        return []

    def _map_image(self, obj):
        keys = [
            ('caption', 'photo_title'),
            ('url', 'photo_file_url'),
            ('provider', lambda obj: self.provider_name),
            ('date', lambda obj: datetime.strptime(obj['upload_date'],
                                                   '%d %B %Y')),
        ]
        return map_dict(keys, obj)

    def images(self, params):
        search_params = {
            'set': 'full',
            'from': 0,
            'to': 20,
            'size': 'small',
            'map_filter': False
        }
        lat, lon = params['lat'], params['lon']

        # TODO: Parametrize the radius and create the box coords from that.
        radius = 0.004
        min_lat = float(lat) - radius
        max_lat = float(lat) + radius
        min_lon = float(lon) - radius
        max_lon = float(lon) + radius
        search_params.update({
            'minx': min_lon,
            'maxx': max_lon,
            'miny': min_lat,
            'maxy': max_lat
        })

        response = requests.get(self.base_url, params=search_params)

        images = map(self._map_image, response.json()['photos'])

        print 'images\n\n\n', images
        return images
