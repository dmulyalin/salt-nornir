change_step_1:
  nr.workflow:
    - options:
        sumtable: True
        report_all: False
    - pre_check:
        - name: collect_clock
          function: nr.cli
          args: ["show clock"]
        - name: collect_version_ceos1_only
          function: nr.cli
          args: ["show version"]
          kwargs: {"FB": "ceos2"}
        - name: sleep_1_second
          function: nr.task
          kwargs:
            plugin: nornir_salt.plugins.tasks.sleep
            sleep_for: 1
        - name: collect_clock
          function: nr.cli
          args: ["show clock"]
        - name: step_with_error
          function: nr.task
          kwargs:
            plugin: nornir_salt.plugins.tasks.nr_test
            excpt: True  