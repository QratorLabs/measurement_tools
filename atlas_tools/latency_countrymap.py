import argparse
from collections import defaultdict
import logging
import os

import folium
import geopandas
import pandas
import pkg_resources

from measurement import PingMeasure
from util import get_parent_args_parser, start_logger

shapefile_dir = 'countries'
shapefile_name = 'ne_50m_admin_0_countries.shp'

logger = logging.getLogger(__name__)


class CountryMapper(object):
    project_name = __package__.split('.')[0]

    def __init__(self, args=None):
        start_logger(self.project_name)

        self.probes_grid = defaultdict(list)

        args_parser = self.get_args_parser()
        args = self.args = args_parser.parse_args(args)

        logger.info('Target: %s', args.target)

        if args.filename is None:
            args.filename = '%s_%s' % (args.target, self.project_name)

        probes_features = dict()
        if args.country is not None:
            probes_features['country_code'] = args.country

        self.pings = PingMeasure(
            args.target,
            args.key,
            protocol=args.protocol,
            probes_features=probes_features,
            measurements_list=args.msms,
            probe_number=args.probe_number,
            timeout=args.timeout
        )
        self.pings.run()

    @staticmethod
    def _choose_color(feature, dataframe, linear):
        iso = feature['properties']['iso_a2']
        if iso in dataframe.index:
            return linear(dataframe.get_value(iso, 'Latency'))

        else:
            return 'lightgrey'

    @classmethod
    def create_run(cls):
        cls().run()

    @staticmethod
    def get_args_parser():
        parser = argparse.ArgumentParser(parents=[get_parent_args_parser()])
        parser.add_argument(
            '-m', '--msms',
            metavar='id',
            type=int,
            default=None,
            nargs='+',
            help='comma-separated list of previous measurements_ids '
                 '(default: new_measurement)'
        )
        return parser

    def handle_data(self):
        states_array = defaultdict(list)
        for (_, _, _, _, region, _, _, rtt) in self.pings.results:
            states_array[region].append(rtt)

        states = dict()
        for country, rtt_list in states_array.iteritems():
            states[country] = min(int(sum(rtt_list) / len(rtt_list)), 120)

        return states

    def run(self):
        logger.info('Drawing the countrymap')

        resource_dir = pkg_resources.resource_filename(__package__, shapefile_dir)
        resource_fname = os.path.join(resource_dir, shapefile_name)
        df_shapefile_countries = geopandas.GeoDataFrame.from_file(resource_fname)

        cut_countries = self.handle_data()
        dataframe = pandas.DataFrame(
            data=cut_countries.items(),
            columns=['iso_a2', 'Latency'],
        )
        dataframe.set_index('iso_a2', inplace=True)

        linear = folium.LinearColormap(
            ['green', 'yellow', 'red'], vmin=0., vmax=120.
        ).to_step(6)

        countrymap = folium.Map(
            location=[20, 20],
            zoom_start=3, min_zoom=2, max_zoom=8,
            tiles='Mapbox Bright'
        )

        folium.GeoJson(
            df_shapefile_countries,
            style_function=lambda feature: {
                'fillColor': self._choose_color(feature, dataframe, linear),
                'color': 'black',
                'weight': 1,
                'fillOpacity': 0.6
            },
            highlight_function=lambda feature: {
                'fillColor': self._choose_color(feature, dataframe, linear),
                'color': 'black',
                'weight': 3,
                'fillOpacity': 0.7,
                'dashArray': '5, 5'
            }
        ).add_to(countrymap)

        countrymap.add_child(linear)
        countrymap.save('%s.html' % self.args.filename)
