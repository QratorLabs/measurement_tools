#!/usr/bin/env python

from setuptools import find_packages, setup


setup(
    name='atlas_tools',
    version='0.2.0',
    author='Alexander Yakushkin, Evgeny Uskov',
    author_email='ay@qrator.net, eu@qrator.net',
    packages=find_packages(),
    install_requires=[],
    entry_points={
        'console_scripts': [
            'atlas-heatmap = atlas_tools.latency_heatmap:main',
            'atlas-countrymap = atlas_tools.latency_countrymap:main',
            'atlas-dnsmap = atlas_tools.dns_map:main',
            'atlas-reachability = atlas_tools.reachability:main',
        ],
    },
    package_data={
        'atlas_tools': ['countries/*'],
    },
    test_suite='tests'
)
