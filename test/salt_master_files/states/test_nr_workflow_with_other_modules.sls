state_1:
  nr.workflow:
    - pre_checks:
      - name: pre_check_if_logging_configured
        function: nr.cli
        args: ["show clock"]
    - list_files:
      - name: list_files_in_current_folder
        function: cmd.run
        args: ["ls -l"]
  cmd.run:
    - name: ls -l
