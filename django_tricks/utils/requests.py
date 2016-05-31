import re
from collections import OrderedDict
from urllib.parse import urlencode, urljoin, urlunparse

absolute_http_url_re = re.compile(r'^https?://', re.IGNORECASE)


def get_headers(request):
    wsgi_env = list(sorted(request.META.items()))
    return OrderedDict((k.replace('_', ' '), v)
                       for (k, v) in wsgi_env if k.startswith('HTTP_') or k.startswith('REMOTE_'))


def build_absolute_uri(location, params: dict = None, is_secure=False):
    from django.contrib.sites.models import Site
    from django.utils.encoding import iri_to_uri

    site = Site.objects.get_current()
    host = site.domain
    params = '?%s' % urlencode(params) if params else ''

    if not absolute_http_url_re.match(location):
        current_uri = '%s://%s' % ('https' if is_secure else 'http', host)
        location = urljoin(current_uri, location)

    return iri_to_uri(location) + params


def get_ip(request):
    ip = request.META.get('HTTP_X_FORWARDED_FOR', None)
    ip = ip.split(', ')[0] if ip else request.META.get('REMOTE_ADDR', '')
    return ip


def build_url(scheme='', host='', path='', params='', query='', fragment=''):
    return urlunparse((scheme, host, path, params, query, fragment))


def get_local_host(request):
    scheme = 'http' + ('s' if request.is_secure() else '')
    return build_url(scheme=scheme, host=request.get_host())
