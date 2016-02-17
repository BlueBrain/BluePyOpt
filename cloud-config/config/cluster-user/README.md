# Cluster User

If you are not the administrator of a cluster, but have access to one, this
document outlines how to setup a working environment that can be used for
optimization.

Note: It is assumed that on this cluster, there is a shared file-system where the
software can be installed once and then used by all allocation of resources.

## Basic Configuration

1. Make sure that there is a virtual environment from which you will run
   `Ansible`, read the documentation [here](../../README.md) to set one up.

2. In the cluster-user directory, modify the `hosts` file to include the cluster head node,
   the contents should be a single stanza with a single line:
    ```
    [neuron-optimizer-worker]
    dns.name.of.head.node
    ```

3. If the username is different for the cluster from on the host it's being
   configured from, the `user_name` in `vars.yaml` will have to be changed to
   this new name.  One can also set an absolute path in for `workspace` in
   `vars.yaml` to modify the installation path.

4. If the python version available on the cluster isn't at least 2.7, then it
   is recommended to modify `python27_build` in `vars.yaml` to be 'true' such
   that a local version of Python will be compiled.

## Installation Information

Run the installation by issuing:
```
$ source ./venv-ansible/bin/activate
$ ansible-playbook site.yaml
```

Once it has run, there should be a `~/workspace` directory on the cluster with
all the required software as described [here](../README.md) under
'Installation Information'.
