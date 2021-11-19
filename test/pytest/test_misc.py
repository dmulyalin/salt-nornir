import logging
import pprint
import json
import time
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
        arg=["cat /var/salt-nornir/nrp1/files/tf_index_nrp1.json"],
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

    
def test_results_dump_directive():
    res = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show hostname"],
        kwarg={"dump": "show_clock_full_results"},
        tgt_type="glob",
        timeout=60,
    )
    tf_aliases = client.cmd(
        tgt="nrp1",
        fun="cmd.run",
        arg=["cat /var/salt-nornir/nrp1/files/tf_index_nrp1.json"],
    )
    tf_aliases = json.loads(tf_aliases["nrp1"])

    file_content = client.cmd(
        tgt="nrp1",
        fun="cmd.run",
        arg=["cat {}".format(tf_aliases["show_clock_full_results"]["nrp1"][0]["filename"])],
    )
    file_content = file_content["nrp1"]
    # print(file_content)
    # print(pprint.pformat(res, indent=2, width=150))
    assert (
        "ceos1" in file_content and
        "ceos2" in file_content and
        "show hostname" in file_content and
        "Hostname: ceos" in file_content and
        "FQDN" in file_content 
    )
# test_results_dump_directive()


def test_nornir_hosts():
    res = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["hosts"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )
    assert res["nrp1"] == ["ceos1", "ceos2"]
# test_nornir_hosts()


def test_nornir_hosts_with_filter():
    res = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["hosts"],
        kwarg={"FB": "ceos1"},
        tgt_type="glob",
        timeout=60,
    )
    assert res["nrp1"] == ["ceos1"]
# test_nornir_hosts()


def test_host_results_hcache():
    res = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"hcache": True},
        tgt_type="glob",
        timeout=60,
    )
    inventory = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory"],
        tgt_type="glob",
        timeout=60,
    )
    clear = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["clear_hcache"],
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(inventory) 
    assert "hcache" in inventory["nrp1"]["hosts"]["ceos1"]["data"]
    assert "hcache" in inventory["nrp1"]["hosts"]["ceos2"]["data"]
    assert "show clock" in inventory["nrp1"]["hosts"]["ceos1"]["data"]["hcache"]
    assert "show clock" in inventory["nrp1"]["hosts"]["ceos2"]["data"]["hcache"]
    
# test_host_results_hcache()


def test_host_results_hcache_key():
    res = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"hcache": "cache1"},
        tgt_type="glob",
        timeout=60,
    )
    inventory = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory"],
        tgt_type="glob",
        timeout=60,
    )
    clear = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["clear_hcache"],
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(inventory) 
    assert "cache1" in inventory["nrp1"]["hosts"]["ceos1"]["data"]
    assert "cache1" in inventory["nrp1"]["hosts"]["ceos2"]["data"]
    assert "show clock" in inventory["nrp1"]["hosts"]["ceos1"]["data"]["cache1"]
    assert "show clock" in inventory["nrp1"]["hosts"]["ceos2"]["data"]["cache1"]
    
# test_host_results_hcache_key()


def test_host_results_hcache_clear_all():
    res = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"hcache": True},
        tgt_type="glob",
        timeout=60,
    )
    clear = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["clear_hcache"],
        tgt_type="glob",
        timeout=60,
    )
    inventory = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory"],
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(clear) 
    assert clear["nrp1"]["ceos1"]["nornir_salt.plugins.tasks.salt_clear_hcache"]["hcache"] == True
    assert clear["nrp1"]["ceos2"]["nornir_salt.plugins.tasks.salt_clear_hcache"]["hcache"] == True
    assert "hcache" not in inventory["nrp1"]["hosts"]["ceos1"]["data"]
    assert "hcache" not in inventory["nrp1"]["hosts"]["ceos2"]["data"]
    
# test_host_results_hcache_clear_all()


def test_host_results_hcache_clear_by_key():
    res = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"hcache": "cache1234"},
        tgt_type="glob",
        timeout=60,
    )
    clear = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["clear_hcache"],
        kwarg={"cache_keys": ["cache1234", "cache4321"]},
        tgt_type="glob",
        timeout=60,
    )
    inventory = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory"],
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(clear) 
    assert clear["nrp1"]["ceos1"]["nornir_salt.plugins.tasks.salt_clear_hcache"]["cache1234"] == True
    assert clear["nrp1"]["ceos2"]["nornir_salt.plugins.tasks.salt_clear_hcache"]["cache1234"] == True
    assert clear["nrp1"]["ceos1"]["nornir_salt.plugins.tasks.salt_clear_hcache"]["cache4321"] == False
    assert clear["nrp1"]["ceos2"]["nornir_salt.plugins.tasks.salt_clear_hcache"]["cache4321"] == False
    assert "cache1234" not in inventory["nrp1"]["hosts"]["ceos1"]["data"]
    assert "cache1234" not in inventory["nrp1"]["hosts"]["ceos2"]["data"]
    
