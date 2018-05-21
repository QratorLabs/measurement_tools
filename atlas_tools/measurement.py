from __future__ import print_function

import logging

from atlas_tools.ripe_atlas import Atlas, form_probes

logger = logging.getLogger(__name__)


def chunks(objects_dict, size=10000):
    chunk = []
    for obj in objects_dict.iterkeys():
        chunk.append(obj)
        if len(chunk) >= size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


class Measure(object):
    def __init__(self, target, atlas_api_key,
                 protocol='ICMP', probes_data=None, probe_number=None,
                 timeout=None, probes_features=None, measurements_list=None):
        self.atlas = Atlas(atlas_api_key, protocol=protocol)
        self.name = ''
        self.target = target
        self.timeout = timeout
        self.msm_data = list()
        self.results = list()

        if measurements_list is None:
            self.response = []
        else:
            self.response = measurements_list

        if probes_data is None:
            self.probes_data = self._form_probes(probes_features, probe_number)

        else:
            self.probes_data = probes_data

    def _form_probes(self, probe_params, probe_number):
        logger.info('Forming probes list')
        if probe_params is None:
            probe_params = {}

        if self.response:
            probe_ids = []
            self.msm_data = self.atlas.request_results(self.response, self.timeout)
            for item in self.msm_data:
                probe_ids.append(item['prb_id'])

            probe_params = {'id__in': probe_ids}

        else:
            probe_params['status_name'] = 'Connected'
            probe_params['tags'] = "system-ipv4-works"

        probes_data = form_probes(probe_params, limit=probe_number)
        return probes_data

    def _make_measurement(self):
        pass

    def _form_response(self, measurement):
        logger.info('Forming measurement and waiting response')

        # Atlas limits:
        # 25 measurements per target simultaneously
        # 1000 probes per measurement
        for probes in chunks(self.probes_data, 1000):
            value = ','.join(str(probe_id) for probe_id in probes)
            source = self.atlas.create_source(
                msm_type='probes',
                value=value,
                num_of_probes=len(probes)
            )

            is_success, resp = self.atlas.create_request([measurement], source)
            if is_success:
                self.response.extend(resp['measurements'])

            else:
                logger.error('%s %s', is_success, resp)

    def _flush_results(self):
        pass

    def run(self):
        if not self.response:
            self._make_measurement()
            self.msm_data = self.atlas.request_results(self.response, self.timeout)

        print('Atlas %s measurement IDs: %s' %
              (self.name, ' '.join(str(mid) for mid in self.response)))

        self._flush_results()


class PingMeasure(Measure):
    def __init__(self, *args, **kwargs):
        super(PingMeasure, self).__init__(*args, **kwargs)
        self.name = 'ping'
        self.failed_probes = {}

    def _make_measurement(self):
        measurement = self.atlas.create_ping(target=self.target)
        self._form_response(measurement)

    def _flush_results(self):
        for item in self.msm_data:
            prb_id = item['prb_id']
            rtt = item['min']
            src_ip = item['from']
            try:
                dst_ip = item['dst_addr']

            except KeyError:
                logger.info('Dns resolution failed: %s', prb_id)
                continue

            prb_data = self.probes_data.get(prb_id)
            if prb_data is None:
                continue

            if rtt == -1:
                self.failed_probes[prb_id] = prb_data['country_code']
                continue

            lon, lat = prb_data['geometry']['coordinates']
            data = (
                prb_id, src_ip, dst_ip, prb_data['asn_v4'],
                prb_data['country_code'], lat, lon, rtt
            )
            self.results.append(data)


class TraceMeasure(Measure):
    def __init__(self, *args, **kwargs):
        super(TraceMeasure, self).__init__(*args, **kwargs)
        self.name = 'trace'

    def _make_measurement(self):
        measurement = self.atlas.create_traceroute(target=self.target)
        self._form_response(measurement)

    def _flush_results(self):
        parsed_result = []
        for trace_data in self.msm_data:
            trace = []
            prb_id = trace_data['prb_id']
            dst_ip = trace_data['dst_addr']
            src_ip = trace_data['from']
            for hop in trace_data['result']:
                hop_num = hop['hop']
                if 'error' in hop:
                    trace.append((hop_num, 'error', hop['error']))
                    continue

                hop_ip = hop['result'][0].get('from', '*')
                hop_rtt = hop['result'][0].get('rtt', '-')

                trace.append((hop_num, hop_ip, hop_rtt))

                if hop_ip == dst_ip:
                    trace = []
                    break

            if trace:
                parsed_result.append((src_ip, prb_id, trace))

        self.results.extend(parsed_result)


def ping_measure(atlas_key, target, country=None,
                 probe_limit=None, timeout=None, measurements_list=None):
    probe_params = {}
    if country is not None:
        probe_params['country_code'] = country

    pings = PingMeasure(
        target,
        atlas_key,
        probes_features=probe_params,
        measurements_list=measurements_list,
        probe_number=probe_limit,
        timeout=timeout
    )
    pings.run()

    return pings


def trace_measure(atlas_key, target, protocol, probes_data, timeout=None):
    traces = TraceMeasure(
        target,
        atlas_key,
        protocol=protocol,
        probes_data=probes_data,
        timeout=timeout
    )
    traces.run()

    return traces