from cartopy import crs
from collections import defaultdict
from geopy.distance import great_circle
from geoviews import feature as gf
import geoviews as gv
import holoviews as hv
import logging
import math
import numpy as np
import xarray as xr

from measurement import PingMeasure


logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', filename='atlas.log', level=logging.INFO)
logger = logging.getLogger('heatmap')

hv.extension('matplotlib')
hv.output(backend='matplotlib')
longitude_equator_1_degree = 111.321
latitude_1_degree = 111.0
base_value = 0.0


class HeatMapper(object):
    def __init__(self, target, atlas_api_key, density=4, msm_list=None):
        self.pings = PingMeasure(target, atlas_api_key, logger, measurements_list=msm_list)
        self.pings.run()
        self.density = density
        self.probes_grid = defaultdict(list)
        self.final_grid = np.full((180 * density + 1, 360 * density), base_value)

    def coords_to_indices(self, lat, lon):
        lat = int((lat + 90) * self.density)
        lon = int((lon + 180) * self.density)
        return lat, lon

    def indices_to_coords(self, lat, lon):
        lat = (float(lat)/self.density) - 90
        lon = (float(lon)/self.density) - 180
        return lat, lon

    def coords_in_circle(self, center_lat_geo, center_lon_geo, radius=250):
        center_lat_index, center_lon_index = self.coords_to_indices(center_lat_geo, center_lon_geo)
        lon_radius = int(radius / (math.cos(math.radians(center_lat_geo)) * longitude_equator_1_degree) * self.density)
        lat_radius = int(radius / latitude_1_degree * self.density)

        for lon_index in xrange(center_lon_index - lon_radius, center_lon_index + lon_radius + 1):
            for lat_index in xrange(center_lat_index - lat_radius, center_lat_index + lat_radius + 1):
                lat_geo, lon_geo = self.indices_to_coords(lat_index, lon_index)
                if lat_geo > 80 or lat_geo < -80:
                    continue

                lon_index %= 360 * self.density

                if great_circle((center_lat_geo, center_lon_geo), (lat_geo, lon_geo)).kilometers <= radius:
                    yield (lat_index, lon_index)

    def make_grid(self):
        probes_grid = defaultdict(list)
        for (prb_id, src_ip, asn, region, lat, lon, rtt) in self.pings.results:
            for coord in self.coords_in_circle(lat, lon):
                probes_grid[coord].append(rtt)

        for (lat_index, lon_index), rtts in probes_grid.iteritems():
            self.final_grid[lat_index][lon_index] = max(30, (sum(rtts) / len(rtts)))

    def paint_heatmap(self):
        lt = np.linspace(-90, 90, num=180 * self.density + 1)
        ln = np.linspace(-179.75, 180, num=360 * self.density)

        d = {'coords': {'latitude': {'dims': ('latitude',), 'data': lt},
                        'longitude': {'dims': ('longitude',), 'data': ln}},
             'attrs': {'title': 'Qrator latency map'},
             'dims': ['latitude', 'longitude'],
             'data_vars': {'latency': {'dims': ('latitude', 'longitude'), 'data': self.final_grid}}
             }

        xr_set = xr.Dataset.from_dict(d)
        xr_dataset = gv.Dataset(xr_set, kdims=['latitude', 'longitude'], vdims=['latency'], crs=crs.PlateCarree())
        hv.output(dpi=200, size=500)
        hv.opts("Image [colorbar=True clipping_colors={'min': 'lightgrey'}]")

        img = gf.land * xr_dataset.redim(latency=dict(range=(30, 90))).to(gv.Image, ['longitude', 'latitude']) * gf.ocean * gf.borders

        renderer = hv.renderer('matplotlib').instance(fig='png')
        renderer.save(img, 'my_map1', style=dict(Image={'cmap': 'RdYlGn_r'}))


def paint_heatmap(target, atlas_api_key, density, msm_list):
    logger.info(' Target: %s', target)
    heat = HeatMapper(target, atlas_api_key, density, msm_list)
    heat.make_grid()
    heat.paint_heatmap()
