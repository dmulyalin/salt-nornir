proxy:
  proxytype: nornir
  multiprocessing: True

hosts: {}
groups: {}
default: {}

jinja_env:
  lstrip_blocks: false
  trim_blocks: false
  
salt_nornir_netbox_pillar:
  use_hosts_filters: true
  url: 'https://192.168.75.129:443'
  ssl_verify: False
  host_add_netbox_data: True
  hosts_filters:
  - name: iosxr1
