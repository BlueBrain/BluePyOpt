#!/bin/sh

set -ex

INSTALL_DIR=$HOME/local/nrn

mkdir -p src
cd src
wget http://www.neuron.yale.edu/ftp/neuron/versions/v7.4/nrn-7.4.tar.gz
tar xzvf nrn-7.4.tar.gz
cd nrn-7.4
./configure --prefix=${INSTALL_DIR} --without-x --with-nrnpython
make -j4 install

export PATH="${INSTALL_DIR}/x86_64/bin":${PATH}
export PYTHONPATH="${INSTALL_DIR}/lib/python":${PYTHONPATH}
