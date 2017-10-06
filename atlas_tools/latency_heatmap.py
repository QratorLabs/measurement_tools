import argparse
from collections import defaultdict
import logging
import math

from cartopy import crs
from geopy.distance import great_circle
from geoviews import feature as gf
import geoviews as gv
import holoviews as hv
import numpy as np
import xarray as xr

from atlas_tools import LOGGING_FORMAT, log_filename
from measurement import PingMeasure
from util import get_parent_args_parser

hv.extension('matplotlib')
hv.output(backend='matplotlib')
longitude_equator_1_degree = 111.321
latitude_1_degree = 111.0
base_value = 0.0

logger = logging.getLogger(__name__)


class HeatMapper(object):
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
        self.final_grid = np.full(
            (180 * args.density + 1, 360 * args.density),
            base_value
        )

    @classmethod
    def create_run(cls):
        cls().run()

    @staticmethod
    def get_args_parser():
        parser = argparse.ArgumentParser(parents=[get_parent_args_parser()])
        parser.add_argument(
            '-d', '--density',
            type=int,
            default=4,
            help='cells number per dergee (default: 4)'
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

    def coords_to_indices(self, lat, lon):
        lat = int((lat + 90) * self.args.density)
        lon = int((lon + 180) * self.args.density)
        return lat, lon

    def indices_to_coords(self, lat, lon):
        lat = (float(lat)/self.args.density) - 90
        lon = (float(lon)/self.args.density) - 180
        return lat, lon

    def minmax_coords(self, center_coord, radius):
        return center_coord - radius, center_coord + radius + 1

    def coords_in_circle(self, center_lat_geo, center_lon_geo, radius=250):
        center_lat_index, center_lon_index = self.coords_to_indices(
            center_lat_geo, center_lon_geo
        )

        lon_radius = int(
            self.args.density * radius /
            (math.cos(math.radians(center_lat_geo)) *
             longitude_equator_1_degree)
        )
        lat_radius = int(radius / latitude_1_degree * self.args.density)

        min_lon, max_lon = self.minmax_coords(center_lon_index, lon_radius)
        min_lat, max_lat = self.minmax_coords(center_lat_index, lat_radius)
        for lon_index in xrange(min_lon, max_lon):
            for lat_index in xrange(min_lat, max_lat):
                lat_geo, lon_geo = self.indices_to_coords(
                    lat_index,
                    lon_index
                )
                if lat_geo > 80 or lat_geo < -80:
                    continue

                lon_index %= 360 * self.args.density

                distance = great_circle(
                    (center_lat_geo, center_lon_geo),
                    (lat_geo, lon_geo)
                )
                if distance.kilometers <= radius:
                    yield (lat_index, lon_index)

    def make_grid(self):
        probes_grid = defaultdict(list)
        for (_, _, _, _, _, lat, lon, rtt) in self.pings.results:
            for coord in self.coords_in_circle(lat, lon):
                probes_grid[coord].append(rtt)

        for (lat_index, lon_index), rtts in probes_grid.iteritems():
            self.final_grid[lat_index][lon_index] = max(
                30, (sum(rtts) / len(rtts))
            )

    def paint_heatmap(self):
        lat = np.linspace(-90, 90, num=180 * self.args.density + 1)
        lon = np.linspace(-179.75, 180, num=360 * self.args.density)

        d = {'coords': {'latitude': {'dims': ('latitude',), 'data': lat},
                        'longitude': {'dims': ('longitude',), 'data': lon}},
             'attrs': {'title': 'Qrator latency map'},
             'dims': ['latitude', 'longitude'],
             'data_vars': {'latency': {'dims': ('latitude', 'longitude'),
                                       'data': self.final_grid}}
             }

        xr_set = xr.Dataset.from_dict(d)
        xr_dataset = gv.Dataset(
            xr_set,
            kdims=['latitude', 'longitude'],
            vdims=['latency'],
            crs=crs.PlateCarree()
        )
        hv.output(dpi=200, size=500)
        hv.opts("Image [colorbar=True clipping_colors={'min': 'lightgrey'}]")

        main_layer = xr_dataset.redim(
            latency=dict(range=(30, 90))
        ).to(gv.Image, ['longitude', 'latitude'])

        img = gf.land * main_layer * gf.ocean * gf.borders

        renderer = hv.renderer('matplotlib').instance(fig='png')
        renderer.save(
            img,
            '%s_heatmap' % self.args.target,
            style=dict(Image={'cmap': 'RdYlGn_r'})
        )

    def run(self):
        self.make_grid()
        self.paint_heatmap()
