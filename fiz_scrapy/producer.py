import json
from boto3 import client
import time
from fiz_scrapy import settings


class Publisher(object):
    """
        Publish : Publisher Module To Kafka Server With Fiz Protocols.
    """
    POPULATE = 'populate'
    MISSING = 'missing'
    SCORING = 'scoring'

    def __init__(self, shub_unit_id, request_type, job_id=None, index=1,
                 key=None, topic=None):

        self.topic = "topic__%d" % shub_unit_id if topic is None else topic
        self.stream = client(
            'kinesis',
            region_name=settings.AWS_KINESIS_REGION,
            aws_access_key_id=settings.AWS_KINESIS_ACCESS_ID,
            aws_secret_access_key=settings.AWS_KINESIS_SECRET_ACCESS_KEY,
            use_ssl=True,
        )
        self.shub_unit_id = str(shub_unit_id)
        self.job_id = str(job_id) if job_id else None
        self._key = 'fiz_stream_data'
        self._close = False
        self.close_timeout = 1
        self.type = request_type
        self.next_block = False if index == 1 else True

        '''
        next_block : if the main area is splited into different subareas (in case area is larger),
                 do not release the instance until all the areas are processed.
                 if there are 'n' sub areas ( n=1 if there is no sub area), then first subplace will have index n, then n-1, n-2 
                 until n became 1.
                 after processing n=1, on spider close, the instance is released
        '''

    def setkey(self, key):
        self._key = key

    def __set_to_protocol(self, data):
        """ APPEND DATA INTO PROTOCOL AND SEND"""
        # import pdb;pdb.set_trace()
        return json.dumps({
            'shub_unit_id': self.shub_unit_id,
            'job_id': self.job_id,
            'type': self.type,
            'next': True,
            'mydata': data,
            'error': False,
            })

    def __release_message(self):
        """ DATA APPENDED WITH PROTOCOL"""
        print(" Next: block %s" % self.next_block)
        return json.dumps({
            'shub_unit_id': self.shub_unit_id,
            'job_id': self.job_id,
            'type': self.type,
            'next': self.next_block,
            'mydata': None,
            'error': False,

            })

    def __terminate_message(self):
        """ RETURN FAILED MESSAGE PROTOCOL"""
        return json.dumps({
            'shub_unit_id': self.shub_unit_id,
            'job_id': self.job_id,
            'type': self.type,
            'next': False,
            'mydata': None,
            'error': True,
        })

    def __add_metadata(self, data):
        """ FORMAT DATA TO GET SAVED FOR AWS STREAM"""
        return [{
                'Data': b'%s' % self.__set_to_protocol(item),
                'PartitionKey': 'fiz_stream_data',
                } for item in data]

    def push(self, data):
        formatted_data = self.__set_to_protocol(data)
        self.write(topic=b"%s" % self.topic,
                   value=b"%s" % formatted_data,
                   key=b"%s" % self._key)

    def push_list(self, value):
        if value:       # vulnerable to Null list.
            size = 10
            value = [value[i:i+size] for i in range(0, len(value), size)]
            for chunk in value:
                print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
                print(self.__add_metadata(chunk))
                self.stream.put_records(Records=self.__add_metadata(chunk), StreamName=self.topic)
                time.sleep(1)

    def pclose(self, force=False):
        release_message = self.__terminate_message() if force else self.__release_message()
        # self.write(topic=self.topic, value=release_message, key=self._key)
        self.stream.put_record(
            StreamName=self.topic,
            Data=release_message,
            PartitionKey=self._key,
            ExplicitHashKey='0',
            SequenceNumberForOrdering='0',
        )
        self._close = True

    def write(self, topic, value, key=None):
        topic = self.topic if topic is None else topic
        if topic is None:
            topic = self.topic
        self.stream.put_record(
            StreamName=topic,
            Data=self.__set_to_protocol(value),
            PartitionKey=self._key,
            ExplicitHashKey='0',
            SequenceNumberForOrdering='0',
        )

    @classmethod
    def send_mail_urgantly(cls, error):
        pass


