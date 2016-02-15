#!/bin/sh

set -ex

mkdir -p src
cd src
wget http://www.neuron.yale.edu/ftp/neuron/versions/v7.4/nrn-7.4.tar.gz
tar xzvf nrn-7.4.tar.gz
cd nrn-7.4
./configure --prefix=$HOME/local/nrn
make -j4 install
