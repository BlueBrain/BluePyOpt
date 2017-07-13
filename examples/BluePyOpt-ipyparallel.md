# BluePyOpt Parallelization with ipyparallel

By default, when the optimization is being run, it only uses a single core.
If you have access to a multicore machine, or a cluster of multicore machines, the extra processing power can easily be leveraged by using `BluePyOpt` in combination with [ipyparallel](https://ipyparallel.readthedocs.io/en/latest/).

# Quick Introduction to ipyparallel

The `ipyparallel` project is uses the IPython/Jupyter protocol for simplifying distributing work over many cores.
In the simplest terms, a worker (called an `ipengine`) is started per core.
It is directed by a master process (called an `ipcontroller`) to perform work.
The `ipcontroller` gets its work from clients that connect to it.

## Installation

`ipyparallel` can be installed using pip:

    # create and activate virtualenv
    $ venv venv-ipyparellel; source venv-ipyparellel/bin/activate

    # install ipyparallel
    (venv-ipyparellel)$ pip install ipyparallel

    #check that it installed correctly
    (venv-ipyparellel)$ ipcontroller -V
    [returns a version number]

With `ipyparallel` installed, let's perform a simple parallel operation.
To fully understand what is happening, it is probably best to open three windows.
One for the `ipcontroller`, one for the `ipengines`, and lastly one for the client.

In the `ipcontroller` window:

    # activate the virtualenv
    $ source venv-ipyparellel/bin/activate

    # run the ipcontroller
    (venv-ipyparellel)$ ipcontroller

In the `ipengine` window:

    # activate the virtualenv
    $ source venv-ipyparellel/bin/activate

    # start two ipengines
    (venv-ipyparellel)$ ipengine &; ipengine &

In the client window:

    # activate the virtualenv
    $ source venv-ipyparellel/bin/activate

    #start python
    (venv-ipyparellel)$ python

    >>> from ipyparallel import Client
    >>> c = Client()  # creates a connection to the server
    >>> view = c[:] # creates a 'view' of all the workers
    >>> import socket
    >>> view.apply_sync(socket.gethostname)  # run the function gethostname on all ipengines
    ['your_hostname', 'your_hostname']

If that works, it means that you can parallelize work on a single computer, but across every processor: just start one `ipengine` per processor, and `ipyparallel` will handle the rest.
Several things should be noted here:
* `ipyparallel` will attempt to use an [ipython profile](http://ipython.readthedocs.io/en/stable/config/intro.html#profiles) to coordinate the initial startup between the controller, its workers, and the client.  That is why the above the above commands never included explicit host information
* using the `ipcluster` command one can simplify starting multiple instances on the same machine, and will require only a single window instead of one for the `ipcluster` and the `ipengines`.  Ex:

        # start an ipyparellel cluster with 1 head node, and as many processors as the current machine has
        (venv-ipyparellel)$ ipcluster start

* With a cluster of machines, if there is a shared file system, parallelizing across all the machines and their processors is a matter of starting `ipengine`s on each of the machines

# Running the L5_PC example

With some experience with `ipyparallel`, it's time to try and run an optimization using it.

## Installation

If you already have a working environment, with `BluePyOpt`, [NEURON](http://www.neuron.yale.edu/neuron/) and `ipyparallel` installed, you can skip this step.

There are multiple ways to install the full stack to perform this optimization: using `ansible` (documented [here](https://github.com/BlueBrain/BluePyOpt/tree/master/cloud-config)) as well as using [conda](https://conda.io/docs/).  For simplicity's sake, we will be using the latter to setup an environment that includes all the requirements, including a `NEURON` installation that includes all required mechanisms compiled in.  Note: this only works for `Linux` and `macOS`.


Follow [these instructions](https://conda.io/docs/install/quick.html) to install `conda`.
Make sure that the `conda` command runs (make sure that the install location is included on your path.)

Install the `anaconda` environment manager:
    
    $ conda install anaconda-client

Install the BluePyOpt suite:

    $ conda env create bluepyopt/gecco2017

Activate it, and check that it works:

    $ source activate gecco2017
    $ python
    >>> import neuron

If that works, you should have a properly working environment.

## Running

Start a cluster of `ipengines` (in one window):

    (gecco2017)$ ipcluster start

In the `BluePyOpt` [git](https://github.com/BlueBrain/BluePyOpt/) repository, there is an `examples/l5pc` directory.
From there, one can launch the optimization like so (in another window):

    (gecco2017)$ ./opt_l5pc.py \
        -vv                    \
        --checkpoint check.pkl \
        --offspring_size=50    \
        --max_ngen=2           \
        --ipyparallel          \
        --start

This will run, and based on the number of generations (2 in the example above) and offspring (50 in the example above) the amount of work (2*50 = 100 units) will be distributed across the workers.

One should get output something along the lines of:

    DEBUG:root:Using ipyparallel with 8 engines
    DEBUG:root:Doing start or continue
    DEBUG:traitlets:Importing canning map
    DEBUG:root:Generation took 0:01:10.813599
    DEBUG:root:Generation took 0:01:33.446949
    INFO:__main__:gen       nevals  avg     std     min     max
    1       2       4862.45 123.749 4738.7  4986.2
    2       2       4068.58 1604.07 1307.39 5242.02
