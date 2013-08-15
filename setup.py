# -*- coding: utf-8 -*-
import os
from setuptools import setup, find_packages


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

version = '1.0a1'

long_description = (
    read('README.txt')
    + '\n' +
    'Change history\n'
    '**************\n'
    + '\n' +
    read('CHANGES.txt')
    + '\n' +
    'Contributors\n'
    '************\n'
    + '\n' +
    read('CONTRIBUTORS.txt')
    + '\n' +
    'Download\n'
    '********\n')

setup(name='collective.exhibit',
      version=version,
      description="Content product for creating multi-section exhibits for museums and similar sites",
      long_description=long_description,
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
        'Framework :: Plone',
        'Intended Audience :: Developers',
        ],
      keywords='',
      author='jazkarta',
      author_email='info@jazkarta.com',
      url='https://github.com/jazkarta/collective.exhibit',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['collective'],
      include_package_data=True,
      zip_safe=False,
      install_requires=['setuptools',
                        'plone.app.dexterity [grok]',
                        'plone.app.referenceablebehavior',
                        'plone.formwidget.contenttree',
                        'collective.autopermission',
                        'plone.namedfile [blobs]',
                        'collective.z3cform.keywordwidget',
                        ],
      extras_require=dict(test=['plone.app.testing',]),
      entry_points="""
[z3c.autoinclude.plugin]
target = plone
      """,
      setup_requires=["PasteScript"],
      paster_plugins=["ZopeSkel"],
      )
