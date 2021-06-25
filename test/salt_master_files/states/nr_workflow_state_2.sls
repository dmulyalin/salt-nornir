change_step_1:
  nr.workflow:
    - options:
        fail_if_any_host_fail_any_step: []
        fail_if_any_host_fail_all_step: []
        fail_if_all_host_fail_any_step: []
        fail_if_all_host_fail_all_step: []
        report_all: True
        filters: {"FB": "*"}
    - pre_check:
        - name: pre_check_if_logging_configured
          function: nr.test
          kwargs: {"FB": "ceos*"}
          args: ["show run | inc logging", "contains", "5.5.5.5"]
        - name: save_configuration_before
          function: nr.cli
          kwargs: {"FB": "ceos*"}
          args: ["copy run start"]
          run_if_fail_any: ["pre_check_if_logging_configured"]
    - change:
        - name: apply_logging_config
          function: nr.cfg
          args: ["logging host 5.5.5.5"]
          kwargs: {"plugin": "netmiko"}
          run_if_fail_any: ["pre_check_if_logging_configured"]
    - post_check:
        - name: post_check_if_logging_configured
          function: nr.test
          kwargs: {"FB": "ceos*"}
          args: ["show run | inc logging", "contains", "5.5.5.5"]
          run_if_pass_any: ["apply_logging_config"]
        - name: save_configuration_after
          function: nr.cli
          kwargs: {"FB": "ceos*"}
          args: ["copy run start"]
          run_if_pass_any: ["apply_logging_config"]
    - rollback:
        - name: run_rollback_commands
          function: nr.cfg
          args: ["no logging host 5.5.5.5"]
          kwargs: {"plugin": "netmiko"} 
          run_if_fail_any: ["apply_logging_config", "post_check_if_logging_configured"]