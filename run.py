#!/usr/bin/python

import os
import sys
source_root = os.path.abspath(os.path.dirname(__file__))
os.chdir(source_root)
sys.path.append(os.path.abspath(os.path.join(source_root, os.pardir)))

from optparse import OptionParser
import cmd

from availability import ip_test
from latency_heatmap import paint_heatmap

class CommandHandler(cmd.Cmd):
    def __init__(self):
        cmd.Cmd.__init__(self)

        self.intro = 'Regions\n'
        self.doc_header = 'Available commands (type help <topic>):\n'
        self.ruler = ''
        self.prompt = '> '

    def do_EOF(self, args):
        """EOF

Handles the receipt of EOF as a command"""

        return True

    def do_ip_test(self, args):
        """Check target attainability by using Atlas tools.

Usage:
    run.py ip_test -t <target> -k <key> [options ... ]

Available options:
    -t, --target - target of measurements (IPv4 address | domain name)
    -k, --key - your atlas key to create measurements: ATLAS_API_CREATE_KEY
    -c, --country - use probes only for chosen country (default: all active Atlas probes) (country in 2 letter code)
    -p, --protocol - protocol for measurements: ICMP or UDP (default: ICMP)
    -s, --size - output countries with failed ping measurements and its proportion of all failed pings (default: 10)
"""

        parser = OptionParser()
        parser.add_option('-t', '--target', type=str, dest='target', default=None)
        parser.add_option('-k', '--key', type=str, dest='key', default=None)
        parser.add_option('-c', '--country', type=str, dest='country', default=None)
        parser.add_option('-p', '--protocol', type='choice', choices=['ICMP', 'UDP'], dest='protocol', default='ICMP')
        parser.add_option('-s', '--size', type=int, dest='size', default=10)
        opts, args = parser.parse_args(sys.argv[2:])

        if opts.target is None or opts.key is None:
            print "You should set target: '-t (IPv4 address | domain name)'"
            print "You should set key to create atlas measurement: '-k ATLAS_API_CREATE_KEY'"
            return

        ip_test(opts.target, opts.key, proto=opts.protocol, country=opts.country, failed_countries_size=opts.size)

    def do_heatmap(self, args):
        """Paint heatmap by using Atlas tools.

Usage:
    run.py heatmap -t <target> -k <key> [options ... ]

Available options:
    -t, --target - target of measurements (IPv4 address | domain name)
    -k, --key - your atlas key to create measurements: ATLAS_API_CREATE_KEY
    -d, --density - cell number per dergee (default: 4)
    -m, --measurements - comma-separated list of previous measurements_ids (default: new_measurement)
"""

        parser = OptionParser()
        parser.add_option('-t', '--target', type=str, dest='target', default=None)
        parser.add_option('-k', '--key', type=str, dest='key', default=None)
        parser.add_option('-d', '--density', type=int, dest='density', default=4)
        parser.add_option('-m', '--measurements', type=str, action='callback', callback=CommandHandler.make_msm_list, dest='msm_list', default=None)
        opts, args = parser.parse_args(sys.argv[2:])

        if opts.target is None or opts.key is None:
            print "You should set target: '-t (IPv4 address | domain name)'"
            print "You should set key to create atlas measurement: '-k ATLAS_API_CREATE_KEY'"
            return

        paint_heatmap(opts.target, opts.key, opts.density, opts.msm_list)

    @staticmethod
    def make_msm_list(option, opt, value, parser):
        setattr(parser.values, option.dest, value.split(','))

handler = CommandHandler()
if len(sys.argv) == 1:
    handler.onecmd('help')
else:
    handler.onecmd(' '.join(sys.argv[1:]))
