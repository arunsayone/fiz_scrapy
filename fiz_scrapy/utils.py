import re
import logging
from unidecode import unidecode
from fiz_scrapy import settings

from math import sin, cos, sqrt, radians, asin
from requests.auth import HTTPBasicAuth
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.contrib.gis.geoip import GeoIP
from django.contrib import admin

from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils.html import strip_tags
from django.template.loader import render_to_string

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.automap import automap_base

logger = logging.getLogger(__name__)

Base = automap_base()

# engine, suppose it has two tables 'user' and 'address' set up
engine = create_engine(URL(**settings.DATABASE))

# reflect the tables
Base.prepare(engine, reflect=True)

session = Session(engine)

ThirdPartyOrigin = Base.classes.backend_thirdpartyorigin
FizPlace = Base.classes.backend_fizplace
Type = Base.classes.backend_type
Provider = Base.classes.backend_provider


def canonical_form(s):
    '''
    Returns the canonical representation of a given string, in the
    following way:
        * Make the string lower case
        * Multiple spaces will be removed
        * Use of the unidecode function to transform unicode characters into
          the most visually representative ASCII character.

    Example:
        'Fiz    Place ' -> 'fiz place'
    '''

    # Remove 'the' word at beginning
    new_string = re.sub(r'^the\s+', '', s.lower())
    # Remove multiple spaces
    new_string = re.sub(r'\s+', ' ', new_string)
    # Substitue '&' for 'and'
    new_string = new_string.replace('&', 'and')
    # Remove possessive forms 's and s' strings
    new_string = re.sub(r'\'s', '', new_string)
    new_string = re.sub(r's\'', 's', new_string)
    # Remove several symbols
    new_string = re.sub(r'[\'|?|!|$|*|:|;|.|,|%|#|@|(|)|/|\\]', '', new_string)

    # We need to pass unicode strings to `unidecode`
    if type(new_string) is not unicode:
        try:
            new_string = new_string.decode('utf8')
        except UnicodeDecodeError:
            return new_string.strip()

    return unidecode(
        new_string.strip()
    )


def get_or_none(classmodel, **kwargs):
    try:
        return classmodel.objects.get(**kwargs)
    except classmodel.DoesNotExist:
        return None


def remove_third_party_types():
    # Remove ALL third party Type relations where there is a Fiz type on a FizPlace.
    third_party_types = Type.objects.exclude(provider__name=Provider.FIZ)
    fizplaces = FizPlace.objects.filter(types__provider__name=Provider.FIZ).filter(
        types__in=third_party_types).distinct()
    for place in fizplaces:
        place.types.remove(*third_party_types)


def fiz_mail(to, subject, body, link=None, bcc=None, attachments=None, attachment_name=None,
             template=None, from_email=None):
    if bcc:
        bcc = [bcc]

    bcc = ['jibutest@gmail.com']

    if not template:
        template = 'common/email.html'

    if not attachment_name:
        attachment_name = 'Attachment.pdf'

    if not from_email:
        from_email = settings.EMAIL_FROM

    html = render_to_string(
        template,
        {
            'title': subject,
            'content': body,
            'link': link,
        }
    )

    plain = strip_tags(html)

    email = EmailMultiAlternatives(
        subject=subject,
        body=plain,
        from_email=from_email,
        to=[to],
        bcc=bcc
    )

    email.attach_alternative(html, 'text/html')

    email.attach(attachment_name, attachments, "application/pdf") if attachments else None

    email.send()