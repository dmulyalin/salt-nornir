# This state target only non existing hosts

change_step_1:
  nr.workflow:
    - options:
        fail_if_any_host_fail_any_step: []
        fail_if_any_host_fail_all_step: []
        fail_if_all_host_fail_any_step: []
        fail_if_all_host_fail_all_step: []
        filters: {"FB": "foobar*"}
    - pre_check:
        - name: pre_check_if_logging_configured
          function: nr.test
          kwargs: {"cli": {"enable": True}, "remove_tasks": False}
          args: ["show run | inc logging", "contains", "5.5.5.5"]
        - name: save_configuration_before
          function: nr.cli
          kwargs: {"enable": True}
          args: ["copy run start"]
          run_if_fail_any: ["pre_check_if_logging_configured"]
