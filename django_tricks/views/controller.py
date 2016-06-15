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
                sub_match = pattern.resolve(self.path)
            except Resolver404:
                raise Http404('Controller view not found.')
            else:
                if sub_match:
                    return sub_match.func(self, request, *args, **kwargs)

            raise Http404('Controller view not found.')
