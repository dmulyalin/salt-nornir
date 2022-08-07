# Testing/Development environment for Salt-Nornir Proxy Minion

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

- Machine with minimum of 1 CPU and 2 GByte of RAM
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
