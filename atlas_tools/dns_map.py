from collections import defaultdict
import argparse
import logging

import folium
import pandas

from atlas_tools.measurement import ping_measure
from atlas_tools.util import base_parser, atlas_parser, ping_parser, start_logger, check_ping_args

logger = logging.getLogger(__name__)

MAP_COLORS = [
    'red', 'blue', 'green', 'purple', 'orange', 'darkred',
    'beige', 'darkblue', 'darkgreen', 'cadetblue', 'white',
    'pink', 'lightblue', 'lightgreen', 'gray', 'lightgray'
]


def _make_map(ping_results, fname):
    logger.info('Drawing DNS map')

    columns_labels = [
        'probe_id', 'source_ip', 'dst_ip', 'asn',
        'country', 'latitude', 'longitude', 'latency'
    ]

    panda_probes = pandas.DataFrame.from_records(
        ping_results, columns=columns_labels
    )

    dns_map = folium.Map(
        location=[20, 20],
        zoom_start=2, max_zoom=10, min_zoom=2,
        tiles='Mapbox Bright'
    )

    resolves_counters = defaultdict(int)
    for name, row in panda_probes.iterrows():
        resolves_counters[row["dst_ip"]] += 1

    resolves_counters = [
        (dst_ip, count) for dst_ip, count in resolves_counters.items()
    ]
    resolves_counters.sort(key=lambda tup: tup[1], reverse=True)

    marker_clusters = defaultdict(dict)
    for i, (dst_ip, count) in enumerate(resolves_counters):
        color = MAP_COLORS[i % len(MAP_COLORS)]
        marker_clusters[dst_ip]['count'] = count
        marker_clusters[dst_ip]['color'] = color

        feature_layer = folium.FeatureGroup(
            name='Resolved ip: %s, color: %s, count: %s' %
                 (dst_ip, color, count)
        ).add_to(dns_map)
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

    dns_map.add_child(folium.LayerControl())
    dns_map.save(fname)


def create_map(fname, atlas_key, target, country=None,
               probe_limit=None, timeout=None, measurements_list=None):
    pings = ping_measure(
        atlas_key, target,
        country=country,
        probe_limit=probe_limit,
        timeout=timeout,
        measurements_list=measurements_list
    )

    _make_map(pings.results, fname)


def main():
    parser = argparse.ArgumentParser(
        parents=[base_parser(), atlas_parser(), ping_parser()],
        description='create a world map of DNS resolving results for the target'
    )
    parser.add_argument(
        '-f', '--filename',
        help="output HTML filename (default: 'dnsmap_<target>.html')"
    )
    args = parser.parse_args()

    check_ping_args(parser, args)
    if args.filename is None:
        args.filename = 'dnsmap_%s.html' % args.target

    start_logger('atlas_tools', verbose=args.verbose)

    create_map(
        args.filename, args.key, args.target,
        country=args.country,
        probe_limit=args.probe_number,
        timeout=args.timeout,
        measurements_list=args.msms
    )


if __name__ == '__main__':
    main()
