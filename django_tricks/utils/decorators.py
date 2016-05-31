import sys

from django.core.cache import cache
from django.utils.six import wraps


class ServiceReturn:
    def __init__(self, name, ret_value, err=None, exc_info=None):
        self.name = name
        self.ret_value = ret_value
        self.exc_info = exc_info
        self.err = err

    def __repr__(self):
        return '<ServiceReturn %s [%s]>' % (self.name, 'success' if self.successful else 'failed')

    def __nonzero__(self):
        return self.successful

    def __bool__(self):
        return self.successful

    def __iter__(self):
        return iter(self.ret_value)

    def __getattr__(self, item):
        return getattr(self.ret_value, item)

    @property
    def successful(self):
        return self.err is None

    @property
    def failed(self):
        return self.exc_info is not None

    def raise_for_status(self):
        if self.exc_info:
            raise self.err


def service(func):
    """wrap functions'return value with ServiceReturn, catching exceptions and storing
    the return value and successful status."""
    name = func.__qualname__

    @wraps(func)
    def inner(*args, **kwargs) -> ServiceReturn:

        # Do argument validation if annotations are available
        annotations = func.__annotations__

        if annotations:
            for argname, argtype in annotations.items():
                if argtype in kwargs and type(kwargs[argname]) is not argtype:
                    raise ValueError('"%s" argument has the wrong type.'
                                     'Expected %s, found %s' % (name, argtype, type(kwargs[argname])))

        try:
            ret = func(*args, **kwargs)
        except Exception as err:
            exc_info = sys.exc_info()
            return ServiceReturn(name, ret_value=None, err=err, exc_info=exc_info)

        return ServiceReturn(name, ret_value=ret)

    return inner


def cacheresult(func, prefix=None, keyname=None):
    """Saves up in the cache the function's return value each time it is called.

    Uses the name of the method and their arguments to build the cache key name."""

    keyname = '%s%s' % (prefix, keyname or func.__qualname__)

    @wraps(func)
    def inner(this, *args, **kwargs):

        if args or kwargs:
            cachekey = '%s%s%s' % (keyname, hash(args), hash(kwargs))
        else:
            cachekey = keyname

        res = cache.get(cachekey)

        if res is None:
            res = func(this, *args, **kwargs)
            cache.set(cachekey, res)
        return res

    return inner
