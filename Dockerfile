# Copyright (c) 2016-2020, EPFL/Blue Brain Project
#
# This file is part of BluePyOpt <https://github.com/BlueBrain/BluePyOpt>
#
# This library is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License version 3.0 as published
# by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

FROM  andrewosh/binder-base
MAINTAINER Werner Van Geit

USER root

RUN apt-get update
RUN apt-get install -y wget libx11-6 python-dev git build-essential libncurses-dev
RUN wget https://bootstrap.pypa.io/get-pip.py
RUN python get-pip.py
RUN wget http://www.neuron.yale.edu/ftp/neuron/versions/v7.4/nrn-7.4.x86_64.deb
RUN dpkg -i nrn-7.4.x86_64.deb
RUN rm nrn-7.4.x86_64.deb

RUN pip install bluepyopt

ENV PYTHONPATH /usr/local/nrn/lib/python:$PYTHONPATH