# test_host_results_hcache_clear_by_key()


def test_host_results_dcache():
    res = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"dcache": True},
        tgt_type="glob",
        timeout=60,
    )
    inventory = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory"],
        tgt_type="glob",
        timeout=60,
    )
    clear = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["clear_dcache"],
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(inventory) 
    assert "dcache" in inventory["nrp1"]["defaults"]["data"]
    assert "dcache" in inventory["nrp1"]["defaults"]["data"]
    assert "show clock" in inventory["nrp1"]["defaults"]["data"]["dcache"]["ceos1"]
    assert "show clock" in inventory["nrp1"]["defaults"]["data"]["dcache"]["ceos2"]
    
# test_host_results_dcache()


def test_host_results_dcache_key():
    res = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"dcache": "cache1"},
        tgt_type="glob",
        timeout=60,
    )
    inventory = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory"],
        tgt_type="glob",
        timeout=60,
    )
    clear = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["clear_dcache"],
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(inventory) 
    assert "cache1" in inventory["nrp1"]["defaults"]["data"]
    assert "cache1" in inventory["nrp1"]["defaults"]["data"]
    assert "show clock" in inventory["nrp1"]["defaults"]["data"]["cache1"]["ceos1"]
    assert "show clock" in inventory["nrp1"]["defaults"]["data"]["cache1"]["ceos2"]
    
# test_host_results_dcache_key()


def test_host_results_dcache_clear_all():
    res = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"dcache": True},
        tgt_type="glob",
        timeout=60,
    )
    clear = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["clear_dcache"],
        tgt_type="glob",
        timeout=60,
    )
    inventory = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory"],
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(clear) 
    assert clear['nrp1']['dcache'] == True
    assert "dcache" not in inventory["nrp1"]["defaults"]["data"]
    assert "dcache" not in inventory["nrp1"]["defaults"]["data"]
    
# test_host_results_dcache_clear_all()


def test_host_results_dcache_clear_by_key():
    res = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"dcache": "cache1234"},
        tgt_type="glob",
        timeout=60,
    )
    clear = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["clear_dcache"],
        kwarg={"cache_keys": ["cache1234", "cache4321"]},
        tgt_type="glob",
        timeout=60,
    )
    inventory = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory"],
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(clear) 
    assert clear["nrp1"]["cache1234"] == True
    assert clear["nrp1"]["cache4321"] == False
    assert "cache1234" not in inventory["nrp1"]["defaults"]["data"]
    assert "cache1234" not in inventory["nrp1"]["defaults"]["data"]
    
# test_host_results_dcache_clear_by_key()


def test_host_results_list_hcache():
    res = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock", "show hostname"],
        kwarg={"hcache": True, "to_dict": False, "add_details": True},
        tgt_type="glob",
        timeout=60,
    )
    inventory = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory"],
        tgt_type="glob",
        timeout=60,
    )
    clear = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["clear_hcache"],
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(inventory) 
    assert "hcache" in inventory["nrp1"]["hosts"]["ceos1"]["data"]
    assert "hcache" in inventory["nrp1"]["hosts"]["ceos2"]["data"]
    assert isinstance(inventory["nrp1"]["hosts"]["ceos1"]["data"]["hcache"], dict)
    assert isinstance(inventory["nrp1"]["hosts"]["ceos2"]["data"]["hcache"], dict)
    assert "show clock" in inventory["nrp1"]["hosts"]["ceos1"]["data"]["hcache"]
    assert "show clock" in inventory["nrp1"]["hosts"]["ceos2"]["data"]["hcache"]
    assert "show hostname" in inventory["nrp1"]["hosts"]["ceos1"]["data"]["hcache"]
    assert "show hostname" in inventory["nrp1"]["hosts"]["ceos2"]["data"]["hcache"]
    assert "ceos1" in inventory["nrp1"]["hosts"]["ceos1"]["data"]["hcache"]["show hostname"]
    assert "ceos2" in inventory["nrp1"]["hosts"]["ceos2"]["data"]["hcache"]["show hostname"]
    
# test_host_results_list_hcache()


