proxy:
  multiprocessing: true
  proxytype: nornir
    
hosts:
  ceos1:
    hostname: 10.0.1.10
    platform: arista_eos
    port: 6001
    connection_options: {}
    data: {}
    groups:
    - eos_params
  ceos2:
    hostname: 10.0.1.10
    platform: arista_eos
    port: 6002
    connection_options: {}
    data: {}
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
    
nornir:
  actions: {}

defaults:
  data: {}