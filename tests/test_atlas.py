import os.path
import unittest

from mock import patch

from atlas_mock import patch_atlas, atlas_data_types

from atlas_tools.measurement import form_probes
from atlas_tools.latency_countrymap import create_countrymap
from atlas_tools.latency_heatmap import init_renderer, create_heatmap
from atlas_tools.dns_map import create_map
from atlas_tools.reachability import test_reachability


def _gethostbyaddr(addr):
    return addr, None, None


@patch_atlas
@patch('socket.gethostbyaddr', _gethostbyaddr)
class TestAtlas(unittest.TestCase):
    TARGET = 'example.com'
    DELETE_FILES = True

    def setUp(self):
        init_renderer()

    def test_probes(self):
        probes = form_probes({})
        self.assertIsInstance(probes, dict)

        for probe_id, probe in probes.iteritems():
            self.assertEqual(probe_id, probe['id'])

    def test_countrymap(self):
        atlas_data_types['ping'] = 'ping_results'

        fname = 'countrymap.test.html'
        create_countrymap(fname, None, self.TARGET, 'ICMP')

        self.assertTrue(os.path.exists(fname))
        if self.DELETE_FILES:
            os.unlink(fname)

    def test_heatmap(self):
        atlas_data_types['ping'] = 'ping_results'

        fname = 'heatmap.test.png'
        create_heatmap(fname, None, self.TARGET, 'ICMP')

        self.assertTrue(os.path.exists(fname))
        if self.DELETE_FILES:
            os.unlink(fname)

    def test_dnsmap(self):
        atlas_data_types['ping'] = 'ping_results'

        fname = 'dnsmap.test.html'
        create_map(fname, None, self.TARGET, 'ICMP')

        self.assertTrue(os.path.exists(fname))
        if self.DELETE_FILES:
            os.unlink(fname)

    def test_reachability(self):
        atlas_data_types['ping'] = 'ping_fail_results'

        fname = 'reachability.test.dat'
        test_reachability(fname, None, self.TARGET, 'ICMP')

        self.assertTrue(os.path.exists(fname))
        if self.DELETE_FILES:
            os.unlink(fname)
