import os

from django.core.validators import MinValueValidator
from django.db.models import FloatField
from django.forms import widgets
from django.utils.translation import gettext_lazy as _
from pint import UnitRegistry

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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