if __name__ == '__main__':

    p = Publisher(8945, request_type=Publisher.POPULATE, job_id=20, topic="topic__283086")
    # p.push({"next": "value -- ", 'data': [1, 2, 3, 4]})
    p.push_list([{'web': None, 'name': u'Pettorano Sul Gizio', 'provider_url': None, 'place_details': [{'provider_url': u'https://maps.google.com/?q=67034+Pettorano+Sul+Gizio+AQ,+Italy&ftid=0x13306aff42dcc9a5:0xfa55f4cfd01bc02f', 'opening_times': {}, 'name': u'Pettorano Sul Gizio', 'rating': None, 'pictures': [{'url': 'https://maps.googleapis.com/maps/api/place/photo?maxwidth=5529&maxheight=2894&photoreference=CmRaAAAAuMKzJWMidrR0XmQI3U0nrjtAQ2OPKGPZItyV7y5xZK_7dkra9F4MxsYXGsvixgXwi9hYBmqDE4lX8y0tEdwh4hi2NyTEL9gQwtqJG1smMxTS5tn44_h-7C1UoEJ_q4tlEhAAw8p4S4HZYYfrrVxULJlIGhRgAbn3Vj0Hi1nqgOl6ru4KP9yT0A&key=AIzaSyCa4lazz3Qj0NZuCT0iUSzcv5W3zJ1X60I', 'html_attributions': [u'<a href="https://maps.google.com/maps/contrib/108637223408036165197/photos">Mireille Marignac-Vinais</a>'], 'provider': 'google'}, {'url': 'https://maps.googleapis.com/maps/api/place/photo?maxwidth=1024&maxheight=768&photoreference=CmRaAAAAk9ftTvRLdoQU1Xk11el7lVNZ_Up-DkRu_ivX6edOpGzNdV1KZbKIoJAC8N0Mzb9HVUWzUtYIXQnot1y0ecIFWpGqkE39IuzKgMjPf-09VbUMa_aQTJn-MFy2HYjN3qoFEhDmTYWSD_wQqi5dWbgfyN9VGhQuT9_0PAKf_ImRcS-X28TlnDQJ5A&key=AIzaSyCa4lazz3Qj0NZuCT0iUSzcv5W3zJ1X60I', 'html_attributions': [u'<a href="https://maps.google.com/maps/contrib/100332014731456126053/photos">leonardo mazzeschi</a>'], 'provider': 'google'}, {'url': 'https://maps.googleapis.com/maps/api/place/photo?maxwidth=3072&maxheight=4096&photoreference=CmRaAAAAftsKjqQmmHKPwOoAutfTYW_v7FSdSydzAIR-DmcOr7o1Xupd2wrpgMlyEvnHUSpxw6XLLUpgF0Rw3exfdkAL7L4N-sYSFmJap6kdpmK8jlULC0lVfrzCHkFxPtwekAkJEhCVTC8taphsfXtRxrII5RCFGhRwTECbGHsuQGlw3xgqqlSyQZK6Lg&key=AIzaSyCa4lazz3Qj0NZuCT0iUSzcv5W3zJ1X60I', 'html_attributions': [u'<a href="https://maps.google.com/maps/contrib/117877707658773329981/photos">Elena Cagnazzo</a>'], 'provider': 'google'}, {'url': 'https://maps.googleapis.com/maps/api/place/photo?maxwidth=3072&maxheight=4096&photoreference=CmRaAAAARa-2KDxn3y3SahLajLPPHHi9oUDVUhmEQ8V1j6CQUWMOnkDRczoXpTBrtDFDq-UtQIYkfwb7Q29Gj4Xwexld1GZb2Z5aWpIM2Iw-5dCBpTZ9PSHVle5llA9f2aoxhO1QEhAx6mpctWKwZx5TWGly3hZIGhSQrNG8GiKv4GHP5fiPH5Nh6sdDDw&key=AIzaSyCa4lazz3Qj0NZuCT0iUSzcv5W3zJ1X60I', 'html_attributions': [u'<a href="https://maps.google.com/maps/contrib/117877707658773329981/photos">Elena Cagnazzo</a>'], 'provider': 'google'}, {'url': 'https://maps.googleapis.com/maps/api/place/photo?maxwidth=4896&maxheight=3264&photoreference=CmRaAAAAAQUX7GHTfhzxTuF3qs5-GzX6kl125WZaRLoJVCP_mYRNRIklbgxzkGSj_YSGGXBL-NNv5NqhICcBokfEnmx8Vh-bUn62UIh9a5sH24GuMxauJzKKHTfjxMRPrZe53is2EhBjxKyPGdYPrRyaIJ7WaeEFGhQuJtddbArAeiTUJt5jH8kV1cniqQ&key=AIzaSyCa4lazz3Qj0NZuCT0iUSzcv5W3zJ1X60I', 'html_attributions': [u'<a href="https://maps.google.com/maps/contrib/110420360645728453546/photos">Giuseppe D&#39;Antonio</a>'], 'provider': 'google'}, {'url': 'https://maps.googleapis.com/maps/api/place/photo?maxwidth=1024&maxheight=768&photoreference=CmRaAAAADFW_6QTLS48UBEZ2keliC1T3AM28MChRwsUI0jZ5Hi0fuXrKonNyfEWtsHXpeFOGjtgDmM3uX56uf0B040Q1PODaW25g-u1lfTl6hua89CJs7wZRptTqW3rzaMvpmb1zEhDGEXLReZ8UHt5i7zb2QA74GhRLkt0YropnZQxxFtXHO-qt9AXDJA&key=AIzaSyCa4lazz3Qj0NZuCT0iUSzcv5W3zJ1X60I', 'html_attributions': [u'<a href="https://maps.google.com/maps/contrib/100332014731456126053/photos">leonardo mazzeschi</a>'], 'provider': 'google'}], 'lon': 13.9586133, 'reviews': None, 'phone': '', 'third_party_provider': 'google', 'third_party_id': u'ChIJpcncQv9qMBMRL8Ab0M_0Vfo', 'address': u'67034 Pettorano Sul Gizio AQ, Italy', 'lat': 41.9756728, 'ref': u'CmRbAAAAfkNfvQx1DKf5E6Ph2HHf9OAzV_h03CB_2_60we__1USVOH0r7XGEvLyUFqrc7kh69IhzbhXm0Mn4Ur3O7_rtyBCOKreDQwCqRFhTKUmQh0RfhTvDpKP03eYArlNTKVIzEhDBEwBp7hcmP7b4fXoFcCR2GhSIOnATGC7Z0IR3gulnGDW699QWiw', 'types': [u'locality', u'political']}], 'lon': 13.9586133, 'phone': None, 'third_party_provider': 'google', 'third_party_id': u'ChIJpcncQv9qMBMRL8Ab0M_0Vfo', 'lat': 41.9756728, 'types': [u'locality', u'political']}] )
    p.pclose()
