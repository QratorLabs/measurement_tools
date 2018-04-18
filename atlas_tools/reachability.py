import argparse
from collections import defaultdict
import logging
import socket

from measurement import ping_measure, trace_measure
from util import get_parent_args_parser, start_logger

logger = logging.getLogger(__name__)

FAILED_COUNTRIES_SIZE = 10
FAILED_COUNTRIES = False


def _log_pings(pings, failed_countries, failed_countries_size):
    logger.info('Atlas ping measurement ids: %s', pings.response)
    logger.info(
        'Failed pings: %s / %s',
        len(pings.failed_probes),
        len(pings.results) + len(pings.failed_probes)
    )

    if failed_countries:
        f_countries = defaultdict(int)
        for country in pings.failed_probes.itervalues():
            f_countries[country.upper()] += 1

        logging.info('Probe_ids: %s', pings.failed_probes.keys())
        logging.info('Failed pings breakdown by countries:')

        f_countries = f_countries.items()
        f_countries.sort(key=lambda tup: tup[1], reverse=True)

        for idx in xrange(min(failed_countries_size, len(f_countries))):
            country, counter = f_countries[idx]
            logging.info(
                '%s: %.4f',
                country,
                float(counter) / len(pings.failed_probes)
            )


def _log_traces(traces, failed_probes, filename):
    logger.info('Atlas trace measurement ids: %s', traces.response)
    logger.info(
        'Failed traces: %s / %s',
        len(traces.results),
        len(failed_probes)
    )

    with open(filename, 'w+') as fd:
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
                    try:
                        host_str, _, _ = socket.gethostbyaddr(hop_ip)
                        fd.write(
                            '%s\t%s\t%s\t%s\n' %
                            (hop_num, hop_ip, hop_rtt, host_str)
                        )
                    except socket.herror:
                        pass

            fd.write('\n')


def test_reachability(fname, atlas_key, target, protocol, country=None,
                      probe_limit=None, timeout=None):
    pings = ping_measure(
        atlas_key, target, protocol,
        country=country,
        probe_limit=probe_limit,
        timeout=timeout
    )

    _log_pings(pings, FAILED_COUNTRIES, FAILED_COUNTRIES_SIZE)


    logger.info('Tracing target with ping-failed probes')

    probes_data = {
        probe_id: pings.probes_data[probe_id]
        for probe_id in pings.failed_probes
    }

    traces = trace_measure(
        atlas_key, target, protocol,
        probes_data=probes_data,
        timeout=timeout
    )

    _log_traces(traces, pings.failed_probes, fname)


def main():
    start_logger('atlas_tools')

    parser = argparse.ArgumentParser(parents=[get_parent_args_parser()])
    args = parser.parse_args()

    if args.filename is None:
        args.filename = 'reachability_%s.dat' % args.target

    test_reachability(
        args.filename, args.key, args.target, args.protocol,
        country=args.country,
        probe_limit=args.probe_number,
        timeout=args.timeout
    )


if __name__ == '__main__':
    main()