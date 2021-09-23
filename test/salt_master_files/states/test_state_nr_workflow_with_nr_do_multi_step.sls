change_step_1:
  nr.workflow:
    - options:
        report_all: True
          
    - change:
        - name: configure_ntp_nr_do
          function: nr.do
          args: ["configure_ntp"]