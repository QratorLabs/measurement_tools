#!/usr/bin/python

from setuptools import find_packages, setup

from atlas_tools import __version__

package_name = 'atlas_tools'

setup(
    name=package_name,
    version=__version__,
    author='Alexander Yakushkin',
    author_email='ay@qrator.net',
    packages=find_packages(),
    dependency_links=[
        'https://github.com/ioam/geoviews/tarball/master#egg=geoviews-1.3.2'
    ],
    install_requires=[
        'Cartopy',
        'geoviews>=1.3.2',
        'holoviews',
        'geopy',
        'shapely>=1.5.6',
        'pyshp>=1.1.4',
        'six>=1.3.0',
        'matplotlib>=1.3.0',
        'ripe.atlas.cousteau'

    ],
    entry_points={
        'console_scripts': [
            'atlas-heatmap = ' +
            '{}.latency_heatmap:HeatMapper.create_run'.format(package_name),

            'atlas-availability = ' +
            '{}.availability:do_ip_test'.format(package_name),

            'atlas-countrymap = ' +
            '{}.latency_countrymap:CountryMapper.create_run'.format(
                package_name
            ),
        ],
    },
)
