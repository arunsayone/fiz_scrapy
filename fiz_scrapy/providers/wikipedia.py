import logging
import requests
import grequests
import BeautifulSoup

from datetime import datetime
from fiz_scrapy.missing_place import MissingPlaceService

from .utils import map_dict, strip_html_tags


logger = logging.getLogger(__name__)


class Wikipedia():

    rate_limit = None

    def pre_run(self, action, extra, *args, **kwargs):
        self.provider_name = 'wikipedia'
        extra_data = extra
        if extra_data:
            self.extra_data = extra_data
        self.base_url = self.extra_data['base_url']

        # According to https://www.mediawiki.org/wiki/Extension:GeoData
        # the maximum value for gsradius is 10000
        self.maximum_radius = 10000

    def places(self, params):
        # Default search params
        search_params = {
            'action': 'query',
            'list': 'geosearch',
            'gslimit': 500,
            'gsprop': 'type|name|country|region',
            'format': 'json'
        }

        # Add aggregator params
        search_params.update({
            'gsradius': min(params['radius'], self.maximum_radius),
            'gscoord': '{}|{}'.format(params['lat'], params['lon']),
        })

        response = requests.post(self.base_url, params=search_params)

        logger.info('{} - Searching places'.format(
            self.provider_name.title())
        )

        results = map(self.__map, response.json()['query']['geosearch'])

        for item in results:
            third_party_id = item['third_party_id']
            # Query params for requesting extract, categories, and coordinates
            query_params_data = {'action': 'query',
                                 'explaintext': '',
                                 'format': 'json',
                                 'pageids': third_party_id,
                                 'prop': 'extracts|categories|coordinates'}

            # Query Params for requesting images info.
            query_params_images = {'action': 'query',
                                   'prop': 'imageinfo',
                                   'format': 'json',
                                   'pageids': third_party_id,
                                   'generator': 'images',
                                   'gimlimit': 'max',
                                   'iiprop': 'url|extmetadata'}

            # Make the asynchronous requests to the Wikipedia api.
            rs = (grequests.post(u, params=params) for u, params in
                  [(self.base_url, query_params_data),
                   (self.base_url, query_params_images)])
            res_data, res_images = grequests.map(rs)

            if res_data and res_images:
                res_data, res_images = res_data.json(), res_images.json()
                res_data['third_party_id'] = third_party_id
                res_data['third_party_provider'] = self.provider_name

                keys_data = [
                    'third_party_id',
                    'third_party_provider',
                    ('name', 'title'),
                    ('description', self._map_description_detail),
                    ('types', self._map_type_detail),
                    ('lat', self._map_lat_detail),
                    ('lon', self._map_lon_detail),
                    ('wikipedia_url', self._map_wikipediaurl_detail),
                    ('provider_url', self._map_wikipediaurl_detail)
                ]
                result = map_dict(keys_data, res_data)

                keys_images = [
                    ('pictures', self._map_pictures_detail)
                ]
                result.update(map_dict(keys_images, res_images))
                item['pictures'] = result['pictures']

            parameters = {'pids': [third_party_id]}
            item['place_details'] = self.place_details(parameters)
            # scraped_data_list = self.scoring_data_fetch(item)
            # item['scraped_data_list'] = scraped_data_list
        return results

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

    # Field mappers
    def _make_url(self, obj):
        return (self.base_url.replace('api', 'index') +
                '?curid=' +
                str(obj['pageid']))

    def _make_address(self, obj):
        address = ''
        if obj['country']:
            address += obj['country']
            if obj['region']:
                address += ', {}'.format(obj['region'])
        elif obj['region']:
            address += obj['region']
        return address

    # Map result object
    def __map(self, obj):
        keys = [
            'lon',
            'lat',
            ('third_party_id', 'pageid'),
            ('name', 'title'),
            ('address', self._make_address),
            ('wikipedia_url', self._make_url),
            ('types', lambda obj: ([obj.get('type')]
                                   if obj.get('type') is not None else [])),
        ]

        mapped_obj = map_dict(keys, obj)

        # Set Provider information
        mapped_obj['third_party_provider'] = self.provider_name

        logger.info(
            '{} - Place {} - {}'.format(
                self.provider_name.title(),
                mapped_obj['third_party_id'],
                'places'
            )
        )

        return mapped_obj

    def _map_description_detail(self, obj):
        return (obj['query']['pages']
                   [str(obj['third_party_id'])]
                   ['extract'].split('==')[0])

    def _map_type_detail(self, obj):
        return [cat['title'].split('Category:')[1] for cat in
                obj['query']['pages']
                   [str(obj['third_party_id'])]
                   ['categories']]

    def _map_lat_detail(self, obj):
        return (obj['query']['pages'][str(obj['third_party_id'])]
                   ['coordinates'][0]['lat'])

    def _map_lon_detail(self, obj):
        return (obj['query']['pages'][str(obj['third_party_id'])]
                   ['coordinates'][0]['lon'])

    def _map_wikipediaurl_detail(self, obj):
        return (self.base_url.replace('api', 'index') +
                '?curid=' +
                str(obj['third_party_id']))

    def __get_image_attribution(self, dic_metadata):
        attribution = {}
        license = (dic_metadata.get('LicenseShortName',
                                    dic_metadata.get('License', {}))
                               .get('value'))

        raw_license_url = dic_metadata.get('LicenseUrl', {}).get('value', '')
        if 'http' in raw_license_url:
            license_url = dic_metadata.get('LicenseUrl', {}).get('value')
        elif raw_license_url != '':
            license_url = 'http:{}'.format(raw_license_url)
        else:
            license_url = None

        author_html = dic_metadata.get('Artist', {}).get('value')

        attribution = {
            'license': license,
            'license_url': license_url
        }
        if author_html:
            soup = BeautifulSoup.BeautifulSoup(author_html)

            if len(soup.findAll('a')) == 0:
                return attribution
            author_dict = dict(soup.findAll('a')[0].attrs)

            title = author_dict.get('title')
            if title and len(title.split('User:')) > 1:

                author = title.split('User:')[1]

            else:
                author = ''

            author_has_url = 'page does not exist' not in author
            if author and not author_has_url:
                author = author.split(' (page does not exist)')[0]

            href = author_dict.get('href')
            if '&' in href:
                href = href.split('&')[0]
            if href and author_has_url:
                author_url = 'http:{}'.format(href)
            else:
                author_url = None

            attribution.update({
                'author': author,
                'author_url': author_url
            })

        return attribution

    def _map_pictures_detail(self, obj):
        res_pictures = []
        if 'query' in obj:
            for k, v in obj['query']['pages'].items():

                if '.ogg' not in v['imageinfo'][0]['url']:
                    pic_details = {
                        'url': v['imageinfo'][0]['url'],
                        'provider': self.provider_name,
                        'caption': strip_html_tags(v['imageinfo'][0]['extmetadata']
                                                   .get('ImageDescription', {})
                                                   .get('value', '')),
                        'attribution': self.__get_image_attribution(
                                        v['imageinfo']
                                        [0]
                                        ['extmetadata'])
                    }

                    pic_details['name'] = (v['imageinfo'][0]['extmetadata']
                                           .get('ObjectName', {}).get('value'))

                    if (pic_details['attribution'].get('author') and
                        pic_details['attribution'].get('license') and
                       pic_details.get('name')):

                        # Set up attribution text using image name,
                        # author, and license.
                        pic_details['attribution_text'] = (
                         pic_details.get('name') + ' by ' +
                         pic_details['attribution'].get('author') +
                         ' is licensed under ' +
                         pic_details['attribution'].get('license')
                        )
                    else:
                        pic_details['attribution_text'] = None

                    res_pictures.append(pic_details)

        return res_pictures

    def place_details(self, params):
        third_party_id = params['pids']
        if third_party_id:
            third_party_id = third_party_id[0]
        # Query params for requesting extract, categories, and coordinates
        query_params_data = {'action': 'query',
                             'explaintext': '',
                             'format': 'json',
                             'pageids': third_party_id,
                             'prop': 'extracts|categories|coordinates'}

        # Query Params for requesting images info.
        query_params_images = {'action': 'query',
                               'prop': 'imageinfo',
                               'format': 'json',
                               'pageids': third_party_id,
                               'generator': 'images',
                               'gimlimit': 'max',
                               'iiprop': 'url|extmetadata'}

        # Make the asynchronous requests to the Wikipedia api.
        rs = (grequests.post(u, params=params) for u, params in
              [(self.base_url, query_params_data),
               (self.base_url, query_params_images)])
        res_data, res_images = grequests.map(rs)
        res_data, res_images = res_data.json(), res_images.json()
        res_data['third_party_id'] = third_party_id
        res_data['third_party_provider'] = self.provider_name

        keys_data = [
            'third_party_id',
            'third_party_provider',
            ('name', 'title'),
            ('description', self._map_description_detail),
            ('types', self._map_type_detail),
            ('lat', self._map_lat_detail),
            ('lon', self._map_lon_detail),
            ('wikipedia_url', self._map_wikipediaurl_detail),
            ('provider_url', self._map_wikipediaurl_detail)
        ]
        result = map_dict(keys_data, res_data)

        keys_images = [
            ('pictures', self._map_pictures_detail)
        ]
        result.update(map_dict(keys_images, res_images))

        logger.info(
            '{} - Place {} - {}'.format(
                self.provider_name.title(),
                result['third_party_id'],
                'place_details'
            )
        )

        return [result]
