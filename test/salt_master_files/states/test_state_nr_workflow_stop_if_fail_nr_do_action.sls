change_step_1:
  nr.workflow:
    - options:
        report_all: True
        filters: {"FB": "*"}
        
    - pre_check_steps:
        - name: run_test
          function: nr.do
          args: ["test_state_nr_workflow_stop_if_fail_nr_do_action"]
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