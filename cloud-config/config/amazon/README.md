# Amazon Setup

This documents how an Amazon Web Services cluster can be created.

Note: It is quite easy to run up a large bill on AWS, so the following is only
guidance for setting it up.  Make sure that the costs for setting up a cluster
are fully understood.  It is recommended to often check the AWS console's
`Estimated Billing` to keep track of theses costs.

## Installation

It is assumed that a `virtualenv` exists for `Ansible`.  It is worth reading
the description of `Ansible` and the initial setup in [here](../../README.md).

To access the AWS and `Elastic Computing` components (EC2), the following 
extra components should be installed:

```
$ source ./venv-ansible/activate
$ pip install boto boto3 awscli
```

[Boto](https://pypi.python.org/pypi/boto) is the older generation of AWS/EC2
management utilities, however it is need for Ansible

[boto3](https://github.com/boto/boto3) and [awscli](https://pypi.python.org/pypi/awscli) are useful for interfacing with AWS.


## Creating AWS Cloud

First, one should configure the following in the create_instance.yaml
Playbook:
```
    region: us-west-2
    ami_image: ami-187c9978 # http://cloud-images.ubuntu.com/trusty/current/
    instance_type: t2.nano
    worker_instances: 2
```

Where:

- *region*: is which [AWS Region](http://docs.aws.amazon.com/general/latest/gr/rande.html) that should be used.  This impacts the cost of resources, where the data is stored and which ami's can be used

- *ami_image*: the image that is used as the base for the configuration.
  Generally, a Ubuntu LTS image will work, and the correct one for the chosen
  region must be chosen [from here](http://cloud-images.ubuntu.com/trusty/current/)  A `hvm` instance works.  One may get better performance, at a cost, by using SSD instances or other types.

- *instance_type*: A description of the different instance types is [available
  here](https://aws.amazon.com/ec2/instance-types/).  Usually, the costs grows
  with the computing power.  For the example, the cheapest instance type is
  created, but in a real optimization scenario, the computing resources are
  likely too small to be effective.

- *worker_instances*: How many worker instances to launch, in addition to the
  head node.

To run the creation scrips, the following must exist in the terminal
environment so that the AWS infrastructure can authenticate the client.
```
export AWS_ACCESS_KEY_ID= replace with access id
export AWS_SECRET_ACCESS_KEY= replace with access key
export AWS_REGION= replace with default AWS region
```

It's also a good idea to create the credentials in the ~/.aws/ directory as
described [here.](http://boto3.readthedocs.org/en/latest/guide/quickstart.html#configuration)

Now the simple cloud can be created and launched with:
```
$ source ./venv-ansible/activate
$ ansible-playbook create_instance.yaml
```

### Cloud Details

The above cloud has the following details:

- An [AWS Keypair](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html) with the name `single_cell_opt`.  It will have created a `single_cell_opt.pem` file in the directory it ran, and this file should only be given to people who are allowed to login to the cloud instances.

- An [AWS Virtual Private Cloud](https://aws.amazon.com/vpc/) (VPC) is created
  with the resource tag `single_cell_opt`.  By default, a 10.0.0.0/24 block is
  reserved, and an [Internet Gateway](http://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/VPC_Internet_Gateway.html) is created so the instances can access the internet.

- An [AWS Security Group](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-network-security.html) is created by the name of `single_cell_opt`.  By default, it only allows access via SSH from the full internet (0.0.0.0/0), and allows the instances to access the internet.

## Configuring AWS Cloud

Once the instances are created, then it's a matter of configuring them using
the normal `Ansible` methods.  However, a couple configuration steps must
first be performed:

1. The `hosts` and `amazon_ssh_config` files must be created.  This can be
   accomplished by running the following script:
```
# Note: this can be run with the --dry-run argument to see the output first
$ python gather_config.py
```

2. Then, ansible will take care of the rest of the configuration, as described
   [here.](../../README.md)
```
$ ansible-playbook site.yaml
```

# AWS Tips

From the command line, one can check the running instances:
```
$ aws ec2 describe-instances
```

Or list the current IP addresses
```
$ aws ec2 describe-addresses
```
