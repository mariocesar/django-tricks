from django.core.urlresolvers import RegexURLPattern, Resolver404
from django.http import Http404
from django.utils import six


def route(regex):
    def wrapper(func):
        func.urlpattern = RegexURLPattern(
            regex, func,
            name=func.__qualname__)
        return func

    return wrapper


class ControllerType(type):
    def __new__(cls, name, bases, attrs):
        super_new = super(ControllerType, cls).__new__
        # Create the class.
        module = attrs.pop('__module__')
        new_class = super_new(cls, name, bases, {'__module__': module})
        new_class.url_patterns = []

        for obj_name, obj in attrs.items():
            setattr(new_class, obj_name, obj)

            if hasattr(obj, 'urlpattern'):
                new_class.url_patterns.append(obj.urlpattern)

        return new_class


class ControllerView(six.with_metaclass(ControllerType)):
    def dispatch(self, request, *args, **kwargs):
        self.path = kwargs.pop('path')

        for pattern in self.url_patterns:
            try:
                resolver_match = pattern.resolve(self.path)
            except Resolver404:
                raise Http404('Controller view "%s" not found.' % self.path)
            else:
                if resolver_match:
                    callback, callback_args, callback_kwargs = resolver_match
                    request.resolver_match = resolver_match

                    return callback(self, request, *args, **callback_kwargs)

        raise Http404('No views registered in the controller %s.' % type(self))
