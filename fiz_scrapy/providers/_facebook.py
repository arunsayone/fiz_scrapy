import time
import logging
import iso8601
import facebook
from fiz_scrapy.missing_place import MissingPlaceService

from .utils import map_dict

logger = logging.getLogger(__name__)


class FacebookMain():

    rate_limit = "4166666/h"

    def pre_run(self, action, extra, *args, **kwargs):
        print 'facebook...\t\t', dir(facebook)
        self.provider_name = 'facebook'
        extra_data = extra
        if extra_data:
            self.extra_data = extra_data

        logger.info('Connecting to {}'.format(self.provider_name.title()))

        access_token = facebook.GraphAPI().get_app_access_token(
            self.extra_data['app_id'],
            self.extra_data['app_secret']
        )
        self.client = facebook.GraphAPI(access_token)

    def places(self, params):
        search_params = {
            'center': '{},{}'.format(params['lat'], params['lon']),
            'distance': params['radius'],
            'type': 'place',
            'fields': ','.join([
                'category', 'location', 'category_list', 'name', 'likes',
                'checkins', 'were_here_count', 'talking_about_count'
            ])
        }

        logger.info('{} - Searching places'.format(self.provider_name))

        data = map(
            self._map,
            self.client.request('search', args=search_params)['data']
        )
        for item in data:
            parameters = {'pids': [item['third_party_id']]}
            item['place_details'] = self.place_details(parameters)
            # scraped_data_list = self.scoring_data_fetch(item)
            # item['scraped_data_list'] = scraped_data_list
        return data

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

    def fetch_image(self, obj):
        keys = [('pictures', self._map_pictures)]
        mapped_obj = map_dict(keys, obj)
        return mapped_obj

    def place_details(self, params):
        if not params['pids']:
            raise ValueError('PID parameter must be defined')
        third_party_id = params['pids']
        if third_party_id:
            third_party_id = third_party_id[0]
        return self._map_details(self.client.get_object(third_party_id), params)

    # Map methods

    # List
    def _get_place_location(self, obj):
        try:
            return '{}, {}'.format(
                obj['location']['city'],
                obj['location']['country']
            )
        except:
            return ''

    def _map(self, obj):
        keys = [
            ('name', 'name'),
            ('address', self._get_place_location),
            ('lat', 'location.latitude'),
            ('lon', 'location.longitude'),
            ('third_party_id', 'id'),
            ('types', self._get_category_list),
            ('facebook_likes_count', 'likes'),
            ('facebook_checkins_count', 'checkins'),
            ('facebook_were_here_count', 'were_here_count'),
            ('facebook_talking_about_count', 'talking_about_count')
        ]

        mapped_obj = map_dict(keys, obj)

        # Set Provider information
        mapped_obj['third_party_provider'] = self.provider_name

        logger.info(
            '{} - Place {}'.format(
                self.provider_name,
                mapped_obj['third_party_id']
            )
        )

        return mapped_obj

    def _get_category_list(self, obj):
        try:
            # lambda obj: [cat['id'] for cat in obj['category_list']]
            category = [cat['id'] for cat in obj['category_list']]
            return category
        except:
            return ''

    # Details
    def _format_opening_time(self, opening_time):
        """
        Format opening time:
            15:20 --> 15:20:00
        """
        return time.strftime(
            '%H:%M:%S',
            time.strptime(
                opening_time,
                '%H:%M'
            )
        )

    def _map_opening_times(self, obj):
        """
        Map opening time:
            {
                u'sat_1_open': u'8:00',
                u'sat_1_close': u'11:00',
                u'sat_2_open': u'12:00',
                u'sat_2_close': u'18:00',
            }

        To this sctructure:
            {
                6: [
                    (08:00:00, 11:00:00),
                    (12:00:00, 18:00:00)
                ],
            }
        """
        days_map = {
            'Sun': 0,
            'Mon': 1,
            'Tue': 2,
            'Wed': 3,
            'Thu': 4,
            'Fri': 5,
            'Sat': 6,
        }

        opening_times = {}

        if 'hours' not in obj:
            return opening_times

        checked = []
        for segment, segment_time in obj['hours'].items():
            day, shift_number, status = segment.split('_')
            segment_field = '{}_{}_{}'.format(day, shift_number, status)

            if segment_field in checked:
                continue

            time = self._format_opening_time(segment_time)
            # Now get opposite status
            opposite_time_field = '{}_{}_{}'.format(
                day,
                shift_number,
                'open' if status == 'close' else 'close'
            )
            opposite_time = self._format_opening_time(
                obj['hours'][opposite_time_field]
            )

            if status == 'open':
                segment_times = (time, opposite_time)
            else:
                segment_times = (opposite_time, time)

            # Added close segment to checked lists
            checked.append(opposite_time_field)

            mapped_day = days_map[day.title()]
            if mapped_day not in opening_times:
                opening_times.update({mapped_day: [segment_times]})
            else:
                opening_times[mapped_day].append(segment_times)

        return opening_times

    def _map_pictures(self, obj):
        picture_keys = [
            ('provider', lambda obj: self.provider_name),
            ('url', 'source'),
            # ('date', lambda obj: iso8601.parse_date(obj['created_time']))
        ]
        pictures = self.client.get_connections(obj['id'], 'photos')

        if pictures and len(pictures['data']) > 0:
            return [map_dict(picture_keys, pic) for pic in pictures['data']]

    def _map_details(self, obj, params):
        keys = [
            ('name', 'name'),
            ('address', self._get_place_location),
            ('avatar', 'cover.source'),
            ('lat', 'location.latitude'),
            ('lon', 'location.longitude'),
            ('description', 'about'),
            ('phone', 'phone'),
            ('opening_times', self._map_opening_times),
            ('pictures', self._map_pictures),
            ('third_party_id', 'id'),
            ('types', self._get_category_list),
            ('provider_url', 'link'),
            ('facebook_likes_count', 'likes'),
            ('facebook_checkins_count', 'checkins'),
            ('facebook_were_here_count', 'were_here_count'),
            ('facebook_talking_about_count', 'talking_about_count')
        ]



        mapped_obj = map_dict(keys, obj)

        # If solicited, make a call to Instagram to obtain extra pictures
        if params.get('instagram_images'):
            instagram_api = (Provider.objects
                                     .get(name='instagram')
                                     .api_client())

            mapped_obj['pictures'] += (instagram_api._place_pictures_from
                                       (self.provider_name,
                                        mapped_obj['third_party_id']))

        # Set Provider information
        mapped_obj['third_party_provider'] = self.provider_name

        logger.info(
            '{} - Place {}'.format(
                self.provider_name,
                mapped_obj['third_party_id']
            )
        )

        return [mapped_obj]
