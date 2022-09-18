1. [Testing and Development environment for Salt-Nornir Proxy Minion](#testing-and-development-environment-for-salt-nornir-proxy-minion)
2. [Prerequisites](#prerequisites)
3. [Setting up cEOS image](#setting-up-ceos-image)
4. [Setting up Juniper vSRX Virtual Machine](#setting-up-juniper-vsrx-virtual-machine)
5. [Setting up required folders structure](#setting-up-required-folders-structure)
6. [Building and starting development containers](#building-and-starting-development-containers)
7. [Access containers shell](#access-containers-shell)
8. [Working with environment](#working-with-environment)
9. [Running tests](#running-tests)
10. [Setting up Jupyter LAB](#setting-up-jupyter-lab)
11. [Adding Netbox Container](#adding-netbox-container)
12. [Troubleshooting](#troubleshooting)

# Testing and Development environment for Salt-Nornir Proxy Minion

Salt-Nornir testing environment consists of a set of docker containers
and virtual machines:

- salt-master - runs `salt-master` process and salt-api process
- ceos1 - this container runs first Arista cEOS device
- ceos2 - this container runs second Arista cEOS device
- vSRX-1 - runs Juniper vSRX Virtual Machine router
- salt-nornir-fakenos - runs FakeNOS fake network of 402 Arista cEOS devices
- salt-minion-nrp1 - runs `nrp1` Salt-Nornir proxy minion to manage ceos1 and ceos2 devices
- salt-minion-nrp2 - runs `nrp2` Salt-Nornir proxy minion to manage:
  - vSRX-1 VM Router
  - always on sandox devices csr1000v-1 - sandbox-iosxe-latest-1.cisco.com
  - always on sandox devices iosxr1 - sandbox-iosxr-1.cisco.com
  - always on sandox devices nxos1 - sandbox-nxos-1.cisco.com
- salt-minion-nrp3 - runs `nrp3` Salt-Nornir proxy minion to manage fakenos Arista cEOS devices

## Prerequisites

Test environment has these dependencies:

- Machine with minimum of 1 CPU, 2 GByte of RAM - the more the better - and Internet access
- Docker Compatible Operating System to host docker containers
- [Docker](https://docs.docker.com/engine/install/) - to run containers
- [Docker-Compose](https://docs.docker.com/compose/install/) - to start the environment
- [GIT](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) - to clone repositories from github

## Setting up cEOS image

This is only required if need to run tests using `nrp1` proxy minion.

Register on Arista website, download
[cEOS-lab.tar.xyz image](https://www.arista.com/en/support/software-download), copy
image file on machine running docker and import image into docker:

```
docker import cEOS-lab.tar.xyz ceosimage:xyz
```

## Setting up Juniper vSRX Virtual Machine

This is only required if need to run `salt-nornir/test/pytest/test_interop_juniper.py`
tests.

Download vSRX VM from Juniper and run it using configuration from
in `salt-nornir/test/vSRX-1.conf` file adjusting management IP if required in
both vSXR configuration and `salt-nornir/test/pytest/test_interop_juniper.py`
file.

## Setting up required folders structure

To facilitate development process, docker containers build uses local copies of
`salt-nornir`, `nornir-salt` and `fakenos` libraries without installing them from
PyPI, these libraries mounted as a volumes to containers Python `site-packages/`
directory. That allows to introduce changes to the code and after container restart
this changes take effect immidiately.

1. Create directory to hold test environment:

```
mkdir salt-nornir-dev
cd salt-nornir-dev
```

2. Clone repositories code from github

```
git clone https://github.com/dmulyalin/nornir-salt.git
git clone https://github.com/dmulyalin/salt-nornir.git
git clone https://github.com/dmulyalin/fakenos.git
```

## Building and starting development containers

Build containers using docker-compose:

```
cd salt-nornir/
docker-compose -f docker-compose.rocky.py39.yaml up
```

## Access containers shell

Open new terminal window to access Master shell:

```
docker exec -it salt-master bash
```

Open new terminal window login to your Minion:

```
docker exec -it salt-minion-nrp1 bash
```

Open new terminal window to access ceos1 CLI:

```
docker exec -it ceos1 Cli
```

To access ceos1 bash shell:

```
docker exec -it ceos1 bash
```

## Working with environment

Most of the interaction is happening on master, to access master shell run:

```
docker exec -it salt-master bash
```

From here can run any of salt utilities commands e.g.:

```
salt --versions-report
salt "*" test.ping
salt nrp1 nr.cli "show clock"
salt nrp2 nr.nornir version
salt-run nr.call cli "show clock" FB=ceos1
```

All files from `salt-nornir/test/salt_master_files/` mounted under `/etc/salt/` 
directory within salt-master container, as a result any changes to any of the files in 
`salt_master_files` directory visible within master container and accessible to master 
process.

## Running tests

All tests contained within `salt-nornir/test/pytest/` directory and mounted as a volume
to salt-master container under `/tmp/pytest/` path.

To run tests, access salt-master shell, navigate to `/tmp/pytest/` directory and run tests
using pytest:

```
docker exec -it salt-master bash
cd /tmp/pytest/
pytest -vv
```

## Setting up Jupyter LAB

This is optional, but makes it very convenient to interact with test environment using
[Jupyter LAB](https://jupyter.org/) WEB Interface.

To [install Jupyter LAB](https://jupyter.org/install):

```
pip install jupyterlab
```

Optional - Generate Jupyter LAB config and set WEB UI password:

```
jupyter notebook --generate-config
jupyter notebook password
```

Navigate to operating system root directory and start Jupyter LAB using `nohup`:

```
cd /
nohup jupyter lab --allow-root --ip=<your host ip> --port=8888
```

Thanks to using `nohup` terminal window can be closed.

Browse to `http://<your host ip>:8888` to access Jupyter LAB WEB UI.

To restart Jupyter LAB find its process id, kill it and start it again:

```
ps -A | grep jup
kill -9 <jupyter lab pid>
cd /
nohup jupyter lab --allow-root --ip=<your host ip> --port=8888
```

## Adding Netbox Container

To test functions related to integration with Netbox need to 
spun up Netbox container from 
[netbox-docker repository](https://github.com/netbox-community/netbox-docker)

To test secrets need to add netbox-secretstore plugin to netbox-docker 
container deployment following 
[documentation instructions](https://github.com/netbox-community/netbox-docker/wiki/Using-Netbox-Plugins)

Once Netbox instance is up and running, need to update file 
`salt_nornir/test/pytest/netbox_data.py` with correct URL.

To prepare Netbox for testing need to populate it with data, it is 
automatically done on Pytest invocation or can be done manually running
the script:

```
python3 salt_nornir/test/pytest/netbox_data.py
```

Running netbox_data script will prompt user for input to decide on what to do.
For example, to clean and re-populate Netbox can use option 3:

```
[root@salt-master pytest]# python3 netbox_data.py 
Select what to do with Netbox:
1 - cleanup
2 - populate
3 - cleanup first, next populate
[1,2,3]: 3
INFO:__main__:netbox_data: deleting netbox_secretstore secrets
INFO:__main__:netbox_data obtained netbox-secretsore session key
INFO:__main__:netbox_data: deleting netbox_secretstore secret roles
INFO:__main__:netbox_data obtained netbox-secretsore session key
INFO:__main__:netbox_data: deleting devices
INFO:__main__:netbox_data: deleting ip addresses
INFO:__main__:netbox_data: delete device roles
INFO:__main__:netbox_data: deleting device types
INFO:__main__:netbox_data: deleting platforms
INFO:__main__:netbox_data: deleting manufacturers
INFO:__main__:netbox_data: deleting tags
INFO:__main__:netbox_data: deleting racks
INFO:__main__:netbox_data: deleting sites
INFO:__main__:netbox_data: deleting regions
INFO:__main__:netbox_data: deleting tenants
INFO:__main__:netbox_data: creating regions
INFO:__main__:netbox_data: creating tenants
INFO:__main__:netbox_data: creating sites
INFO:__main__:netbox_data: creating racks
INFO:__main__:netbox_data: creating manufacturers
INFO:__main__:netbox_data: creating device types
INFO:__main__:netbox_data: creating device roles
INFO:__main__:netbox_data: creating platforms
INFO:__main__:netbox_data: creating ip addresses
INFO:__main__:netbox_data: creating tags
INFO:__main__:netbox_data: creating devices
INFO:__main__:netbox_data: creating interfaces
INFO:__main__:netbox_data: associating primary ip adresses to devices
INFO:__main__:netbox_data: creating netbox_secretstore secret roles
INFO:__main__:netbox_data obtained netbox-secretsore session key
INFO:__main__:netbox_data: creating netbox_secretstore secrets
INFO:__main__:netbox_data obtained netbox-secretsore session key
[root@salt-master pytest]# 
```

Test environment configured to use default netbox-docker credentials of:

- Username: admin
- Password: admin
- API Token: 0123456789abcdef0123456789abcdef01234567

If any of above changes, need to make sure to adjust respective `netbox_data.py`
sript variables.

## Troubleshooting

### To rebuild containers

Delete containers and images:

```
docker container ls -a <<- list CONTAINER IDs
docker rm <CONTAINER ID> <<- remove remove salt-master, salt-minion-nrp1/2/3 containers
docker image ls <<- list IMAGE ID
docker image rm -f <IMAGE ID> <<- remove salt-master, salt-minion-nrp1/2/3 images
```

Clean up master PKI directory as it is mounted as a volume to salt-master, without
cleaning it up it will contain keys for previously build minions containers and
master will reject requests from rebuild minion containers:

```
rm -rfd salt-nornir/test/salt_master_files/pki
```

### To restart containers

To restart containers can run below command, but sometimes need to run it twice as
on first run container shutted down but not restarted by docker:

```
docker restart salt-minion-nrp1
```

### To fix master not accepting minion keys

In case salt-minion container have been rebuild need to delete all the previously
accepted keys on master. Master configured to automatically trust/accept all minions
keys:

```
docker exec -it salt-master bash
salt-key -D -y
```
