# SALTSTACK Nornir

Repository to store Nornir based SALTSTACK modules:

- salt-nornir proxy minion module 
- salt-nornir execution module
- salt-nornir state module

Nornir modules [pull request](https://github.com/saltstack/salt/pull/58393)

## Motivation

Primary reason for developing Nornir proxy is scaling issues. 

Not a secret that normally for each network device we want to manage with SALT, there is a dedicated proxy-minion process must be configured and started. Each such a process consumes from  about 90 MByte or RAM. Meaning, to managed 1000 network devices, ~90 Gbyte of RAM required. That is a significant amount of resources to spent. Problem aggravated by the fact that SSH based proxy-minions use threading to execute tasks and prone to memory leaks [issue](https://github.com/saltstack/salt/issues/38990), workaround - periodic processes restart, that in return raises operational costs of the system.

## Design

<img src="images/Nornir proxy-minion architecture.png">

[Nornir ](https://nornir.readthedocs.io/en/latest/index.html) is an open-source automation software that uses plugins to work with popular libraries such as - NAPALM, Netmiko, Paramiko, NCClient etc. Key difference is that Nornir uses Python to express task execution work flows and runs them in parallel using threading.

Wrapping Nornir in salt-proxy allowing us to use SALTSTACK's systems - schedulers, reactors, returners, mines, pillars, API etc. together with Nornir's capability to effectively run jobs for multiple devices. As a result, single proxy process can deliver configuration or retrieve state from multiple devices. Moreover, Nornir proxy has support for long running connections to devices and shares access to connections with child processes, as a result recommended way to run this proxy is with multiprocessing set to True.

To illustrate, say we want to manage same 1000 devices, but with Nornir proxy. For that we start 10 Nornir processes proxying for 100 devices each, say each process consumes 300 MByte of RAM, resulting in 3 GByte of RAM to run 10 process. Every time we want to run task, new process started, consuming another 300 MByte or RAM. Assume extreme case, we have 4 tasks executing for 1000 devices with process dedicated to each task, that would consume 15 GByte of RAM, once tasks completed and processes destroyed, RAM consumption will fall back to 3 GByte. That is x6 times improvement compared to above example where we need 90 GByte or RAM to manage same number of devices.

## Inter process communication

To facilitate long running connections, proxy-minion designed to use queues for inter-process jobs communication.

<img src="images/nornir_proxy_inter_process_communication_v0.png">

Above architecture helps avoid these problems:
- If no long running connections exists to devices, each new task creates dedicated connections to devices, increasing overall execution time
- Increase in the number of connections increases load on AAA system (Tacacs, Radius) as more tasks result in more authentication requests from devices

## Drawbacks

- Double targeting required to narrow down tasks execution to a subset of hosts
- In addition to knowing how pillar works, one will have to know how [Nornir inventory](https://nornir.readthedocs.io/en/3.0.0/tutorial/inventory.html) structured to use it effectively, as Nornir inventory integrated in proxy-minion pillar
- Tasks executed sequentially one after another, if a lot of tasks scheduled simultaneously, they will consume resource waiting to execute


# How to use

# Installation

From [PyPi distribution](https://pypi.org/project/salt-nornir/0.1.0/)

```
pip install salt_nornir
```

Sample Pillar with Nornir inventory:

```
proxy:
  proxytype: nornir
  
hosts:
  LAB-R1:
    hostname: 192.168.1.10
    platform: ios
    password: user
    username: user
    data: 
      jumphost:
        hostname: 172.16.0.10
        port: 22
        password: admin
        username: admin
  IOL1:
    hostname: 192.168.217.10
    platform: ios
    location: B1
    groups: [lab]
  IOL2:
    hostname: 192.168.217.7
    platform: ios
    location: B2
    groups: [lab]
  IOL3:
    hostname: 192.168.217.11
    platform: ios
    location: B3
    groups: [lab]
    
groups: 
  lab:
    username: nornir
    password: nornir
          
defaults: {}
```

Start salt-proxy process, accept key on master and run commands to explore doc strings for further usage:

```
salt nornir-minion-id sys.doc nr
```
