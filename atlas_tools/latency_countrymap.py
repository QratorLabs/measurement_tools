import argparse
from collections import defaultdict
import logging
import os

import folium
import geopandas
import pandas
import pkg_resources

from atlas_tools import log_filename, LOGGING_FORMAT
from measurement import PingMeasure
from util import get_parent_args_parser

shapefile_dir = 'countries'
shapefile_name = 'ne_50m_admin_0_countries.shp'

logger = logging.getLogger(__name__)


class CountryMapper(object):
    project_name = __package__.split('.')[0]

    def __init__(self, args=None):
        root_logger = logging.getLogger()
        for log_handler in root_logger.handlers:
            root_logger.removeHandler(log_handler)

        logging.basicConfig(
            level=logging.INFO,
            format=LOGGING_FORMAT,
            filename=log_filename
        )
        logging.root.handlers[0].addFilter(logging.Filter(self.project_name))

        self.probes_grid = defaultdict(list)

        args_parser = self.get_args_parser()
        args = self.args = args_parser.parse_args(args)

        logger.info(' Target: %s', args.target)

        if args.filename is None:
            args.filename = '%s_%s' % (args.target, self.project_name)

        self.pings = PingMeasure(
            args.target,
            args.key,
            measurements_list=args.msms
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
            '-c', '--colors',
            type=int,
            default=9,
            help='number of colors in colormap (default: 9)'
        )
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

        m = folium.Map(location=[20, 20], zoom_start=3)

        folium.GeoJson(
            df_shapefile_countries,
            style_function=lambda feature: {
                'fillColor': self._choose_color(feature, dataframe, linear),
                'color': 'black',
                'weight': 1,
                'fillOpacity': 0.7
            }
        ).add_to(m)

        m.add_child(linear)
        m.save('%s.html' % self.args.filename)
