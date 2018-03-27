import types
import re
import json
import urllib2
import requests


def get_dot(d, dotkey):
    """Get value from a dict-like object with dot notation keys"""
    value = d
    try:
        for key in dotkey.split('.'):
            value = value[key]
    except KeyError:
        return None
    else:
        return value


def map_dict(keys_mappings, source_dict):
    item = {}
    for keys in keys_mappings:
        if not isinstance(keys, (tuple, list)):
            keys = (keys, keys)
        if isinstance(keys[1], (tuple, list)):
            val = map_dict(keys[1], source_dict)
        elif (isinstance(keys[1], types.LambdaType) or
                hasattr(keys[1], '__call__')):
            val = keys[1](source_dict)
        else:
            val = get_dot(source_dict, keys[1])

            # Parse address from list to string
            if isinstance(val, list) and keys[1] == "location.formattedAddress":
                val = ", ".join(val)

        item[keys[0]] = val
    return item


def strip_html_tags(text):
    if text is not None:
        return re.sub('<[^<]+?>', '', text)
    return text


def format_fields(fields, separator=', '):
    """
    Helper function useful (for example) to format an 'address'
    given a set of fields (for example 'country', 'region', 'city') and
    when some of them may be None.
    """
    not_none_fields = [field for field in fields if field is not None]
    return separator.join(not_none_fields)


def pretty_dump(dic):
    if not isinstance(dic, dict):
        return ''
    return json.dumps(dic, sort_keys=True,
                      indent=4, separators=(',', ': '))


def is_exception_urlerror(exception):
    return isinstance(exception, urllib2.URLError)


def is_exception_read_timeout(exception):
    return isinstance(exception, requests.exceptions.ReadTimeout)


def is_exception_ssl_error(exception):
    return isinstance(exception, requests.exceptions.SSLError)
