change_step_1:
  nr.workflow:
    - options:
        report_all: True
          
    - change:
        - name: apply_logging_config_nr_do
          function: nr.do
          args: ["configure_logging"]