# -*- encoding: utf8 -*-
import random
import re

from django.conf import settings
from django.contrib.auth.hashers import mask_hash

GENERATORS = None
PREFERRED_GENERATOR = None


class BaseCodeGenerator(object):
    name = None

    def salt(self):
        return ''

    def verify(self, code):
        raise NotImplementedError()

    def encode(self, salt):
        raise NotImplementedError()

    def safe_summary(self, *args, **kwargs):
        raise NotImplementedError()


class LuhnCodeGenerator(BaseCodeGenerator):
    name = 'luhn'
    parts = 4
    base = 16

    @property
    def symbols(self):
        if self._symbols:
            return self._symbols
        self._symbols = settings.LUHN_SYMBOLS
        return self._symbols

    def symbols_encoder(self, index):
        return self.symbols[index]

    def symbols_decoder(self, value):
        return self.symbols.index(value)

    def luhn_sum_mod_base(self, string):
        # Adapted from http://en.wikipedia.org/wiki/Luhn_name
        digits = map(self.symbols_decoder, string)
        return (sum(digits[::-2]) + sum(
            map(lambda d: sum(divmod(2 * d, self.base)),
                digits[-2::-2]))) % self.base

    def generate_checkdigit(self, string):
        checkdigit = self.luhn_sum_mod_base(string + self.symbols_encoder(0))
        if checkdigit: checkdigit = self.base - checkdigit
        return self.symbols_encoder(checkdigit)

    def verify_checkdigit(self, string):
        return 0 == self.luhn_sum_mod_base(string)

    def encode(self, salt, parts=4):
        assert salt and '$' not in salt
        assert parts > 3
        if not parts:
            parts = self.parts

        samples = []
        for n in range(parts - 1):
            # Each part has a unique set of symbols
            samples += random.sample(self.symbols, 4)

        samples += random.sample(self.symbols,
                                 3)  # Leave space for the check digit
        code = ''.join(samples)
        code_salted = '%s%s' % (code, salt)
        checksum = self.generate_checkdigit(code_salted)
        code = '-'.join(re.findall(r'.{4}', '%s%s' % (code, checksum))).upper()
        return '{0}${1}${2}'.format(self.name, salt, code)

    def verify(self, code):
        code = re.sub(r'[\s\-_]', '', code.lower())
        assert len(code) % 4
        code_salted = '{0}{1}{2}'.format(code[:-1], self.salt, code[-1])

        result = False

        try:
            result = self.verify_checkdigit(code_salted)
        except ValueError:
            result = False

        return result

    def summary(self, encoded):
        name, salt, code = encoded.split('$', 2)
        assert name == self.name

        return {'name': name,
                'salt': salt,
                'code': code}

    def safe_summary(self, encoded):
        summary = self.summary(encoded)
        return {'name': summary['name'],
                'salt': mask_hash(summary['salt']),
                'code': mask_hash(summary['code'])}


class NumbersCodeGenerator(LuhnCodeGenerator):
    symbols = '01234567890'
    name = 'numbers'
    base = 10
