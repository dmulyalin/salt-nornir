change_step_1:
  nr.workflow:
    - options:
        report_all: True
        filters: {"FB": "*"}
        
    - pre_check_steps:
        - name: ceos1_will_fail
          function: nr.test
          args: ["show hostname", "contains", "ceos2"]
        - name: failed_step_2
          function: nr.test
          args: ["show version", "contains", "non exists pattern"]
        - name: passed_step_1
          function: nr.test
          args: ["show clock", "contains", "Clock source: local"]
        - name: passed_step_2
          function: nr.test
          args: ["show version", "contains", "cEOS"]         
          
    - change:
        - name: apply_logging_config
          function: nr.cfg
          args: ["logging host 5.5.5.5"]
          kwargs: {"plugin": "netmiko"}
          run_if_pass_all: ["ceos1_will_fail", "passed_step_1"]
        - name: apply_ntp_config
          function: nr.cfg
          args: ["ntp server 6.6.6.6"]
          kwargs: {"plugin": "netmiko"}
          run_if_pass_all: ["failed_step_2", "passed_step_1"]