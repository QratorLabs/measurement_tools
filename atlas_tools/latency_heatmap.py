from collections import defaultdict
import argparse
import logging
import math

from cartopy import crs
from geopy.distance import great_circle
from geoviews import feature as gf
import geoviews as gv
import holoviews as hv
from matplotlib import pyplot
import numpy as np
import xarray as xr

from atlas_tools.measurement import ping_measure
from atlas_tools.util import base_parser, atlas_parser, ping_parser, start_logger


RENDERER_NAME = 'Agg'
LONGITUDE_EQUATOR_1_DEGREE = 111.321
LATITUDE_1_DEGREE = 111.0
BASE_VALUE = 0.0

logger = logging.getLogger(__name__)


def _coords_to_indices(density, lat, lon):
    lat = int((lat + 90) * density)
    lon = int((lon + 180) * density)
    return lat, lon


def _indices_to_coords(density, lat, lon):
    lat = (float(lat) / density) - 90
    lon = (float(lon) / density) - 180
    return lat, lon


def _minmax_coords(center_coord, radius):
    return center_coord - radius, center_coord + radius + 1


def _coords_in_circle(density, center_lat_geo, center_lon_geo, radius=250):
    center_lat_index, center_lon_index = _coords_to_indices(density, center_lat_geo, center_lon_geo)

    lon_radius = int(
        density * radius /
        (math.cos(math.radians(center_lat_geo)) *
         LONGITUDE_EQUATOR_1_DEGREE)
    )
    lat_radius = int(radius / LATITUDE_1_DEGREE * density)

    min_lon, max_lon = _minmax_coords(center_lon_index, lon_radius)
    min_lat, max_lat = _minmax_coords(center_lat_index, lat_radius)
    for lon_index in xrange(min_lon, max_lon):
        for lat_index in xrange(min_lat, max_lat):
            lat_geo, lon_geo = _indices_to_coords(density, lat_index, lon_index)
            if lat_geo > 80 or lat_geo < -80:
                continue

            lon_index %= (360 * density)

            distance = great_circle(
                (center_lat_geo, center_lon_geo),
                (lat_geo, lon_geo)
            )
            if distance.kilometers <= radius:
                yield (lat_index, lon_index)



def _make_grid(ping_results, density):
    probes_grid = defaultdict(list)
    for (_, _, _, _, _, lat, lon, rtt) in ping_results:
        for coord in _coords_in_circle(density, lat, lon):
            probes_grid[coord].append(rtt)

    final_grid = np.full(
        (180 * density + 1, 360 * density),
        BASE_VALUE
    )

    for (lat_index, lon_index), rtts in probes_grid.iteritems():
        final_grid[lat_index][lon_index] = max(
            30, (sum(rtts) / len(rtts))
        )
    
    return final_grid


def _make_heatmap(final_grid, density, fname, target):
    logger.info('Drawing the heatmap')

    lat = np.linspace(-90, 90, num=180 * density + 1)
    lon = np.linspace(-179.75, 180, num=360 * density)

    d = {'coords': {'latitude': {'dims': ('latitude',), 'data': lat},
                    'longitude': {'dims': ('longitude',), 'data': lon}},
         'attrs': {'title': '%s latency heatmap' % target},
         'dims': ['latitude', 'longitude'],
         'data_vars': {'latency': {'dims': ('latitude', 'longitude'),
                                   'data': final_grid}}
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

    if fname.endswith('.png'):
        fname = fname[:-4]

    renderer = hv.renderer('matplotlib').instance(fig='png')
    renderer.save(img, fname, style=dict(Image={'cmap': 'RdYlGn_r'}))


def init_renderer():
    hv.extension('matplotlib')
    hv.output(backend='matplotlib')
    pyplot.switch_backend(RENDERER_NAME)


def create_heatmap(fname, atlas_key, target, density=4, country=None,
                   probe_limit=None, timeout=None, measurements_list=None):
    pings = ping_measure(
        atlas_key, target,
        country=country,
        probe_limit=probe_limit,
        timeout=timeout,
        measurements_list=measurements_list
    )

    grid = _make_grid(pings.results, density)
    _make_heatmap(grid, density, fname, target)


def main():
    parser = argparse.ArgumentParser(
        parents=[base_parser(), atlas_parser(), ping_parser()],
        description='create a world heatmap of target latencies from Atlas probes'
    )
    parser.add_argument(
        '-f', '--filename',
        help="output PNG image filename (default: 'heatmap_<target>.png')"
    )
    parser.add_argument(
        '-d', '--density',
        type=int,
        default=4,
        help='cells number per dergee (default: 4)'
    )
    args = parser.parse_args()

    if args.filename is None:
        args.filename = 'heatmap_%s.png' % args.target

    start_logger('atlas_tools', verbose=args.verbose)

    # initialize Matplotlib
    init_renderer()

    create_heatmap(
        args.filename, args.key, args.target,
        density=args.density,
        country=args.country,
        probe_limit=args.probe_number,
        timeout=args.timeout,
        measurements_list=args.msms
    )


if __name__ == '__main__':
    main()
