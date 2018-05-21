import argparse
import logging
import sys

LOGGING_FORMAT = '%(asctime)s: %(message)s'


def base_parser():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-v', '--verbose', action='store_true', help='more verbose output')
    return parser


def atlas_parser():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        '-t', '--target',
        required=True,
        help='IPv4 address | domain name'
    )
    parser.add_argument(
        '-k', '--key',
        # required=True,
        help='ATLAS_API_CREATE_KEY'
    )
    parser.add_argument(
        '-c', '--country',
        help='choose probes from this country (2-letter country code) '
             '(default: all active Atlas probes)'
    )
    parser.add_argument(
        '-n', '--probe-number',
        type=int,
        default=25000,
        metavar='N',
        help='number of probes in measurement '
             '(default: all active Atlas probes)'
    )
    parser.add_argument(
        '-T', '--timeout',
        type=int,
        default=900,
        help='time allocated for measurement in seconds '
             '(default: 15 min)'
    )
    return parser


def ping_parser():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        '-m', '--measurement-ids',
        metavar='ID',
        type=int,
        default=None,
        nargs='+',
        dest='msms',
        help='use existing measurements instead of creating the new ones '
             '(default: create new measurements)'
    )
    return parser


def check_ping_args(parser, args):
    if args.key is None and args.msms is None:
        parser.error('Atlas key (-k) is required for creating new measurements')


def start_logger(project_name, verbose=False):
    root_logger = logging.getLogger()
    for log_handler in root_logger.handlers:
        root_logger.removeHandler(log_handler)

    logging.basicConfig(
        format=LOGGING_FORMAT,
        level=logging.INFO if verbose else logging.WARNING
    )
    logging.root.handlers[0].addFilter(logging.Filter(project_name))
