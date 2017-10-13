import argparse
import logging

LOGGING_FORMAT = '%(asctime)s: %(message)s'
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
        help='Results filename'
    )
    parser.add_argument(
        '-p', '--protocol',
        choices=['ICMP', 'UDP'],
        default='ICMP',
        help='Choose measurement protocol (default: ICMP)'
    )
    parser.add_argument(
        '-c', '--country',
        help='Measurement only for selected country (2-letter code country) '
             '(default: all active Atlas probes)'
    )
    parser.add_argument(
        '-n', '--probe_number',
        type=int,
        default=25000,
        help='Number of probes in measurement '
             '(default: all active Atlas probes)'
    )
    parser.add_argument(
        '-T', '--timeout',
        type=int,
        help='Time allocated for measurement in seconds'
             '(default: until the measurement stops)'
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
