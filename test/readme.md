# Testing environment for SALT-Nornir proxy Minion

Based on: https://github.com/dehvCurtis/SaltStack-CentOS-Docker

## Setting up cEOS image

Download cEOS-lab.tar.xz image from Arista website and import it in docker:
docker import cEOS-lab.tar.xz ceosimage:4.26.0F

## Start the environment up

Startup both Master and Minion:

$ docker-compose up

This window will display debugging output from the salt master and minions

## Connect to containers

Open new terminal window login to your Master:

$ docker container ls << to get container id
$ docker exec -it salt-master bash << to drop into container shell

Open new terminal window login to your Minion:

$ docker container ls << to get container id
$ docker exec -it salt-minion bash << to drop into container shell

Open new terminal window login to ceos1, but make sure to wait for a few minutes for all EOS agents to start:

$ docker exec -it ceos1 Cli

or to cEOS bash shell:

$  docker exec -it ceos1 bash

## Misc

To rebuild containers:

$ docker-compose build salt-master
$ docker-compose build salt-minion
$ docker-compose build ceos1

To fix master not accepting minion keys need to delete all the previously accepted keys:

$ docker exec -it salt-master bash
$ salt-key -D -y