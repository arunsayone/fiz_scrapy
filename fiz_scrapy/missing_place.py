import re
import six
import time
import json
import difflib
import requests
import collections

from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

from fiz_scrapy import settings
from math import sin, cos, sqrt, radians, asin

from yelp.client import Client
from yelp.oauth1_authenticator import Oauth1Authenticator
from flickrapi import FlickrAPI
from math import radians, cos, sin, asin, sqrt, atan2


class BaseService(object):
    pass


class MissingPlaceService(BaseService):

    def third_party(self, i, scraped_data_list, place_copy):
        """
        Find all third party ids place
        """
        # print "\n\n\n\n third_partyyy", i, "iiii", scraped_data_list, "scrapped_data_list",
        # place_copy, "place_copyyyyyyyyyyyy"
        name = i['name'].encode('utf-8')
        name_copy1 = name
        original_name = name
        original_name = re.sub("[^A-Za-z0-9'.]", " ", original_name)
        google_place_name = name.decode(
            'utf-8') + " " + place_copy  # appending location with trip advisor name to search in google places
        google_place_name = re.sub("[^A-Za-z0-9'.]", " ", google_place_name)
        google_place_name = re.sub(r'\s+', '+', google_place_name)
        google_place_details = self.google_places(str(google_place_name), str(original_name))
        print google_place_details, "google place detailsssssssss", i
        ta_latitude, ta_longitude = i['latitude'], i['longitude']

        if google_place_details is not None:
            google_place_name, google_latitude, google_longitude = google_place_details["google_name"], \
                                                                   google_place_details['google_latitude'], \
                                                                   google_place_details['google_longitude']
            if google_latitude is not None and google_longitude is not None:
                km = None
                if ta_latitude is not None and ta_longitude is not None:
                    # Find coordinate difference between trip advisor coordinates and google_place_name coordinates
                    km = cord_diff(float(ta_longitude), float(ta_latitude), float(google_longitude),
                                        float(google_latitude))
                # foursquare_name = name_copy1
                # yelp_name = name_copy1
                foursquare_name = google_place_name.encode('utf-8')
                yelp_name = google_place_name.encode('utf-8')
                flickr_name = google_place_name.encode('utf-8')
                print str(foursquare_name), str(place_copy), str(ta_latitude), str(ta_longitude), 'foursquare_name###'
                if ta_latitude and ta_longitude:
                    foursquare_details = self.foursquare(str(foursquare_name), str(ta_latitude), str(ta_longitude))
                    yelp_details = self.yelp(str(yelp_name), str(place_copy), str(ta_latitude), str(ta_longitude))
                    flickr_details = self.flickr(str(flickr_name), str(ta_latitude), str(ta_longitude))
                else:
                    foursquare_details = self.foursquare(str(foursquare_name), str(google_latitude), str(google_longitude))
                    yelp_details = self.yelp(str(yelp_name), str(place_copy), str(google_latitude), str(google_longitude))
                    flickr_details = self.flickr(str(flickr_name), str(google_latitude), str(google_longitude))
                # print "\n\n\n\n\nflickr_details", flickr_details, "flickr_details detailsssssssssssssss"
                # wiki_id = self.wiki(name_copy1)
                wikipedia_id = self.wiki(google_place_name)
                # if i["wiki_id"]:
                #     # If wikipedia id is in tripadvisor details itself then choose that else take id  from wiki api
                #     wikipedia_id = i["wiki_id"]
                # elif wiki_id:
                #     wikipedia_id = wiki_id
                # else:
                #     wikipedia_id = None
                similarity = similarity_check(name_copy1, google_place_name)

                # The following checking determines if trip advisor name matches with gooogle name
                #If so give preference to google deatils else give priority to trip advisor details
                if similarity >= 0.8 and km < 5:  #priority to google details
                    name = google_place_name
                    #Rounding coordinates decimals to limit 5
                    latitude = round(float(google_place_details["google_latitude"]), 5)
                    longitude = round(float(google_place_details["google_longitude"]), 5)
                    email = i["email"]
                    web = google_place_details["google_website"]
                    # Exclude types from Google - point_of_interest and establishment
                    try:
                        types = google_place_details["google_type"]
                    except:
                        # Jump to next place in iteration, if no associated types
                        types = []
                    print types,"aaaaaaaaaaaaaaaaaaaaaa",google_place_details["google_type"],google_place_details["google_type"][:-2]
                    # If no types from Google (other than point_of_interest and establishment)
                    # if len(types)==0:
                    #     types=i["category"]

                    telephone = google_place_details["google_phone"] \
                        if google_place_details["google_phone"] is not None else i["phone"]
                    address = google_place_details["google_address"] \
                        if google_place_details["google_address"] is not None else i["address"]
                    score_count = 0
                    composite_score = 0
                    if yelp_details["yelp_rating"] is not None:
                        composite_score += float(yelp_details["yelp_rating"])
                        score_count += 1
                    if google_place_details["google_rating"] is not None:
                        composite_score += float(google_place_details["google_rating"])
                        score_count += 1
                    if i["rating"]:
                        composite_score += float(i["rating"])
                        score_count += 1
                    if foursquare_details["foursquare_rating"] is not None:
                        if foursquare_details["foursquare_rating"] != 'nul':
                            composite_score += (float(str(foursquare_details["foursquare_rating"]))) / 2
                            score_count += 1
                    composite_score = round(float(composite_score / score_count), 1) if score_count else 0
                    thirdparty_ids = {"wikipedia": wikipedia_id, "google": google_place_details["google_place_id"],
                                      "yelp": yelp_details["yelp_id"], "facebook": foursquare_details["facebook_id"],
                                      "foursquare": foursquare_details["foursquare_id"], 'fiz': None,
                                      "flickr": flickr_details['flickr_id']}
                    # thirdparty_ratings={"google_rating":google_place_details["google_rating"],
                    # "foursquare_rating":foursquare_details["foursquare_rating"],
                    # "ta_rating":i["rating"],"yelp":yelp_details["yelp_rating"]}

                else:  # priority to trip advisor details
                    name = i["name"]
                    #Rounding coordinates decimals to limit 5
                    latitude = round(float(i["latitude"]), 5)
                    longitude = round(float(i["longitude"]), 5)
                    email = i["email"]
                    web = i["website"]
                    types = i["category"]
                    telephone = i["phone"]
                    address = i["address"]
                    score_count = 0
                    composite_score = 0
                    if yelp_details["yelp_rating"] is not None:
                        composite_score += float(yelp_details["yelp_rating"])
                        score_count += 1
                    if foursquare_details["foursquare_rating"] is not None:
                        composite_score += (float(foursquare_details["foursquare_rating"])) / 2
                        score_count += 1
                    if i["rating"]:
                        composite_score += float(i["rating"])
                        score_count += 1

                    composite_score = round(float(composite_score / score_count), 1) if score_count else 0
                    thirdparty_ids = {"wikipedia": wikipedia_id, "facebook": foursquare_details["facebook_id"],
                                      "yelp": yelp_details["yelp_id"],
                                      "foursquare": foursquare_details["foursquare_id"], 'fiz': None,
                                      "flickr": flickr_details['flickr_id']}
                    # thirdparty_ratings={"foursquare_rating":foursquare_details["foursquare_rating"],
                    # "ta_rating":i["rating"],"yelp":yelp_details["yelp_rating"]}
                print composite_score, "Composite Score########################"
                if composite_score == 0:
                    composite_score = None
                if len(types) > 0:
                    lat_lng = [{'latitude': i['latitude'], 'longitude':i['longitude']} for i in scraped_data_list]
                    new_ll = {'latitude': latitude, 'longitude': longitude}
                    if new_ll not in lat_lng:
                        scraped_data_list.append(
                            {'name': name, 'latitude': latitude, 'longitude': longitude, 'email': email,
                             'telephone': telephone, 'address': address, 'thirdparty_ids': thirdparty_ids,
                             'composite_score': composite_score, "types": types, "web": web})
        return scraped_data_list

    def tripadvisor_place_id(self, place):
        """
        Find trip advisor place_Id
        """
        try:
            api = str('https://api.tripadvisor.com/api/internal/1.10/typeahead?auto_broaden=true&'
                      'category_type=neighborhoods%2Cgeos&currency=IN%20R&default_options=overview'
                      '%2Clodging%2Cthings_to_do%2Crestaurants%2Cflights_to%2Cneighborhoods&lang=en_IN'
                      '&query=' + place + '&key=' + settings.MP_TRIPADVISOR_API_KEY)
            tag = json_tag(api)
            temp = tag["data"]
            place_name = ""
            place_selector_list = []
            count = 0
            for i in temp:
                temp1 = i["result_object"]
                location_string = temp1["location_string"]
                temp1 = temp1["ancestors"]
                for j in temp1:
                    if place_name == "":
                        place_name = place_name + str(j["name"])
                    else:
                        place_name = place_name + "," + str(j["name"])
                place_name_copy = place_name
                place_name = ""
                temp4 = i["result_object"]
                place_id = temp4["location_id"]

                if place_name_copy != "":
                    place_selector = {"place_name": str(location_string) + "[" + str(place_name_copy) + "]",
                                      "place_id": str(place_id),
                                      "key": count}
                    place_selector_list.append(place_selector)
                    count += 1
            return place_selector_list
        except Exception as e:
            print "MP - Error fetching TripAdvisor Place ID: ", e
            return []

    def get_categories(self, place_id):
        """
        Find attraction categories of a place
        """
        category_list = []
        api = ('https://api.tripadvisor.com/api/internal/1.10/location/' + place_id +
               '/attractions?limit=50&sort=popularity&show_filters=true&subcategory=0&'
               'subtype=0&include_rollups=true&neighborhood=all&dieroll=9&offset=0&'
               'lang=en_US&currency=USD&key=' + settings.MP_TRIPADVISOR_API_KEY)
        tag = json_tag(api)
        temp = tag["filters"]
        temp = temp["subcategory"]
        for i in temp:
            temp1 = temp[i]
            category_list.append({"key": i, "name": temp1["label"], "count": temp1["count"]})
        return category_list

    def get_subcategories(self, place_id, category_choice):
        """
        Find attraction sub-categories of a place
        """
        subcategory_list = []
        api = ('https://api.tripadvisor.com/api/internal/1.10/location/' + place_id +
               '/attractions?limit=50&sort=popularity&show_filters=true&subcategory=0&'
               'subtype=0&include_rollups=true&neighborhood=all&dieroll=9&offset=0&'
               'lang=en_US&currency=USD&key=' + settings.MP_TRIPADVISOR_API_KEY)
        tag = json_tag(api)
        temp = tag["filters"]
        temp = temp["subtype"]
        total_count = 0
        for i in temp:
            subcategory_id = i
            temp1 = temp[i]
            if "parent_id" in temp1:
                if temp1["parent_id"] == category_choice:
                    total_count += int(temp1["count"])
                    subcategory_list.append({"key": subcategory_id, "name": temp1["label"], "count": temp1["count"]})
        subcategory_list.append({"key": "0", "name": "All", "count": total_count})
        return subcategory_list

    def tripadvisor_total_thingstodo(self, place_id):
        """
        Find number of total attractions  place
        """
        try:
            api = str('https://api.tripadvisor.com/api/internal/1.10/location/' + place_id +
                      '/attractions?limit=30&sort=popularity&show_filters=true&include_rollups=true&'
                      'dieroll=9&lang=en_US&currency=USD&key=' + settings.MP_TRIPADVISOR_API_KEY)
            tag = json_tag(api)
            temp = tag["data"]
            temp = temp[0]
            total_things_to_do = temp["ranking_denominator"]
            return total_things_to_do
        except Exception as e:
            print "MP - Error fetching TripAdvisor (Things to do): ", e
            return None

    def tripadvisor_all(self, place_id, total, category_choice, subcategory_choice, limit):
        """
         Find all attractions of place
        """
        try:
            offset = 0
            place_list = []
            if total != None:
                n = total // 50  # If limit not given
            else:
                n = limit // 50  # If limit given
            n += 1

            # For each iteration trip advisor api returns 50 results
            #n determines no of iterations needed
            for k in range(0, n):
                api = str('https://api.tripadvisor.com/api/internal/1.10/location/' + str(place_id) +
                          '/attractions?limit=50&sort=popularity&show_filters=true&subcategory=' + str(
                          category_choice) + '&subtype=' + str(
                          subcategory_choice) + '&include_rollups=true&neighborhood=all&dieroll=9&offset=' + str(
                          offset) + '&lang=en_US&currency=USD&key=' + settings.MP_TRIPADVISOR_API_KEY)
                tag = requests.get(api)
                tag = json.loads(tag.text)
                print api, 'api_url###'
                temp = tag["data"]
                place_list = self.tripadvisor_details(temp, place_list)  # Find details of all 50 places
                offset = int(offset)
                offset += 50
            return place_list
        except Exception as e:
            print "MP - Error fetching TripAdvisor attractions: ", e
            raise

    def tripadvisor_details(self, temp, place_list):
        """
        Find tripadvisor details of a single place name
        """
        for i in temp:
            if i["location_id"] != "0":
                name = i["name"] if 'name' in i else None
                latitude = i["latitude"] if 'latitude' in i else None
                longitude = i["longitude"] if 'longitude' in i else None
                address = i["address"] if 'address' in i else None
                rating = i["rating"] if 'rating' in i else None
                email = i["email"] if 'email' in i else None
                phone = i["phone"] if 'phone' in i else None
                website = i["website"] if 'website' in i else None
                if 'wikipedia_info' in i:
                    wikipedia_info = i['wikipedia_info']
                    wiki_id = wikipedia_info['pageid']
                    wiki_url = wikipedia_info['url']
                else:
                    wiki_id = None
                    wiki_url = None
                category_types = []
                for categories in (i['subcategory']):
                    category_types.append(categories["name"])
                dictionary = {
                    'name': name, 'category': category_types, 'ta_id': i["location_id"], 'latitude': latitude,
                    'longitude': longitude, 'rating': rating, 'address': address, 'email': email,
                    'phone': phone, 'website': website, 'wiki_id': wiki_id, 'wiki_url': wiki_url
                }
                place_list.append(dictionary)
        return place_list

    def google_places(self, google_place_name, original_place):
        """
        Find google details of a place
        Google place api returns many place names depending upon query name
        We will find the best matching name from google place names with tripadvisor name
        Here original_place is tripadvisor place name and google_place_name is tripadvisor name appended with location
        Ex. 'British museum' is original_place and 'British Museum London' is google_place_name
        """
        print "\n\n\n\n\n google placesssssss", google_place_name, "google place nameee", original_place, "original placeeeeeee"
        try:

            api = str(
                'https://maps.googleapis.com/maps/api/place/textsearch/json?&query=' + google_place_name + '&key=' + settings.MP_GOOGLE_TOKEN)
            tag = json_tag(api)
            if 'results' in tag:
                temp = tag["results"]
                max_similarity = 0
                id_max = None
                for idx, i in enumerate(temp):
                    similarity = similarity_check(original_place, i["name"])
                    if similarity > max_similarity:
                        max_similarity = similarity
                        id_max = idx
                temp = temp[id_max]

            else:
                temp = tag["result"]

            # Find google place id
            place_id = temp["place_id"]
            time.sleep(2)

            # Then use google place id to find all details of that place
            api = str(
                'https://maps.googleapis.com/maps/api/place/details/json?placeid=' + place_id +
                '&key=' + settings.MP_GOOGLE_TOKEN)
            tag = json_tag(api)
            if 'result' in tag:
                temp = tag["result"]
            elif 'results' in tag:
                temp = tag["result"]
                temp = temp[0]
            type = temp["types"] if 'types' in temp else None
            rating = temp["rating"] if 'rating' in temp else None
            name = temp["name"]
            address = temp["formatted_address"]
            phone = temp["formatted_phone_number"] if 'formatted_phone_number' in temp else None
            website = temp["website"] if 'website' in temp else None
            url = temp["url"] if 'url' in temp else None
            temp = temp["geometry"]
            temp = temp["location"]
            latitude = temp["lat"]
            longitude = temp["lng"]
            google_place_details = {
                'google_name': name, 'google_place_id': place_id, 'google_latitude': latitude,
                'google_longitude': longitude, 'google_address': address, 'google_type': type,
                'google_rating': rating, 'google_website': website, 'google_phone': phone,
                'google_maps_url': url
            }
            return google_place_details
        except Exception as e:
            print "MP - Error fetching Google places: ", e

    def foursquare(self, place, latitude, longitude):
        """
        To find foursquare details of a palce
        """
        try:
            # First find foursqaure id of place
            api = str('https://api.foursquare.com/v2/venues/search?client_id=' +
                      settings.MP_FOURSQUARE_CLIENT_ID + '&client_secret=' +
                      settings.MP_FOURSQUARE_CLIENT_SECRET + '&v=20130815&ll=' +
                      latitude + ',' + longitude + '&query=' + place + '')
            print api, "foursqure_api222###"
            tag = json_tag(api)
            temp = tag['response']
            if temp:
                temp = temp.get("venues")[:5]
                max_similarity = 0
                id_max = None
                for idx, i in enumerate(temp):
                    similarity = similarity_check(place, i["name"])
                    if similarity > max_similarity:
                        max_similarity = similarity
                        id_max = idx
                if max_similarity > 0.8:
                    foursquare_id = temp[id_max]['id']
                    print foursquare_id,":::::::::::::::::::::;"
                    #Then using foursqaure_id find rest details such as facebook id,twitter url,rating etc
                    api = str(
                        'https://api.foursquare.com/v2/venues/' + foursquare_id +
                        '?oauth_token=' + settings.MP_FOURSQUARE_TOKEN + '&v=20160701')
                    tag = json_tag(api)
                    temp = tag['response']
                    temp = temp["venue"]
                    foursquare_rating = temp["rating"] if 'rating' in temp else None
                    foursquare_url = temp["canonicalUrl"]

                    temp = temp["contact"]
                    facebook_id = temp["facebook"] if 'facebook' in temp else None
                    if 'twitter' in temp:
                        twitter_url = str(temp["twitter"])
                        twitter_url = "https://twitter.com/" + twitter_url
                    else:
                        twitter_url = None
                    valid_url = URLValidator()
                    try:
                        valid_url(twitter_url)
                    except ValidationError, e:
                        print e
                        twitter_url = None
                    foursquare_details = {'foursquare_id': foursquare_id, 'foursquare_rating': foursquare_rating,
                                          'foursquare_url': foursquare_url, 'facebook_id': facebook_id,
                                          'twitter_url': twitter_url}
                else:
                    foursquare_details = {'foursquare_id': None, 'foursquare_rating': None, 'foursquare_url': None,
                                          'facebook_id': None, 'twitter_url': None}
            else:
                foursquare_details = {'foursquare_id': None, 'foursquare_rating': None, 'foursquare_url': None,
                                          'facebook_id': None, 'twitter_url': None}
            return foursquare_details

        except Exception as e:
            print "MP - Error fetching Foursquare: ", e
            foursquare_details = {'foursquare_id': None, 'foursquare_rating': None, 'foursquare_url': None,
                                  'facebook_id': None, 'twitter_url': None}
            return foursquare_details

    def wiki(self, place):
        """
        To find wikipedia id of place
        """
        try:
            place = place.replace(" ", "%20").encode('utf-8')
            api = str('https://en.wikipedia.org/w/api.php?format=json&action=query&prop=extracts&'
                      'exintro=&explaintext=&titles=' + str(place) + '')
            tag = json_tag(api)
            temp = tag["query"]
            temp = temp["pages"]
            wiki_id = temp.keys()[0]
            if wiki_id == "-1":
                wiki_id = None
            return wiki_id
        except Exception as e:
            print "MP - Error fetching Wiki: ", e
            return None

    def yelp(self, place_name, location, latitude, longitude):
        """
        To get yelp id of place.
        Location should be also specified along with place name
        For example place name is british museum and loaction is london
        """
        try:
            print settings.MP_YELP_TOKEN_SECRET, "Yelp token"
            # auth = Oauth1Authenticator(
            #     consumer_key=settings.MP_YELP_CONSUMER_KEY,
            #     consumer_secret=settings.MP_YELP_CONSUMER_SECRET,
            #     token=settings.MP_YELP_TOKEN,
            #     token_secret=settings.MP_YELP_TOKEN_SECRET
            # )
            auth = Oauth1Authenticator(
                consumer_key="YVjUh5SDw2vSgm-ybAuZdQ",
                consumer_secret="OPbnaGVaHDJYS1MLcqD-AKF6jRM",
                token="Zcyqrmrv14PqqzHtJQrQZMWTpY4EBGnf",
                token_secret="RRbLsOc1VTz7bdtbqMw8pFpZ3sE"
            )
            print auth,"---------------"

            class CustClient(Client):
                def _make_connection(self, signed_url):
                    try:
                        print signed_url, 'signed_url###'
                        conn = six.moves.urllib.request.urlopen(signed_url, None)
                    except six.moves.urllib.error.HTTPError as error:
                        self._error_handler.raise_error(error)
                    else:
                        try:
                            response = json.loads(conn.read().decode('UTF-8'))
                        finally:
                            conn.close()
                        temp = response["businesses"][:5]
                        max_similarity = 0
                        id_max = None
                        for idx, i in enumerate(temp):
                            similarity = similarity_check(place_name, i["name"])
                            if similarity > max_similarity:
                                max_similarity = similarity
                                id_max = idx
                        # print max_similarity, temp[id_max]["name"]
                        global yelp_id
                        global yelp_rating
                        yelp_id = None
                        yelp_rating = None
                        print temp, "Response from Yelp"
                        km = cord_diff(float(longitude), float(latitude),
                                       float(temp[id_max]['location']['coordinate']['longitude']),
                                       float(temp[id_max]['location']['coordinate']['latitude']))
                        if max_similarity > 0.8 and km < 5:
                            yelp_id = temp[id_max]["id"]
                            yelp_rating = temp[id_max]["rating"]
                        return yelp_id

            client = CustClient(auth)
            params = {
                'term': '' + place_name + '',
                'cll': '' + latitude + ',' + longitude + ''
            }
            client.search('' + location + '', **params)
            yelp_details = {'yelp_id': yelp_id, 'yelp_rating': yelp_rating}
            return yelp_details
        except Exception as e:
            print "MP - Error fetching Yelp: ", e
            yelp_details = {'yelp_id': None, 'yelp_rating': None}
            return yelp_details

    def flickr(self, place, latitude, longitude):
        """
        To find flickr details of a place
        """
        print 'Inside Flickr...',
        print 'MP_FLICKR_PUBLIC', settings.MP_FLICKR_PUBLIC
        print 'MP_FLICKR_PUBLIC Type..', type(settings.MP_FLICKR_PUBLIC)
        try:
            # First find flickr id of place
            # flickr = FlickrAPI(settings.MP_FLICKR_PUBLIC, settings.MP_FLICKR_SECRET, format='parsed-json')
            flickr = FlickrAPI('c30ddbd565c3b40c31c11ecbe1330407', '2b7261ccf9acc42c', format='parsed-json')
            print flickr, "flickr###"
            place_data = flickr.places.find(query=place)
            total_places = place_data['places']['place']

            if total_places:
                coordinates = []
                for count, place in enumerate(total_places):
                    coordinates.append([place['latitude'], place['longitude'], place['place_id']])

                radius = 1.00  # in kilometer
                flickr_details = {}
                for i, j, k in coordinates:
                    a = self.parse_distance(float(longitude), float(latitude), float(j), float(i))
                    print('Distance (km) : ', a)
                    if a <= radius:
                        print('Inside the area:******', i, j, k)
                        flickr_details = {'flickr_id': k}
                    else:
                        print('Outside the area:.....')
                        flickr_details = {'flickr_id': None}
            else:
                flickr_details = {'flickr_id': None}
            return flickr_details

        except Exception as e:
            print "MP - Error fetching Flickr: ", e
            flickr_details = {'flickr_id': None}
            return flickr_details

    def parse_distance(self, lon1, lat1, lon2, lat2):
        """
        Calculate the great circle distance between two points
        on the earth (specified in decimal degrees)
        """
        # approximate radius of earth in km
        earth_radius = 6373.0

        print 'Coordinates from fiz :\t', lat1, '\t', lon1, '\n'
        print 'Coordinates from flickr :\t', lat2, '\t', lon2, '\n'

        lat1 = radians(lat1)
        lon1 = radians(lon1)
        lat2 = radians(lat2)
        lon2 = radians(lon2)

        lon_difference = lon2 - lon1
        lat_difference = lat2 - lat1

        a = sin(lat_difference / 2)**2 + cos(lat1) * cos(lat2) * sin(lon_difference / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        distance = earth_radius * c
        return distance


def json_tag(api):
    """
    to get json response of api
    """
    r = requests.get(api)
    tag = json.loads(r.content.decode('utf8'))
    return tag


def convert(data):
    """
    To eliminate unicode tagging
    """
    if isinstance(data, basestring):
        return str(data)
    elif isinstance(data, collections.Mapping):
        return dict(map(convert, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(convert, data))
    else:
        return data


def similarity_check(place1, place2):
    """
    To find similarity between two place names by removing stop words.
    Similarity is in range 0 to 1. If similarity is 1 then perfect match b/w place names.
    """
    stop_words = ['the', '&', 'and', 'of', 'at']
    place1 = re.sub("[^A-Za-z0-9'.]", " ", place1)
    place2 = re.sub("[^A-Za-z0-9'.]", " ", place2)
    place1 = place1.lower()
    place2 = place2.lower()
    place1 = place1.split()
    place2 = place2.split()
    for i in place1:
        if i in stop_words:
            place1.remove(i)
    place1 = " ".join(place1)
    for i in place2:
        if i in stop_words:
            place2.remove(i)
    place2 = " ".join(place2)
    similarity = difflib.SequenceMatcher(a=str(place1), b=str(place2))
    similarity = similarity.ratio()
    return similarity


def cord_diff(lon1, lat1, lon2, lat2):
        """
        Find kilometer difference between coordinates of two locations
        """
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        km = 6367 * c
        return km