#!/bin/sh

set -ex

SRC_DIR=$1
INSTALL_DIR=$2

if [ ! -e ${INSTALL_DIR}/.install_finished ]
then
    mkdir -p ${SRC_DIR}
    cd ${SRC_DIR}
    wget http://www.neuron.yale.edu/ftp/neuron/versions/v7.4/nrn-7.4.tar.gz
    tar xzvf nrn-7.4.tar.gz
    cd nrn-7.4
    ./configure --prefix=${INSTALL_DIR} --without-x --with-nrnpython have_cython=no BUILD_RX3D=0
    make -j4 install

    export PATH="${INSTALL_DIR}/x86_64/bin":${PATH}
    export PYTHONPATH="${INSTALL_DIR}/lib/python":${PYTHONPATH}

    python -c 'import neuron'

    touch -f ${INSTALL_DIR}/.install_finished
else
    echo 'Neuron was fully installed in previous build, not rebuilding'
fi
