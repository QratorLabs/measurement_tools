import argparse
import logging

LOGGING_FORMAT = '%(asctime)s:%(levelname)s:%(message)s'
log_filename = 'atlas.log'


def get_parent_args_parser():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        '-t', '--target',
        required=True,
        help='IPv4 address | domain name'
    )
    parser.add_argument(
        '-k', '--key',
        required=True,
        help='ATLAS_API_CREATE_KEY'
    )
    parser.add_argument(
        '-f', '--filename',
        default=None,
        help='Results filename'
    )
    parser.add_argument(
        '--UDP',
        dest='protocol',
        action='store_const',
        const='UDP',
        default='ICMP',
        help='Do measurement via UDP (by default: ICMP)'
    )
    parser.add_argument(
        '-c', '--country',
        type=str, default=None,
        help='Measurement only for selected country (2-letter code country) '
             '(default: all active Atlas probes)'
    )
    parser.add_argument(
        '-n', '--probe_number',
        type=int, default=None,
        help='Number of probes in measurement, '
             '(default: all active Atlas probes)'
    )

    return parser


def start_logger(project_name):
    root_logger = logging.getLogger()
    for log_handler in root_logger.handlers:
        root_logger.removeHandler(log_handler)

    logging.basicConfig(
        level=logging.INFO,
        format=LOGGING_FORMAT
    )
    logging.root.handlers[0].addFilter(logging.Filter(project_name))
