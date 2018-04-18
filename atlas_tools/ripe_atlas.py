from datetime import datetime
import logging
import time

from ripe.atlas.cousteau import Ping, Traceroute, AtlasRequest, AtlasSource, \
    AtlasCreateRequest, AtlasResultsRequest, ProbeRequest

logger = logging.getLogger(__name__)


def form_probes(atlas_params, limit=None):
    probe_request = ProbeRequest(**atlas_params)

    probes_data = {}
    for probe in probe_request:
        probes_data[probe['id']] = probe

        if limit is not None and len(probes_data) >= limit:
            break

    return probes_data


class Atlas(object):
    def __init__(self, atlas_api_key, ip_version=4, protocol='ICMP'):
        self.af = ip_version
        self.atlas_api_key = atlas_api_key
        self.protocol = protocol
        self.source = None
        self.trace = None

    def create_traceroute(self, target, packets=1):
        trace = Traceroute(
            af=self.af,
            target=target,
            description="Trace for %s" % target,
            protocol=self.protocol,
            packets=packets,
            skip_dns_check=True
        )

        return trace

    def create_ping(self, target, packets=1):
        ping = Ping(
            af=self.af,
            target=target,
            description="Ping for %s" % target,
            protocol=self.protocol,
            packets=packets,
            skip_dns_check=True
        )

        return ping

    @staticmethod
    def create_source(msm_type, value, num_of_probes):
        source = AtlasSource(
            type=msm_type,
            value=value,
            requested=num_of_probes
        )

        return source

    def create_request(self, measurements, source,
                       is_oneoff=True, packet_interval=5000):
        atlas_request = AtlasCreateRequest(
            start_time=datetime.utcnow(),
            key=self.atlas_api_key,
            measurements=measurements,
            sources=[source],
            packet_interval=packet_interval,
            is_oneoff=is_oneoff
        )

        (is_success, response) = atlas_request.create()
        return is_success, response

    @staticmethod
    def request_results(response, timeout):
        msm_data = list()
        for measurement_num in response:
            kwargs = {
                "msm_id": measurement_num
            }

            # Check measurement status. Move on if measurement stopped or timeout expired.
            while True:
                is_success, results = AtlasStatusRequest(**kwargs).create()
                if is_success:
                    if results['status']['name'] == 'Stopped':
                        break
                    if timeout is not None and time.time() >= results['start_time'] + timeout:
                        logging.warning('measurement %d timeout', measurement_num)
                        break

                    logging.info('measurement %d status: %s', measurement_num, results['status']['name'])
                else:
                    logging.warning('status request failed: %s', results)

                time.sleep(10)
                continue

            # Get measurement data
            while True:
                is_success, results = AtlasResultsRequest(**kwargs).create()
                if is_success:
                    break
                else:
                    logging.warning('status request failed: %s', results)
                    time.sleep(10)
                    continue

            msm_data.extend(results)

        return msm_data


class AtlasStatusRequest(AtlasRequest):
    def __init__(self, **kwargs):
        super(AtlasStatusRequest, self).__init__(**kwargs)

        self.url_path = '/api/v2/measurements/{0}/'
        self.msm_id = kwargs["msm_id"]

        self.url_path = self.url_path.format(self.msm_id)

    def create(self):
        return self.get()
