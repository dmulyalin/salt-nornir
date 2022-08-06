change_step_1:
  nr.workflow:
    - options:
        fail_if_any_host_fail_any_step: []
        fail_if_any_host_fail_all_step: []
        fail_if_all_host_fail_any_step: []
        fail_if_all_host_fail_all_step: []
        report_all: False
        filters: {"FB": "ceos1"}
        hcache: True
        dcache: False
        sumtable: False
    # define pre-check steps
    - pre_check:
        - name: pre_check_pull_config
          function: nr.nc
          kwargs: 
            source: candidate
            plugin: ncclient
            filter: |
              <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
                <interface></interface>
              </interfaces>
          args: ["get_config"]