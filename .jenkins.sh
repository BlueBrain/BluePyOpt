#!/bin/bash

set -e
set -x

tox_args='--recreate -e py3-unit-functional-style'

if [ "${os}" = "cscsviz" ]
then
	. /opt/rh/python27/enable
elif [ "${os}" = "Ubuntu-18.04" ]
then
	tox_args="${tox_args}"
fi

which python
python --version

cd $WORKSPACE

#########
# Virtualenv
#########

if [ ! -d "${WORKSPACE}/env" ]; then
  virtualenv ${WORKSPACE}/env --no-site-packages
fi

. ${WORKSPACE}/env/bin/activate
pip install pip --upgrade
pip install tox --upgrade

#####
# Tests
#####

cd  ${WORKSPACE}/BluePyOpt

tox ${tox_args}
