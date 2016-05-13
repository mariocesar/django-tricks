from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class VerboseNameModel(object):
    """Return a more meaningful model representation, if found
    a field name or method verbose_name() use it, or build
    a new representation.

    example:

        >>> user = User.objects.get(pk=1)
        >>> print(user)
        "<django.contrib.auth.models:User pk=1>"

    """

    def __str__(self):
        if hasattr(self, 'verbose_name'):
            if callable(self.verbose_name):
                return self.verbose_name()
            return self.verbose_name
        elif hasattr(self, 'name'):
            return self.name

        return "<%s:%s pk=%s>" % (
            six.text_type(class_.__module__),
            six.text_type(type(self)),
            six.text_type(self.pk))


class ValidateModel(object):
    def save(self, *args, **kwargs):
        self.full_clean()
        super(ValidateModel, self).save(*args, **kwargs)


class AutoNumberModel(object):
    NUMBER_FIELD = 'number'
    NUMBER_AUTO = True

    def __init__(self, *args, **kwargs):
        super(AutoNumberModel, self).__init__(*args, **kwargs)
        if not hasattr(self, self.NUMBER_FIELD):
            raise AttributeError('Missing number field %s' % self.NUMBER_FIELD)

    def numbering_prefix(self):
        return self._meta.verbose_name

    def format_number(self, value):
        # Preprend a X- when debugging
        prefix = '%s%s' % ('X-' if settings.DEBUG else '', self.numbering_prefix().upper())
        return '{prefix}{value:0>5}'.format(prefix=prefix, value=value)

    def pop_next_number(self):
        return self.format_number(self.pop_next_number_value())

    def pop_next_number_value(self):
        raise NotImplementedError('Implement and return a `current_value` + 1')

    def save(self, *args, **kwargs):
        if self.NUMBER_AUTO and not self.number:
            self.number = self.pop_next_number()
        return super(AutoNumberModel, self).save(*args, **kwargs)
