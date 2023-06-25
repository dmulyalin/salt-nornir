change_step_1:
  nr.workflow:
    - check_access_lists:
        - name: We have the new access list entries
          function: nr.test
          kwargs:
            suite: salt://tests/test_suite_template_with_job_data_from_workflow.j2
            FB: ceos*
            event_progress: True
            hcache: test_acl_entries
            plugin: scrapli
            job_data: {"access_groups": "test"}
          report: True
          run_if_pass_any: []
          