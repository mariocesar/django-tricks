import os
import string
from itertools import chain

from django.conf import settings
from django.contrib.auth.hashers import mask_hash
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.forms import SimpleArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import FloatField, CharField, SlugField, PositiveIntegerField
from django.forms import widgets
from django.utils.crypto import get_random_string
from django.utils.functional import curry
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from pint import UnitRegistry
from pytz import common_timezones

from django_tricks.utils.luhncode import LuhnCodeGenerator

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TIMEZONE_CHOICES = [(timezone, timezone) for timezone in common_timezones]

ureg = UnitRegistry(system='mks')


class UnitField(FloatField):
    def __init__(self, *args, **kwargs):
        unit = kwargs.pop('unit', None)

        if unit is None:
            raise ValueError('Missing unit definition.')

        self.unit = ureg(unit)
        self.symbol = ureg.get_symbol(unit)

        super(UnitField, self).__init__(*args, **kwargs)

        if not self.help_text:
            self.help_text = _('Value in {}').format(self.symbol)

    def deconstruct(self):
        name, path, args, kwargs = super(UnitField, self).deconstruct()
        kwargs['unit'] = self.symbol
        return name, path, args, kwargs

    def to_python(self, value):
        if value:
            return value * self.unit
        return value

    def formfield(self, **defaults):
        attrs = {'type': 'number',
                 'step': 'any'}

        min_values = [validator.limit_value for validator in self.validators if
                      isinstance(validator, MinValueValidator)]

        if min_values:
            attrs['min'] = min(min_values)

        if not self.blank:
            attrs['required'] = 'required'

        defaults.update({'widget': widgets.NumberInput(attrs=attrs)})

        return super(UnitField, self).formfield(**defaults)


class TimezoneChoiceField(CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 200)
        kwargs['choices'] = TIMEZONE_CHOICES
        super().__init__(*args, **kwargs)


class FlagsCheckboxSelectMultiple(widgets.CheckboxSelectMultiple):
    def __init__(self, *args, **kwargs):
        self.queryset = kwargs.pop('queryset')
        super(FlagsCheckboxSelectMultiple, self).__init__(*args, **kwargs)

    def value_from_datadict(self, data, files, name):
        value = super(FlagsCheckboxSelectMultiple, self).value_from_datadict(data, files, name)
        add_field_name = '%s_add' % name
        add_flags = data.get(add_field_name, None)

        if add_flags:
            value = value + add_flags.split(',')

        value = ', '.join(set(value))
        return value

    def append_choices(self, field_name, choices):
        flags = list(chain(*self.queryset.values_list(field_name, flat=True)))
        value_choices = [value for value, label in choices]
        flags = filter(lambda flag: flag not in value_choices, flags)

        return list(chain(choices, [(value, value.title()) for value in flags]))

    def render(self, name, value, attrs=None, choices=()):
        self.choices = self.append_choices(name, self.choices)
        output = super(FlagsCheckboxSelectMultiple, self).render(name, value, attrs, choices)
        output += format_html('<ul><li><label for="id_add_flag">Add a new flag(s)</label><br>'
                              '<input id="id_{0}_add" name="{0}_add" type="text" '
                              'class="vTextField" maxlength="140" '
                              'placeholder="A single flag, or many separated by commas \",\"">'
                              '</li></ul>'.format(name))

        return mark_safe(output)


class SimpleFlagField(SimpleArrayField):
    def to_python(self, value):
        if isinstance(value, (list, tuple)):
            value = ', '.join(value)
        return super().to_python(value)

    def prepare_value(self, value):
        value = super(SimpleFlagField, self).prepare_value(value)
        if value:
            return value.split(',')
        return value


class FlagsField(ArrayField):
    def __init__(self, flags, size=None, **kwargs):
        base_field = SlugField(max_length=10, blank=True)
        self.flags = flags
        super(FlagsField, self).__init__(base_field=base_field, size=size, **kwargs)

    def formfield(self, **kwargs):
        defaults = {
            'form_class': SimpleFlagField,
            'widget': FlagsCheckboxSelectMultiple(
                choices=self.flags,
                queryset=self.model._default_manager.filter())
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs['size']
        del kwargs['base_field']
        kwargs['flags'] = self.flags
        return name, path, args, kwargs


class NumberField(PositiveIntegerField):
    def formfield(self, **defaults):
        attrs = {'type': 'number', 'step': '1'}

        if not self.blank:
            attrs['required'] = 'required'

        min_values = [validator.limit_value for validator in self.validators if
                      isinstance(validator, MinValueValidator)]

        max_values = [validator.limit_value for validator in self.validators if
                      isinstance(validator, MaxValueValidator)]

        if min_values:
            attrs['min'] = min(min_values)

        if max_values:
            attrs['max'] = max(max_values)

        defaults.update({'widget': widgets.NumberInput(attrs=attrs)})
        return super(NumberField, self).formfield(**defaults)


class PositiveNumberField(PositiveIntegerField):
    default_validators = [MinValueValidator(0)]


class UppercaseCharField(CharField):
    def from_db_value(self, value, expression, connection, context):
        if isinstance(value, str):
            return value.upper()
        else:
            return value


class DefaultRandomCharField(CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('blank', True)
        kwargs.setdefault('max_length', 100)

        self.length = kwargs.pop('length', None)

        if self.length is None:
            raise ValueError('Missing length of the random strinbg.')

        super().__init__(*args, **kwargs)

        if self.length > self.max_length:
            raise ValueError('Random string can not be more than the field max_length.')

    def deconstruct(self):
        name, path, args, kwargs = super(DefaultRandomCharField, self).deconstruct()
        kwargs['length'] = self.length
        return name, path, args, kwargs

    def get_random_option(self):
        return get_random_string(
            allowed_chars=string.ascii_uppercase + string.ascii_lowercase + string.digits,
            length=self.length)

    def pre_save(self, model_instance, add):
        if not add and getattr(model_instance, self.attname) != '':
            return getattr(model_instance, self.attname)

        while True:
            value = self.get_random_option()

            if model_instance._default_manager.objects.filter(**{self.name: value}).exists():
                continue
            else:
                return value


class LuhnCodeRandomField(DefaultRandomCharField):
    def get_random_option(self):
        generator = LuhnCodeGenerator()
        return generator.encode(settings.SECRET_KEY, parts=self.length)

    def get_FIELD_mask(self, field):
        value = getattr(self, field.attname)
        return mask_hash(value)

    def contribute_to_class(self, cls, name, virtual_only=False):
        super(LuhnCodeRandomField, self).contribute_to_class(cls, name, virtual_only=virtual_only)
        setattr(cls, 'get_%s_mask', curry(self.get_FIELD_mask, field=self))