def test_host_results_str_hcache():
    res = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock", "show hostname"],
        kwarg={"hcache": True, "table": "brief"},
        tgt_type="glob",
        timeout=60,
    )
    inventory = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory"],
        tgt_type="glob",
        timeout=60,
    )
    clear = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["clear_hcache"],
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(inventory) 
    assert "hcache" in inventory["nrp1"]["hosts"]["ceos1"]["data"]
    assert "hcache" in inventory["nrp1"]["hosts"]["ceos2"]["data"]
    assert isinstance(inventory["nrp1"]["hosts"]["ceos1"]["data"]["hcache"], str)
    assert isinstance(inventory["nrp1"]["hosts"]["ceos2"]["data"]["hcache"], str)
    assert inventory["nrp1"]["hosts"]["ceos1"]["data"]["hcache"].count("show clock") == 2 
    assert inventory["nrp1"]["hosts"]["ceos2"]["data"]["hcache"].count("show clock") == 2 
    assert inventory["nrp1"]["hosts"]["ceos1"]["data"]["hcache"].count("show hostname") == 2 
    assert inventory["nrp1"]["hosts"]["ceos2"]["data"]["hcache"].count("show hostname") == 2 
    assert inventory["nrp1"]["hosts"]["ceos1"]["data"]["hcache"] == inventory["nrp1"]["hosts"]["ceos2"]["data"]["hcache"]

# test_host_results_str_hcache()


def test_host_results_list_dcache():
    res = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock", "show hostname"],
        kwarg={"dcache": True, "to_dict": False, "add_details": True},
        tgt_type="glob",
        timeout=60,
    )
    inventory = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory"],
        tgt_type="glob",
        timeout=60,
    )
    clear = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["clear_hcache"],
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(inventory) 
    assert "dcache" in inventory["nrp1"]["defaults"]["data"]
    assert isinstance(inventory["nrp1"]["defaults"]["data"]["dcache"], list)
    assert len(inventory["nrp1"]["defaults"]["data"]["dcache"]) == 4
    
# test_host_results_list_dcache()


def test_nornir_refresh():
    # save some data in hcache and verify it cached
    res = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock", "show hostname"],
        kwarg={"hcache": True},
        tgt_type="glob",
        timeout=60,
    )
    inventory = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory"],
        tgt_type="glob",
        timeout=60,
    )    
    assert "hcache" in inventory["nrp1"]["hosts"]["ceos1"]["data"], "No data cached"
    assert "hcache" in inventory["nrp1"]["hosts"]["ceos2"]["data"], "No data cached"
    # refresh nornir
    res = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["refresh"],
        tgt_type="glob",
        timeout=60,
    )    
    # sleep for 30 seconds to make sure nornir refreshed
    time.sleep(30)
    # verify cache is gone
    inventory = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory"],
        tgt_type="glob",
        timeout=60,
    )    
    assert "hcache" not in inventory["nrp1"]["hosts"]["ceos1"]["data"], "Cached data not gone after refresh"
    assert "hcache" not in inventory["nrp1"]["hosts"]["ceos2"]["data"], "Cached data not gone after refresh"
    
    # verify nornir is functional
    res_check = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock", "show hostname"],
        tgt_type="glob",
        timeout=60,
    )
    assert "show clock" in res_check["nrp1"]["ceos1"], "Nornir not working after refresh"
    assert "show clock" in res_check["nrp1"]["ceos2"], "Nornir not working after refresh"
    
# test_nornir_refresh()

def test_nr_grains_hosts():
    ret = client.cmd(
        tgt="nrp1",
        fun="grains.item",
        arg=["hosts"],
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    assert "ceos1" in ret["nrp1"]["hosts"]
    assert "ceos2" in ret["nrp1"]["hosts"]
    
# test_nr_grains_hosts()


def test_nr_cli_event_progress():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"event_progress": True, "FB": "ceos1"},
        tgt_type="glob",
        timeout=60,
    )
    events = []
    timeout = 60
    start_time = time.time()
    for e in event.iter_events(
            tag="nornir\-proxy/.*p",
            match_type="regex"
        ):
        if e["data"]["task_type"] == "task" and e["data"]["task_event"] == "completed":
            events.append(e)
            break
        elif time.time() - start_time > timeout:
            break
        events.append(e)
    # pprint.pprint(events)
    assert len(events) == 6, "Got not 6 events, but ()".format(len(events))
    assert any(
        [
            e["data"]["task_type"] == "task" and e["data"]["task_event"] == "started"
            for e in events
        ]
    ), "Have not found task started event"
    assert any(
        [
            e["data"]["task_type"] == "task" and e["data"]["task_event"] == "completed"
            for e in events
        ]
    ), "Have not found task completed event"
    assert any(
        [
            e["data"]["task_type"] == "task_instance" and e["data"]["task_event"] == "started"
            for e in events
        ]
    ), "Have not found task instance started event"
    assert any(
        [
            e["data"]["task_type"] == "task_instance" and e["data"]["task_event"] == "completed"
            for e in events
        ]
    ), "Have not found task instance completed event"
    assert any(
        [
            e["data"]["task_type"] == "subtask" and e["data"]["task_event"] == "started"
            for e in events
        ]
    ), "Have not found subtask started event"
    assert any(
        [
            e["data"]["task_type"] == "subtask" and e["data"]["task_event"] == "completed"
            for e in events
        ]
    ), "Have not found subtask started completed"
    
# test_nr_cli_event_progress()