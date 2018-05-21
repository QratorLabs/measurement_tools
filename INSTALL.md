### Installation steps

##### System libraries

For Ubuntu:

```bash
apt-get install proj-bin libproj-dev libgeos-dev python-tk
```

##### Python requirements and the package

```bash
pip install -r requirements/base.txt
pip install -r requirements/sci.txt
pip install -r requirements/map.txt
pip install -r requirements/geoviews.txt
pip install .
```


### Docker

Alternatively, you can use __docker__. See Dockerfile in the project root.