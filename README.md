===========
Atlas tools
===========

Atlas tools is a Python package that works with Ripe Atlas probes.
Features:

* atlas-heatmap - draws a world heatmap of target latency from Atlas probes to target
* atlas-countrymap - draws average countries latency world map
* atlas-nslookupmap - draws domain resolving world map
* availability - diagnostic tool that measures availability of target around the world (or country) and traces target from probes with false result.

------------
Installation
------------

From atlas_tools folder:

.. code:: bash
	$ pip install -r requirements.txt

---------------
Getting Started
---------------

Firstly, your should create an `RIPE Atlas <https://atlas.ripe.net/>` account. Then accumulate some credits.


HeatMap
-------

To create a heatmap:

.. code:: bash
	atlas-heatmap -t 'target' -k 'your_atlas_api_key'

Countrymap
----------

.. code:: bash
	atlas-countrymap -t 'target' -k 'your_atlas_api_key'

NsLookup map
------------

.. code:: bash
	atlas-nslookupmap -t 'target' -k 'your_atlas_api_key'

