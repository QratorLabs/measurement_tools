import argparse

LOGGING_FORMAT = '%(asctime)s:%(levelname)s:%(name)s:%(message)s'
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

    return parser
