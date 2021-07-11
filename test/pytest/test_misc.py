import logging
import pprint
import json

log = logging.getLogger(__name__)

try:
    import salt.client
    import salt.config
    import salt.utils.event
    import salt.exceptions

    HAS_SALT = True
except:
    HAS_SALT = False
    raise SystemExit("SALT Nonrir Tests - failed importing SALT libraries")

if HAS_SALT:
    # initiate execution modules client to run 'salt xyz command' commands
    client = salt.client.LocalClient()
    opts = salt.config.client_config("/etc/salt/master")
    event = salt.utils.event.get_event(
        "master", sock_dir=opts["sock_dir"], transport=opts["transport"], opts=opts
    )


def test_nr_cli_with_event_failed():
    """Test firing event for failed tasks"""
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={
            "tests": [["show clock", "contains", "NTP", "check_ntp"]],
            "event_failed": True,
            "FB": "ceos1",
        },
        tgt_type="glob",
        timeout=60,
    )
    event_ceos1 = event.get_event(
        wait=10, tag="nornir-proxy/nrp1/ceos1/task/failed/check_ntp"
    )
    # pprint.pprint(event_ceos1)
    # {'_stamp': '2021-05-22T04:58:05.022937',
    #  'cmd': '_minion_event',
    #  'data': {'changed': False,
    #           'connection_retry': 0,
    #           'criteria': 'NTP',
    #           'diff': '',
    #           'exception': 'Pattern not in output',
    #           'failed': True,
    #           'host': 'ceos1',
    #           'name': 'check_ntp',
    #           'result': 'FAIL',
    #           'success': False,
    #           'task': 'show clock',
    #           'task_retry': 0,
    #           'test': 'contains'},
    #  'id': 'nrp1',
    #  'pretag': None,
    #  'tag': 'nornir-proxy/nrp1/ceos1/task/failed/check_ntp'}
    assert event_ceos1["tag"] == "nornir-proxy/nrp1/ceos1/task/failed/check_ntp"
    assert event_ceos1["data"]["failed"] == True


# test_nr_cli_with_event_failed()


def test_to_file_processor():
    """
    run task and save results to file, use cat command to verify
    results saved under base url and aliases file is populated accordingly
    """
    res = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"tf": "show_clock_tf_test"},
        tgt_type="glob",
        timeout=60,
    )
    tf_aliases = client.cmd(
        tgt="nrp1",
        fun="cmd.run",
        arg=["cat /var/salt-nornir/nrp1/files/tf_aliases.json"],
    )
    tf_aliases = json.loads(tf_aliases["nrp1"])

    file_content_ceos1 = client.cmd(
        tgt="nrp1",
        fun="cmd.run",
        arg=["cat {}".format(tf_aliases["show_clock_tf_test"]["ceos1"][0]["filename"])],
    )
    file_content_ceos2 = client.cmd(
        tgt="nrp1",
        fun="cmd.run",
        arg=["cat {}".format(tf_aliases["show_clock_tf_test"]["ceos2"][0]["filename"])],
    )

    assert str(res["nrp1"]["ceos1"]["show clock"]) == file_content_ceos1["nrp1"]
    assert str(res["nrp1"]["ceos2"]["show clock"]) == file_content_ceos2["nrp1"]
