proxy:
  multiprocessing: true
  proxytype: nornir
    
hosts:
  fceos1:
    hostname: 10.0.1.10
    port: 6001
    groups:
    - eos_params
  fceos2:
    hostname: 10.0.1.10
    port: 6002
    groups:
    - eos_params
  fceos3_1:
    hostname: 10.0.1.10
    port: 5001
    groups:
    - eos_params
  fceos3_2:
    hostname: 10.0.1.10
    port: 5002
    groups:
    - eos_params
  fceos3_3:
    hostname: 10.0.1.10
    port: 5003
    groups:
    - eos_params 
  fceos3_4:
    hostname: 10.0.1.10
    port: 5004
    groups:
    - eos_params
  fceos3_5:
    hostname: 10.0.1.10
    port: 5005
    groups:
    - eos_params
    
groups:
  eos_params:
    connection_options:
      scrapli:
        extras:
          auth_strict_key: false
          ssh_config_file: false
        platform: arista_eos
    password: nornir
    username: nornir
    platform: arista_eos
    
nornir:
  actions: {}

defaults:
  data: {}