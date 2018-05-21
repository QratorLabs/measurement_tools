FROM ubuntu:16.04

RUN apt-get update
RUN apt-get install -y gcc g++ git
RUN apt-get install -y python-pip
RUN apt-get install -y libgeos-dev proj-bin libproj-dev python-tk

ARG src_dir=/usr/local/src/atlas
ARG work_dir=/opt/atlas

RUN mkdir -p $src_dir $work_dir
WORKDIR $work_dir

COPY requirements $src_dir/requirements
RUN pip install -r $src_dir/requirements/base.txt
RUN pip install -r $src_dir/requirements/sci.txt
RUN pip install -r $src_dir/requirements/map.txt
RUN pip install -r $src_dir/requirements/geoviews.txt

COPY . $src_dir
RUN pip install $src_dir

RUN python $src_dir/setup.py test
