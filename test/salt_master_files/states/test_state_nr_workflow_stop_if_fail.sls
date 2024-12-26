change_step_1:
  nr.workflow:
    - options:
        report_all: True
        filters: {"FB": "*"}
        
    - pre_check_steps:
        - name: run_test
          function: nr.test
          args: ["show hostname", "contains", "ceos1"]
          stop_if_fail: True 
          
    - change:
        - name: collect_config
          function: nr.cli
          args: ["show run | inc logging"]
          kwargs: {"plugin": "netmiko", "enable": True}

    - post-change:
        - name: collect_version
          function: nr.cli
          args: ["show version"]
          kwargs: {"plugin": "netmiko"}