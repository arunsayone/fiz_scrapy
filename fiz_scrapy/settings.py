
# -*- coding: utf-8 -*-

# Scrapy settings for fiz_scrapy project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'fiz_scrapy'

SPIDER_MODULES = ['fiz_scrapy.spiders']
NEWSPIDER_MODULE = 'fiz_scrapy.spiders'


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'fiz_scrapy (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See http://scrapy.readthedocs.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'fiz_scrapy.middlewares.FizScrapySpiderMiddleware': 543,
#}

# Enable or disable downloader middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    'fiz_scrapy.middlewares.MyCustomDownloaderMiddleware': 543,
#}

# Enable or disable extensions
# See http://scrapy.readthedocs.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See http://scrapy.readthedocs.org/en/latest/topics/item-pipeline.html
# ITEM_PIPELINES = {
#    'fiz_scrapy.pipelines.FizScrapyPipeline': 300,
# }

# Enable and configure the AutoThrottle extension (disabled by default)
# See http://doc.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# Max distance for located places queries
MAX_NEARBY_DISTANCE = 50000  # in metres for query
# MAX_REQUESTS_PER_PROVIDER = int(os.getenv('MAX_REQUESTS_PER_PROVIDER', 1))
MAX_REQUESTS_PER_PROVIDER = 4

# DATABASE = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'NAME': 'aggregator',
#         'USER': 'aggregator',
#         'PASSWORD': 'aggregator',
#         'HOST': 'localhost',
#         'PORT': '',
#     }
# }

# DATABASE = {
#     # 'drivername': 'postgres',
#     # 'drivername': 'django.contrib.gis.db.backends.postgis',
#     'drivername': 'postgresql+psycopg2',
#     'host': '127.0.0.1',
#     'port': '5432',
#     'username': 'fizdbuser',
#     'password': 'password',
#     'database': 'backend_fiz'
# }

MP_TRIPADVISOR_API_KEY = 'ce957ab2-0385-40f2-a32d-ed80296ff67f'

# MP_FOURSQUARE_CLIENT_ID = 'CQDHTXVVBGM2SJCYII4U1TZI4R1CTVWJKZFR2V2V0TJVCQVK'
# MP_FOURSQUARE_SECRET_KEY = '5PLYFVLAUZJONHBYT5UTB1NB033T3C4IDT0YS1CDFDYCTKDL'
MP_FOURSQUARE_TOKEN = 'FSPDCIO01QXGKI1ZYN5YMQ0BVYH2ACO2NKAJZ00YIZBZ5K4B'

MP_FOURSQUARE_CLIENT_ID = '2B1ZHUCVWDVBTZNKQYWWQCW4R0CREAU2H3SD41FXXZ22NK0I'
MP_FOURSQUARE_CLIENT_SECRET = 'FXVJZC1V3OT4NTBR0EIQH4LXCKICMLO2UCC02X15NNRS3XKU'
MP_FOURSQUARE_VERSION = '20120801'

MP_YELP_APP_ID = '5UU07imB02-qFShOI_o29Q'
MP_YELP_APP_SECRET = 'VF920BvJJezVzJL50AWQ8bIzelbuYP5zmdfRA5DJvutTJX2pe5VeKLlQnVBAAbkw'
MP_YELP_ACCESS_TOKEN = '__0s51ciQHJ6RBKwg5OrU6kP9kVWPmspkNFrFJTAhrUoxgT1gvxhrXhkAAnUqrRNUolAD65aB3M_3KXFFdfaQja3yME1QwqnCu_-dFwG8zy1cQULmJ_wIg8rBKw3WnYx'

MP_YELP_CONSUMER_KEY = 'YVjUh5SDw2vSgm-ybAuZdQ'
MP_YELP_CONSUMER_SECRET = 'OPbnaGVaHDJYS1MLcqD-AKF6jRM'
MP_YELP_TOKEN = 'Zcyqrmrv14PqqzHtJQrQZMWTpY4EBGnf'
MP_YELP_TOKEN_SECRET = 'RRbLsOc1VTz7bdtbqMw8pFpZ3sE'

MP_GOOGLE_TOKEN = 'AIzaSyCa4lazz3Qj0NZuCT0iUSzcv5W3zJ1X60I'

MP_FLICKR_PUBLIC = 'c30ddbd565c3b40c31c11ecbe1330407'
MP_FLICKR_SECRET = '2b7261ccf9acc42c'

MP_PANORAMAIO_BASE_URL = 'http://www.panoramio.com/map/get_panoramas.php'

MP_EVENTFULL_APP_KEY = 'sHpKc2Q8fJwm6L37'
MP_EVENTFULL_BASE_URL = 'http://api.eventful.com/json/'

MP_INSTAGRAM_ACCESS_TOKEN = '1972706512.42ba383.cb453d7e3d7540c990f25f59c2880fe5'
MP_INSTAGRAM_BASE_URL = 'https://api.instagram.com/v1'
MP_INSTAGRAM_CLIENT_ID = '42ba38307bb34d27a13f18b3bb5991d9'
MP_INSTAGRAM_CLIENT_SECRET = 'a061cdd508e845b2bcd71c00859fe4c5'

MP_WIKIPEDIA_BASE_URL = 'https://en.wikipedia.org/w/api.php'

MP_FACEBOOK_APP_ID = '273689706046055'
MP_FACEBOOK_APP_SECRET = 'eece2341cb5ef2a47cb914ce16604664'

# DEDUPER DISTANCES
DEDUPER_NEARBY_DISTANCE = 1000  # meters Used to test if places are the same



NEW_MP_FOURSQUARE_CLIENT_ID = 'OZP1Y4XFHRYEBOXT10ZF4UU21EUKB2QXFXW0YYQXXKBBXZVR'
NEW_MP_FOURSQUARE_CLIENT_SECRET = 'JMTDX4VO3OEAMGDGO5B4CXUDPM5K4APKC01LMWEHRRGQD35T'
NEW_MP_FOURSQUARE_VERSION = '20120801'

AWS_KINESIS_REGION = 'us-east-1'
AWS_KINESIS_ACCESS_ID = 'AKIAIW3E5REBN5UKKNZQ'
AWS_KINESIS_SECRET_ACCESS_KEY = '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'



