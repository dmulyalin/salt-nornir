change_step_1:
  nr.workflow:  
    - options:
        filters: {"FL": ["ceos1"]}
        
    - change:
        - name: apply_logging_config
          function: nr.cfg
          args: ["logging host 5.5.5.5"]
          kwargs: {"plugin": "netmiko"}
        - name: apply_ntp_config
          function: nr.cfg
          args: ["ntp server 6.6.6.6"]
          kwargs: {"plugin": "netmiko"}