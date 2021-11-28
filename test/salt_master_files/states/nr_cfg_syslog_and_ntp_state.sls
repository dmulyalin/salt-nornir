# apply logging configuration using jinja2 template
configure_logging:
  nr.cfg:
    - filename: salt://templates/nr_syslog_cfg.j2
    - plugin: netmiko

# apply NTP servers configuration using inline commands
configure_ntp:
  nr.task:
    - plugin: nornir_netmiko.tasks.netmiko_send_config
    - config_commands: ["ntp server 7.7.7.7", "ntp server 7.7.7.8"]

# save configuration using netmiko_save_config task plugin
save_configuration:
  nr.task:
    - plugin: nornir_netmiko.tasks.netmiko_save_config