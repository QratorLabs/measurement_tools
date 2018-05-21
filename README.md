# Measurement tools

Tools to analyze latency and connectivity of the target using RIPE Atlas.

Available tools:
* `atlas-heatmap` - create a world heatmap of target latencies from Atlas probes;
* `atlas-countrymap` - create a world map which shows target latencies (RTT) from different countries;
* `atlas-dnsmap` - create a world map of DNS resolving results for the target;
* `atlas-reachability` - diagnostic tool that measures availability of the target around the world (or country) and then builds traceroutes from probes with false result.


## Getting Started

Firstly, your should create an [RIPE Atlas](https://atlas.ripe.net/) account and accumulate some credits.


### Installation

See INSTALL.md for the installation steps.


### RIPE Atlas features

Ripe Atlas limits:
* No more than 100 simultaneous measurements
* No more than 1000 probes may be used per measurement
* No more than 100,000 results can be generated per day
* No more than 50 measurement results per second per measurement. This is calculated as the spread divided by the number of probes.
* No more than 1,000,000 credits may be used each day
* No more than 25 ongoing and 25 one-off measurements of the same type running against the same target at any time

Costs:
* Ping - 1 credit per ping per probe
* Trace - 10 credits per trace per probe

Thereby, if you want to use e.g. 8250 probes for your experiment, RIPE Atlas will create 9 simultaneous measurements with different IDs


### Flags

Atlas key (`-k, --key`) is required for creating new measurements (i.e. if `-m` option is missing).

`-f, --filename` flag allows you to specify the output filename.

You can define single country for your measurement (`-c, --country`) or limit number of probes of experiment (`-n, --number`).
By default all active probes are used.
```
atlas-availability -t 'target' -k 'your_atlas_api_key' -c RU
atlas-dnsmap -t 'target' -k 'your_atlas_api_key' -n 3000
```

For all world maps it is possible to use existing ping measurements (`-m, --measurement-ids`):
```
atlas-heatmap -t 'target' -k 'your_atlas_api_key' -m id1 id2 ...
```
In this case Atlas key is not required.

Time (seconds) allocated for measurements can be set by `-T` (`--timeout`) flag. Default value is 15 min.
