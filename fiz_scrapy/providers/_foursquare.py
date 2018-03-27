import time
import logging
import foursquare

from datetime import datetime
from fiz_scrapy.missing_place import MissingPlaceService
from .utils import is_exception_ssl_error, map_dict

from retrying import retry

logger = logging.getLogger(__name__)
MAX_REQUESTS_PER_PROVIDER = 4


class FoursquareMain():

    rate_limit = "5000/h"

    def pre_run(self, action, extra, *args, **kwargs):
        self.provider_name = 'foursquare'

        extra_data = extra
        if extra_data:
            self.extra_data = extra_data

        print 'self.extra_data\n\n\n', self.extra_data['version']

        logger.info('Connecting to {}'.format(self.provider_name.title()))
        self.client = foursquare.Foursquare(
            client_id=self.extra_data['client_id'],
            client_secret=self.extra_data['client_secret'],
            version=self.extra_data['version']
        )

        self.offset = 50

    @retry(retry_on_exception=is_exception_ssl_error,
           stop_max_attempt_number=2)
    def places(self, params):
        search_params = {
            'll': '{},{}'.format(params['lat'], params['lon']),
            'radius': params['radius'],
            'limit': 50,
            'offset': 0,
            'categoryId': (
                ','.join(params['categories'])
                if params['categories'] else ''
            )
        }

        logger.info('{} - Searching places'.format(
            self.provider_name.title())
        )

        total_results = None
        places = []

        # TODO?: Use grequests for all these requests.
        # Need do precalculate the offsets
        for i in range(MAX_REQUESTS_PER_PROVIDER):
            if (total_results is None or
               search_params.get('offset') < total_results):
                response = self.client.venues.explore(params=search_params)
                total_results = response['totalResults']

                venues = [obj['venue'] for obj in
                          response['groups'][0]['items']]
                places += map(self._map, venues)
                search_params['offset'] += self.offset

        for item in places:
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

    def fetch_images(self, obj, params):
        keys = [('pictures', self._map_pictures)]

        mapped_obj = map_dict(keys, obj)

        # # If solicited, make a call to Instagram to obtain extra pictures
        # if params.get('instagram_images'):
        #     instagram_api = (Provider.objects
        #                              .get(name='instagram')
        #                              .api_client())
        #
        #     mapped_obj['pictures'] += (instagram_api._place_pictures_from
        #                                (self.provider_name,
        #                                 mapped_obj['third_party_id']))

        return mapped_obj

    def place_details(self, params):
        if not params['pids']:
            raise ValueError('PID parameter must be defined')
        third_party_id = params['pids']
        if third_party_id:
            third_party_id = third_party_id[0]
        return self._map_details(self.client.venues(third_party_id)['venue'],
                                 params)

    # Map methods

    # List
    def _map(self, obj):
        keys = [
            ('name', 'name'),
            ('address', 'location.formattedAddress'),
            ('lat', 'location.lat'),
            ('lon', 'location.lng'),
            ('phone', 'contact.formattedPhone'),
            ('third_party_id', 'id'),
            ('types', lambda obj: [cat['id'] for cat in obj['categories']]),
            ('web', 'url'),
            ('provider_url', '_url'),
            ('twitter_url', 'contact.twitter'),
            ('foursquare_checkins_count', 'stats.checkinsCount'),
            ('foursquare_users_count', 'stats.usersCount'),
            ('foursquare_tips_count', 'stats.tipCount'),
            ('foursquare_here_now', 'hereNow.count')
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

    # Details
    def _map_author(self, obj):
        try:
            return '{} {}'.format(
                obj['user']['firstName'].encode('utf8').decode('utf8'),
                obj['user']['lastName'].encode('utf8').decode('utf8')
                if 'lastName' in obj['user'] else ''
            )
        except:
            return ''

    def _map_pictures(self, obj):
        picture_keys = [
            ('provider', lambda obj: self.provider_name),
            ('url', lambda obj: '{}500x500{}'.format(
                obj['prefix'],
                obj['suffix'])
             ),
            ('caption', ''),
            ('author', self._map_author),
            ('author_profile_url', lambda obj: '{}40x40{}'.format(
                    obj['user']['photo']['prefix'],
                    obj['user']['photo']['suffix']
                )
             )
            # ('date', lambda obj: datetime.fromtimestamp(obj['createdAt'])
            #  )
        ]
        pictures = []
        if(int(obj['photos']['count']) > 0):
            for photoitem in obj['photos']['groups']:
                if (photoitem['type'] == 'venue'):
                    for photo in photoitem['items']:
                        pictures.append(map_dict(picture_keys, photo))
        return pictures

    def _map_tips(self, obj):
        tips_keys = [
            ('provider', lambda obj: self.provider_name),
            ('url', 'canonicalUrl'),
            ('author', self._map_author),
            ('author_profile_url', lambda obj: '{}40x40{}'.format(
                    obj['user']['photo']['prefix'],
                    obj['user']['photo']['suffix']
                )
             ),
            ('text', lambda obj: obj['text'].encode('utf8').decode('utf8')),
            # ('date', lambda obj: datetime.fromtimestamp(obj['createdAt']))
        ]
        tips = []
        if(int(obj['tips']['count']) > 0):
            for tip_group in obj['tips']['groups']:
                for tip in tip_group['items']:
                    tips.append(map_dict(tips_keys, tip))
        return tips

    def _format_opening_time(self, opening_time):
        """
        Format opening time:
            3:20 PM --> 15:20:00
        """
        return time.strftime(
            '%H:%M:%S',
            time.strptime(
                opening_time,
                '%I:%M %p'
            )
        )

    def _map_opening_times(self, obj):
        """
        Map opening time to this structure:
            {
                0: [
                    (open_time, close_time),
                    .
                    .
                ],
                ...,
                ...,
                6: [
                    (open_time, close_time),
                    .
                    .
                ]
                extra_info: {
                    status: current_status,
                    is_open: is_open_now
                }
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

        hours_map = {
            'Midnight': '00:00:00',
            'Noon': '12:00:00'
        }

        opening_times = {}
        if 'hours' in obj and 'timeframes' in obj['hours']:
            # Iterates over the differents opening times in a week
            for op in obj['hours']['timeframes']:
                # Get days interval
                days = op['days'].split(',')
                days_interval = []
                for day in days:
                    if u'\u2013' in day:
                        days_split = day.split(u'\u2013')
                        start_day = days_map[days_split[0].strip()]
                        end_day = days_map[days_split[1].strip()]
                        if start_day < end_day:
                            days_interval += range(start_day, end_day + 1)
                        else:
                            days_interval += range(start_day, 7)
                            days_interval += range(0, end_day + 1)
                    else:
                        days_interval.append(days_map[day.strip()])

                # Get shifts for this interval
                segments = []
                for segment in op['open']:
                    start = segment['renderedTime'].split(u'\u2013')[0]
                    end = None
                    if start in hours_map:
                        start = hours_map[start]
                    elif start == '24 Hours':
                        start = '00:00:00'
                        end = '23:59:59'
                    else:
                        start = self._format_opening_time(start)
                    if not end:
                        end = segment['renderedTime'].split(u'\u2013')[1]
                        if end in hours_map:
                            end = hours_map[end]
                        else:
                            end = self._format_opening_time(end)
                    segments.append((start, end))

                # Set shifts for each day in days_intervals
                opening_times.update({day: segments for day in days_interval})

        return opening_times

    def _map_details(self, obj, params):
        keys = [
            'name',
            'description',
            ('third_party_id', 'id'),
            ('address', lambda obj: ', '.join(obj['location']['formattedAddress'])),
            ('foursquare_url', 'shortUrl'),
            ('provider_url', 'shortUrl'),
            ('lat', 'location.lat'),
            ('lon', 'location.lng'),
            ('web', 'url'),
            ('foursquare_checkins_count', 'stats.checkinsCount'),
            ('foursquare_likes_count', 'likes.count'),
            ('foursquare_users_count', 'stats.usersCount'),
            ('foursquare_tips_count', 'stats.tipCount'),
            ('phone', 'contact.formattedPhone'),
            ('twitter_url', 'contact.twitter'),
            ('pictures', self._map_pictures),
            # ('tips', self._map_tips),
            # ('opening_times', self._map_opening_times),
            ('types', lambda obj: [cat['id'] for cat in obj['categories']]),
            ('rating', lambda obj: obj['rating'] if 'rating' in obj else None),
        ]

        mapped_obj = map_dict(keys, obj)

        # If solicited, make a call to Instagram to obtain extra pictures
        # if params.get('instagram_images'):
        #     instagram_api = (Provider.objects
        #                              .get(name='instagram')
        #                              .api_client())
        #
        #     mapped_obj['pictures'] += (instagram_api._place_pictures_from
        #                                (self.provider_name,
        #                                 mapped_obj['third_party_id']))

        # Set Provider information
        mapped_obj['third_party_provider'] = self.provider_name

        logger.info(
            '{} - Place {}'.format(
                self.provider_name.title(),
                mapped_obj['third_party_id']
            )
        )
        return [mapped_obj]
