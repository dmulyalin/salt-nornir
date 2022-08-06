change_step_1:
  nr.workflow:
    - options:
        fail_if_any_host_fail_any_step: []
        fail_if_any_host_fail_all_step: []
        fail_if_all_host_fail_any_step: []
        fail_if_all_host_fail_all_step: []
        report_all: False
        # match fceos1 only
        filters: {"FO": [{"device_info__model__contains": "EOS", "device_info__version": "foobar.199.42"}, {"device_info__model__contains": "EOS", "device_info__version": "foobar.17rx.42"}], "FL": "fceos1, ceos1"}
        sumtable: False
    - pre_check:
        - name: show_current_time
          function: nr.cli
          kwargs: {"FB": "*ceos*"}
          args: ["show clock"]