change_step_1:
  nr.workflow:
    - options:
        filters: {"FL": "ceos1"}
    - pre_check:
        - name: show_current_time
          function: nr.cli
          kwargs: {"FB": "ceos*", "enable": True}
          args: ["show clock"]