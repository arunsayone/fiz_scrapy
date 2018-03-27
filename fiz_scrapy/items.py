# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
import scrapy


class FizScrapyItem(scrapy.Item):
    # define the fields for your item here like:
    name = scrapy.Field()
    name = scrapy.Field()
    lat = scrapy.Field()
    lon = scrapy.Field()
    third_party_id = scrapy.Field()
    third_party_provider = scrapy.Field()
    types = scrapy.Field()

    # Optional fields
    address = scrapy.Field()
    web = scrapy.Field()
    phone = scrapy.Field()
    provider_url = scrapy.Field()
    twitter_url = scrapy.Field()
    eventful_event_count = scrapy.Field()

    # Facebook
    facebook_likes_count = scrapy.Field()
    facebook_checkins_count = scrapy.Field()
    facebook_were_here_count = scrapy.Field()
    facebook_talking_about_count = scrapy.Field()

    # Foursquare
    foursquare_checkins_count = scrapy.Field()
    foursquare_users_count = scrapy.Field()
    foursquare_tips_count = scrapy.Field()
    foursquare_here_now = scrapy.Field()

    # Related
    pictures = scrapy.Field()
    reviews = scrapy.Field()
    tips = scrapy.Field()

    # Optional
    description = scrapy.Field()
    rating = scrapy.Field()

    # TODO: Validate opening time segments
    opening_times = scrapy.Field()

    # Foursquare
    foursquare_likes_count = scrapy.Field()

    # Eventful
    events = scrapy.Field()

    #result
    result = scrapy.Field()
