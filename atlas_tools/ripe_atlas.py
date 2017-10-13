from datetime import datetime
import time

from ripe.atlas.cousteau import Ping, Traceroute, AtlasRequest, AtlasSource, \
    AtlasCreateRequest, AtlasResultsRequest, ProbeRequest


def form_probes(**kwargs):
    probes_data = {}
    probe_request = ProbeRequest(**kwargs)
    for probe in probe_request:
        probes_data[probe['id']] = probe

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
            is_success, results = AtlasStatusRequest(**kwargs).create()
            while not is_success \
                    or results['status']['name'] == 'Ongoing' \
                    or (timeout is not None and
                        time.time() - results['start_time'] < timeout):
                time.sleep(10)
                is_success, results = AtlasStatusRequest(**kwargs).create()

            # Get measurement data
            is_success, results = AtlasResultsRequest(**kwargs).create()
            while not is_success:
                time.sleep(10)
                is_success, results = AtlasResultsRequest(**kwargs).create()

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
