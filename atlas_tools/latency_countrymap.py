import argparse
from collections import defaultdict
import logging
import matplotlib as mpl
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon
import matplotlib.pyplot as pyplot
import mpl_toolkits
import numpy as np
import pandas

from atlas_tools import log_filename, LOGGING_FORMAT
from measurement import PingMeasure
from util import get_parent_args_parser

shapefile = 'countries/ne_50m_admin_0_countries'

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
        self.pings = PingMeasure(
            args.target,
            args.key,
            measurements_list=args.msms
        )
        self.pings.run()

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
            help='number of colors in colormap (default: 9'
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
        for (_, _, _, region, _, _, rtt) in self.pings.results:
            states_array[region].append(rtt)

        states = dict()
        for country, rtt_list in states_array.iteritems():
            states[country] = int(sum(rtt_list) / len(rtt_list))

        cut_states = [
            (country, rtt)
            for country, rtt in states.iteritems() if rtt <= 120
            ]
        bad_countries = [
            country
            for country, rtt in states.iteritems() if rtt > 120
            ]

        return cut_states, bad_countries

    def run(self):
        cut_countries, red_countries = self.handle_data()
        dataframe = pandas.DataFrame(
            data=cut_countries,
            columns=['Country_code', 'Latency']
        )
        dataframe.set_index('Country_code', inplace=True)
        values = dataframe['Latency']
        colormap = pyplot.get_cmap('RdYlGn_r')
        scheme = [
            colormap(i / float(self.args.colors))
            for i in xrange(self.args.colors)
            ]
        bins = np.linspace(0, 120, self.args.colors)
        dataframe['bin'] = np.digitize(values, bins) - 1
        dataframe.sort_values('bin', ascending=False).head(10)

        mpl.style.use('seaborn-notebook')
        legend = pyplot.figure(figsize=(22, 12))

        axis = legend.add_subplot(111, axisbg='w', frame_on=False)
        legend.suptitle(
            'Country map for %s' % self.args.target,
            fontsize=20, y=.95
        )

        basemap = mpl_toolkits.basemap.Basemap(lon_0=0, projection='robin')
        basemap.drawmapboundary(color='w')
        basemap.readshapefile(shapefile , 'units', linewidth=.2)

        all_count = set()
        for info, shape in zip(basemap.units_info, basemap.units):
            all_count.add(info['iso_a2'])
            iso2 = info['iso_a2']
            if iso2 in dataframe.index:
                color = scheme[int(dataframe.ix[iso2]['bin'])]

            elif iso2 in red_countries:
                color = 'DarkRed'

            else:
                color = 'LightGray'

            patches = [Polygon(np.array(shape), True)]
            path_collection = PatchCollection(patches)
            path_collection.set_facecolor(color)
            axis.add_collection(path_collection)

        # Cover up Antarctica so legend can be placed over it.
        axis.axhspan(0, 1000 * 1800, facecolor='w', edgecolor='w', zorder=2)

        # Draw color legend.
        ax_legend = legend.add_axes([0.35, 0.14, 0.3, 0.03], zorder=3)
        cmap = mpl.colors.ListedColormap(scheme)
        cbar = mpl.colorbar.ColorbarBase(
            ax_legend,
            cmap=cmap,
            ticks=bins,
            boundaries=bins,
            orientation='horizontal'
        )
        cbar.ax.set_xticklabels([str(round(i, 1)) for i in bins])

        pyplot.savefig(
            '%s_countrymap.png' % self.args.target,
            bbox_inches='tight',
            pad_inches=.2
        )
