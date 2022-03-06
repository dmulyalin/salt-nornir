#!yaml

change_step_1:
  nr.workflow:
    - pre_check:
        - name: pre_cpre_check_config_gen
          function: nr.cfg_gen
          kwargs: {"filename": "salt://templates/per_host_cfg_snmp_ceos1/{{ host.name }}.txt"}
    - apply_config:
        - name: apply_config
          function: nr.cfg
          run_if_pass_any: ["pre_cpre_check_config_gen"]
          kwargs: {"filename": "salt://templates/per_host_cfg_snmp_ceos1/{{ host.name }}.txt"}