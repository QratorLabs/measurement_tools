import logging
import time

from ripe_atlas import Atlas, form_probes

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
                 protocol='ICMP', probes_data=None, probe_number=25000,
                 probes_features=None, measurements_list=None):
        self.atlas = Atlas(atlas_api_key, protocol=protocol)
        self.name = ''
        self.target = target
        self.results = list()

        if measurements_list is None:
            self.response = []
        else:
            self.response = measurements_list

        if probes_data is None:
            self.probes_data = self._form_probes(probes_features, probe_number)

        else:
            self.probes_data = probes_data

    def _form_probes(self, probes_features, probe_number):
        logger.info('Forming probes list')
        if probes_features is None:
            probes_features = {}

        if self.response:
            probe_ids = []
            for results in self.atlas.request_results(self.response):
                for item in results:
                    probe_ids.append(item['prb_id'])

            probes_features = {'id__in': probe_ids}

        else:
            probes_features['status_name'] = 'Connected'
            probes_features['tags'] = "system-ipv4-works"

        probes_data = form_probes(**probes_features)
        if len(probes_data) > probe_number:
            logger.warning(
                'More than %s probes (%s), cut to %s',
                probe_number,
                len(probes_data),
                probe_number
            )
            probes_data = {
                probe_id: probes_data[probe_id]
                for probe_id in probes_data.keys()[:probe_number]
                }

        return probes_data

    def _make_measurement(self):
        pass

    def _form_response(self, measurement, time_to_wait=180):
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

        time.sleep(time_to_wait)

    def _flush_results(self, results):
        pass

    def run(self):
        if not self.response:
            self._make_measurement()

        logger.info('Atlas %s measurement ids: %s', self.name, self.response)

        for results in self.atlas.request_results(self.response):
            self._flush_results(results)


class PingMeasure(Measure):
    def __init__(self, *args, **kwargs):
        super(PingMeasure, self).__init__(*args, **kwargs)
        self.name = 'ping'
        self.failed_probes = {}

    def _make_measurement(self):
        measurement = self.atlas.create_ping(target=self.target)
        self._form_response(measurement)

    def _flush_results(self, results):
        for item in results:
            prb_id = item['prb_id']
            rtt = item['min']
            src_ip = item['from']
            try:
                dst_ip = item['dst_addr']

            except KeyError:
                logger.info('Dns resolution failed: %s', prb_id)
                continue

            if rtt == -1:
                self.failed_probes[prb_id] = \
                    self.probes_data[prb_id]['country_code']
                continue

            prb_data = self.probes_data[prb_id]
            asn, region, coords = [
                prb_data[elem]
                for elem in ('asn_v4', 'country_code', 'geometry')
                ]
            lon, lat = coords['coordinates']

            self.results.append(
                (prb_id, src_ip, dst_ip, asn, region, lat, lon, rtt)
            )


class TraceMeasure(Measure):
    def __init__(self, *args, **kwargs):
        super(TraceMeasure, self).__init__(*args, **kwargs)
        self.name = 'trace'

    def _make_measurement(self):
        measurement = self.atlas.create_traceroute(target=self.target)
        self._form_response(measurement)

    def _flush_results(self, results):
        parsed_result = []
        for trace_data in results:
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
