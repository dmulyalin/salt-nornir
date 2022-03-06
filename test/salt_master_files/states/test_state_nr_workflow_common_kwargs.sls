change_step_1:
  nr.workflow:
    - options:
        kwargs: {"table": "brief"}
    - pre_check:
        - name: show_current_time
          function: nr.cli
          kwargs: {"FB": "ceos*", "enable": True}
          args: ["show clock"]
        - name: show_device_version
          function: nr.cli
          kwargs: {"FB": "ceos*", "enable": True}
          args: ["show version"]