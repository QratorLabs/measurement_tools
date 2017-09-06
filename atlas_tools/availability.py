import argparse
from collections import defaultdict
import logging
import socket
import time

from atlas_tools import LOGGING_FORMAT, log_filename
from measurement import PingMeasure, TraceMeasure
from util import get_parent_args_parser


logger = logging.getLogger(__name__)


def lookup(addr):
    try:
        return socket.gethostbyaddr(addr)
    except socket.herror:
        return None, None, None


def get_args_parser():
    parser = argparse.ArgumentParser(parents=[get_parent_args_parser()])
    parser.add_argument(
        '-c', '--country',
        type=str, default=None,
        help='measurement only for selected country (2-letter code country) '
             '(default: all active Atlas probes)'
    )
    parser.add_argument(
        '-p', '--protocol',
        choices=['ICMP', 'UDP'],
        default='ICMP',
        help='protocol for measurements: ICMP or UDP (default: ICMP)'
    )
    return parser


def log_pings(pings, failed_countries, failed_countries_size):
    logger.info(' Atlas ping measurement ids: %s', pings.response)
    logger.info(
        ' Failed pings: %s / %s',
        len(pings.failed_probes),
        len(pings.results) + len(pings.failed_probes)
    )

    if failed_countries:
        f_countries = defaultdict(int)
        for country in pings.failed_probes.itervalues():
            f_countries[country.upper()] += 1

        logging.info(' Probe_ids: %s', pings.failed_probes.keys())
        logging.info(' Failed pings breakdown by countries:')
        f_countries = f_countries.items()
        f_countries.sort(key=lambda tup: tup[1], reverse=True)
        for i in xrange(min(failed_countries_size, len(f_countries))):
            country, counter = f_countries[i]
            logging.info(
                ' %s: %.4f',
                country,
                float(counter) / len(pings.failed_probes)
            )


def log_traces(target, traces, failed_probes):
    logger.info(' Atlas trace measurement ids: %s', traces.response)
    logger.info(
        ' Failed traces: %s / %s',
        len(traces.results),
        len(failed_probes)
    )

    with open('failed_traces_to_%s.txt' % target, 'w+') as fd:
        for src_ip, prb_id, trace in traces.results:
            fd.write(
                'Source ip: %s, prb_id: %s\nTrace:\nHop\tip\t\trtt\tptr\n' %
                (src_ip, prb_id)
            )

            for hop_num, hop_ip, hop_rtt in trace:
                if hop_num == 255:
                    continue

                if hop_ip == '*':
                    fd.write('%s\t%s\t\t%s\n' % (hop_num, hop_ip, hop_rtt))
                elif hop_ip == 'error':
                    fd.write('%s\t%s\n' % (hop_num, hop_rtt))
                else:
                    host_str, _, _ = lookup(hop_ip)
                    fd.write(
                        '%s\t%s\t%s\t%s\n' %
                        (hop_num, hop_ip, hop_rtt, host_str)
                    )
            fd.write('\n')


def do_ip_test(args=None):
    root_logger = logging.getLogger()
    for log_handler in root_logger.handlers:
        root_logger.removeHandler(log_handler)

    logging.basicConfig(
        format=LOGGING_FORMAT,
        filename=log_filename,
        level=logging.INFO
    )

    failed_countries_size = 10
    failed_countries = False

    args_parser = get_args_parser()
    args = args_parser.parse_args(args)

    logger.info(' Target: %s', args.target)
    probes_features = dict()
    if args.country is not None:
        probes_features['country_code'] = args.country

    pings = PingMeasure(
        args.target, args.key, protocol=args.protocol,
        probes_features=probes_features
    )
    pings.run()

    log_pings(pings, failed_countries, failed_countries_size)

    if len(pings.probes_data) > 9000 or len(pings.failed_probes) > 1000:
        time.sleep(420)

    probes_data = {
        probe_id: pings.probes_data[probe_id]
        for probe_id in pings.failed_probes
        }

    traces = TraceMeasure(
        args.target,
        args.key,
        protocol=args.protocol,
        probes_data=probes_data
    )
    traces.run()

    log_traces(args.target, traces, pings.failed_probes)
