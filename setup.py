#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()


requirements = []
test_requirements = []


setup(
    name='django_tricks',
    version='0.1.0',
    description="Django tricks is a set of useful models, views and admins tools.",
    long_description=readme + '\n\n' + history,
    author="Mario César Señoranis Ayala",
    author_email='mariocesar.c50@gmail.com',
    url='https://github.com/mariocesar/django-tricks',
    packages=['django_tricks'],
    package_dir={'django_tricks': 'django_tricks'},
    include_package_data=True,
    install_requires=requirements,
    license="MIT",
    zip_safe=False,
    keywords='django_tricks',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
