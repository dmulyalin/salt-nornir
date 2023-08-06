change_step_1:
  nr.workflow:
    - options:
        report_all: True
        filters: {"FB": "*"}
        
    - pre_check_steps:
        - name: run_nr_test_task_with_excption
          function: nr.task
          kwargs:
            excpt: True
            plugin: nornir_salt.plugins.tasks.nr_test
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