change_step_1:
  nr.workflow:        
    - options:
        hcache: False
        dcache: True
    - change:
      - name: get_interfaces
        function: nr.cli
        args: ["show run"]
        kwargs: 
          run_ttp: "salt://ttp/test_state_nr_workflow_hcache_usage.txt"
          enable: True
      - name: apply_mtu_config
        function: nr.cfg
        args: []
        kwargs: 
          plugin: "netmiko"
          filename: "salt://templates/test_state_nr_workflow_dcache_usage.txt"