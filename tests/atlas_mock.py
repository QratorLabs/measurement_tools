import functools
import gzip
import json
import os.path

from mock import patch

from ripe.atlas.cousteau import Ping, Traceroute


DATA_PATH = os.path.join(os.path.dirname(__file__), 'atlas_data')
BASE_MEASUREMENT_ID = 10000

_measurement_id = BASE_MEASUREMENT_ID
_measurements = {}

atlas_data_types = {
    'ping': 'ping_results',
    'trace': 'trace_results'
}


def _json_data(name):
    fpath = os.path.join(DATA_PATH, name + '.json.gz')
    with gzip.open(fpath, 'rt') as fd:
        return json.load(fd)


def atlas_http_method(self, method):
    # ensure that every ripe API is properly mocked
    raise NotImplementedError


def atlas_probes(self):
    probes = _json_data('probes')
    return iter(probes)


def atlas_create_request(self):
    global _measurement_id

    assert len(self.measurements) == 1
    measurement = self.measurements[0]

    if isinstance(measurement, Ping):
        _measurements[_measurement_id] = 'ping'
    elif isinstance(measurement, Traceroute):
        _measurements[_measurement_id] = 'trace'
    else:
        raise ValueError(type(measurement).__name__)

    is_success = True
    response = {"measurements": [_measurement_id]}

    _measurement_id += 1

    return is_success, response


def atlas_status(self):
    is_success = True
    response = _json_data('status')
    return is_success, response


def atlas_results(self):
    measurement_type = _measurements[self.msm_id]
    data_type = atlas_data_types[measurement_type]

    is_success = True
    response = _json_data(data_type)
    return is_success, response


def patch_atlas(cls):
    patches = [
        ('ripe.atlas.cousteau.request.AtlasRequest.http_method', atlas_http_method),
        ('ripe.atlas.cousteau.ProbeRequest.__iter__', atlas_probes),
        ('ripe.atlas.cousteau.request.AtlasCreateRequest.create', atlas_create_request),
        ('atlas_tools.ripe_atlas.AtlasStatusRequest.create', atlas_status),
        ('ripe.atlas.cousteau.request.AtlasResultsRequest.create', atlas_results),
    ]
    for patch_spec in patches:
        cls = patch(*patch_spec)(cls)
    return cls
