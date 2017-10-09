# Atlas tools

Atlas tools is a Python package that works with Ripe Atlas probes.

Features:
* atlas-heatmap - draws a world heatmap of target latency from Atlas probes to target
* atlas-countrymap - draws average countries latency world map
* atlas-nslookupmap - draws domain resolving world map
* atlas-reachability - diagnostic tool that measures availability of target around the world (or country) and traces target from probes with false result.


## Getting Started

Firstly, your should create an [RIPE Atlas](https://atlas.ripe.net/) account. Then accumulate some credits.

### Prerequisites

Install system libs, specified in INSTALL.md

### Installation

```
$ pip install -r requirements.txt
$ python setup.py install
```

### RIPE Atlas features:

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

Thereby, if you want to use 8250 probes for your experiment, RIPE Atlas will create 9 simultaneous measurements with different ids

### Flags
-f, --filename - allows you to specify maps/results filename

You can define single country for your measurement (-c, --country) or limit number of probes of experiment (-n, --number)
```
atlas-availability -t 'target' -k 'your_atlas_api_key' -c RU
atlas-nslookupmap -t 'target' -k 'your_atlas_api_key' -n 3000
```

For maps, its available to use your previous measurements (-m, --msm):
```
atlas-heatmap -t 'target' -k 'your_atlas_api_key' -m msm_id1 msm_id2 ...
```
