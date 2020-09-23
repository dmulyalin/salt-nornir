# SALTSTACK Nornir

Work in progress.

Repository to store Nornir based SALTSTACK modules:

- salt-nornir proxy minion module <- done
- salt-nornir execution module <- done
- salt-nornir state module <- not completed
- salt-nornir runner module <- not started

Nornir modules [pull request](https://github.com/saltstack/salt/pull/58393)

## Motivation

Primary reason for developing Nornir proxy is scaling issues. 

Not a secret that normally for each network device we want to manage with SALT, there is a dedicated proxy-minion process must be spawned and configured. Each such a process consumes from 40 to 70 MByte or RAM. Meaning, to managed 1000 network devices, 40-70 Gbyte of RAM required. That is a big amount of resources to spent. Problem aggravated by the fact that SSH based proxy-minions have to run with multiprocessing mode off, resulting in use of threading to run tasks, but threading prone to memory leaks [issue ](https://github.com/saltstack/salt/issues/38990) and the cure is to periodically restart processes, raising operational costs of overall system.

## Design

<img src="Nornir proxy-minion architecture.png">

[Nornir ](https://nornir.readthedocs.io/en/latest/index.html) is an open-source automation software that uses same libraries under the hood as some other Network proxy-minion - NAPALM, Netmiko, Paramiko and NCClient. The key differentiator of Norninr is that it uses Python to express task execution workflows and runs them in parallel using threading. 

Wrapping Norninr in salt-proxy allowing us to use SALT systems such as schedulers, reactors, returners, mines, pillars, API etc. together with Nornir's capability to effectively run jobs for multiple devices. As a result, single proxy process can deliver configuration or retrieve state from multiple devices simultaneously. Moreover, due to Nornir stateless nature, proxy can and should operate with multiprocessing set to True.

To illustrate, say we want to manage same 1000 devices, but with Nornir proxy. For that we start 10 Nornir processes proxying for 100 devices each, say each process consumes 100 MByte of RAM, resulting in 1 GByte of RAM to run 10 process. Every time we want to run task, new process started, consuming another 100 MByte or RAM. Assume extreme case, we have 4 tasks running in parallel to 1000 devices with process dedicated to each task, that would consume 5 GByte of RAM, once tasks completed and processes destroyed, RAM consumption will fall back to 1 GByte. That is, in author's opinion, quite an improvement compared to above example where we used 40-70 GByte or RAM to manage same number of devices.

## Drawbacks

- Double targeting required to narrow down tasks execution to a subset of hosts
- No long running connections exists to devices, each new task creates dedicated connections to devices, increasing overall execution time
- Load on AAA system (Tacacs, Radius) will increase as more tasks will result in more authentication requests from devices
- In addition to knowing how pillar works, one will have to know how [Nornir inventory](https://nornir.readthedocs.io/en/3.0.0/tutorial/inventory.html) structured to use it effectively, as Nornir inventory integrated in proxy-minion pillar


# How to use

Place files in appropriate directories:

```
salt://_proxy/nornir_proxy_module.py
salt://_modules/nornir_execution_module.py
salt://_states/nornir_state_module.py
```

Sample Pillar with Nornir inventory:

```
proxy:
  proxytype: nornir
  num_workers: 100         
  process_count_max: 3     
  multiprocessing: True        
  
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
    connection_options: 
      napalm:
        optional_args: {dest_file_system: "system:"}
          
defaults: {}
```

Start salt-proxy process, accept key on master and run commands to explore doc strings for further usage:

```
salt nornir-minion-id saltutil.sync_all
salt nornir-minion-id sys.doc nr.cli
salt nornir-minion-id sys.doc nr.cfg
salt nornir-minion-id sys.doc nr.inventory
```
