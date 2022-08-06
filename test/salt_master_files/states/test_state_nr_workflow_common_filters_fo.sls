change_step_1:
  nr.workflow:
    - options:
        # match ceos2 only
        filters: {"FO": [{"data__location": "East City Warehouse"}]}
    - pre_check:
        - name: show_current_time
          function: nr.cli
          kwargs: {"FB": "ceos*"}
          args: ["show clock"]