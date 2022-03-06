change_step_1:
  nr.workflow:
    - options:
        fail_if_any_host_fail_any_step: []
        fail_if_any_host_fail_all_step: []
        fail_if_all_host_fail_any_step: []
        fail_if_all_host_fail_all_step: []
    - pre_check:
        - name: pre_check_if_logging_configured
          function: nr.cli
          args: ["show clock"]

