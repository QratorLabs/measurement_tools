import argparse
from collections import defaultdict
import logging

import folium
import pandas

from measurement import PingMeasure
from util import get_parent_args_parser, start_logger

logger = logging.getLogger(__name__)

m_colors = [
    'red', 'blue', 'green', 'purple', 'orange', 'darkred',
    'beige', 'darkblue', 'darkgreen', 'cadetblue', 'white',
    'pink', 'lightblue', 'lightgreen', 'gray', 'lightgray'
]


class NsLookupMapper(object):
    project_name = __package__.split('.')[0]

    def __init__(self, args=None):
        start_logger(self.project_name)

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
    def get_args_parser():
        parser = argparse.ArgumentParser(parents=[get_parent_args_parser()])
        parser.add_argument(
            '-m', '--msms',
            metavar='id',
            type=int,
            default=None,
            nargs='+',
            help='space-separated list of previous measurements_ids'
                 '(default: new_measurement)'
        )
        return parser

    @classmethod
    def create_run(cls):
        cls().run()

    def make_map(self):
        logger.info('Drawing the nslookup map')

        columns_labels = [
            'probe_id', 'source_ip', 'dst_ip', 'asn',
            'country', 'latitude', 'longitude', 'latency'
        ]

        panda_probes = pandas.DataFrame.from_records(
            self.pings.results, columns=columns_labels
        )

        nslookup_map = folium.Map(
            location=[20, 20],
            zoom_start=2, max_zoom=10, min_zoom=2,
            tiles='Mapbox Bright'
        )

        resolves_counters = defaultdict(int)
        for name, row in panda_probes.iterrows():
            resolves_counters[row["dst_ip"]] += 1

        resolves_counters = [
            (dst_ip, count) for dst_ip, count in resolves_counters.iteritems()
        ]
        resolves_counters.sort(key=lambda tup: tup[1], reverse=True)

        marker_clusters = defaultdict(dict)
        for i, (dst_ip, count) in enumerate(resolves_counters):
            color = m_colors[i % len(m_colors)]
            marker_clusters[dst_ip]['count'] = count
            marker_clusters[dst_ip]['color'] = color

            feature_layer = folium.FeatureGroup(
                name='Resolved ip: %s, color: %s, count: %s' %
                     (dst_ip, color, count)
            ).add_to(nslookup_map)
            marker_clusters[dst_ip]['layer'] = feature_layer

        for name, row in panda_probes.iterrows():
            dst_ip = row['dst_ip']
            folium.CircleMarker(
                location=[float(row['latitude']), float(row['longitude'])],
                popup="Probe_id: %s<br />Resolved_ip: %s" %
                      (row['probe_id'], dst_ip),
                radius=2,
                fill=True,
                color=marker_clusters[dst_ip]['color'],
                fill_opacity=1.0
            ).add_to(marker_clusters[dst_ip]['layer'])

        nslookup_map.add_child(folium.LayerControl())
        nslookup_map.save('%s.html' % self.args.filename)

    def run(self):
        self.make_map()
