import logging
import pprint
import json
import time
import yaml
import pytest
import threading

from utils import fixture_modify_proxy_pillar


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


@pytest.fixture
def remove_hosts_at_the_end(request):
    def delete_hosts():
        # remove hosts
        remove_ceos1_1 = client.cmd(
            tgt="nrp1",
            fun="nr.nornir",
            arg=["inventory", "delete_host"],
            kwarg={"name": "ceos1-1"},
            tgt_type="glob",
            timeout=60,
        )      
        remove_ceos2_1 = client.cmd(
            tgt="nrp1",
            fun="nr.nornir",
            arg=["inventory", "delete_host"],
            kwarg={"name": "ceos2-1"},
            tgt_type="glob",
            timeout=60,
        )    
        print("Deleted ceos1-1 and ceos2-1 hosts.")
        pprint.pprint(remove_ceos1_1)
        pprint.pprint(remove_ceos2_1)
    
        # get lis tof hosts managed by proxy minion
        proxy_hosts_at_the_end = client.cmd(
            tgt="nrp1",
            fun="nr.nornir",
            arg=["hosts"],
            kwarg={},
            tgt_type="glob",
            timeout=60,
        )      
        print("proxy minion hosts at the end:")
        pprint.pprint(proxy_hosts_at_the_end)
        
    request.addfinalizer(delete_hosts)
    
def add_hosts_via_jumphost(jump_ip):
    # add hosts using docker vm as a jumphost
    print("Add ceos1-1 and ceos2-1 hosts using docker vm as a jumphost")
    ret_add_ceos1_1 = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory", "create_host"],
        kwarg={
            "name": "ceos1-1",
            "hostname": "10.0.1.4",
            "platform": "arista_eos",
            "groups": ["lab", "eos_params"],
            "data": {
                "jumphost": {
                    "hostname": jump_ip, 
                    "username": "nornir", 
                    "password": "nornir",
                }
            }        
        },
        tgt_type="glob",
        timeout=60,
    )     
    ret_add_ceos2_1 = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory", "create_host"],
        kwarg={
            "name": "ceos2-1",
            "hostname": "10.0.1.5",
            "platform": "arista_eos",
            "groups": ["lab", "eos_params"],
            "data": {
                "jumphost": {
                    "hostname": jump_ip, 
                    "username": "nornir", 
                    "password": "nornir",
                }
            }        
        },
        tgt_type="glob",
        timeout=60,
    )    
    print("Added host ceos1-1:")
    pprint.pprint(ret_add_ceos1_1)
    print("Added host ceos2-1:")
    pprint.pprint(ret_add_ceos2_1)

def refresh_nrp1_pillar():   
    client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["refresh"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )     
    time.sleep(10) # give proxy minion some time to refresh
    client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["refresh"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )     
    time.sleep(10) # give proxy minion some time to refresh
    
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
    for worker_name, res_data in clear["nrp1"].items():
        assert res_data["ceos1"]["nornir_salt.plugins.tasks.salt_clear_hcache"]["hcache"] == True
        assert res_data["ceos2"]["nornir_salt.plugins.tasks.salt_clear_hcache"]["hcache"] == True
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
    for worker_name, res_data in clear["nrp1"].items():
        assert res_data["ceos1"]["nornir_salt.plugins.tasks.salt_clear_hcache"]["cache1234"] == True
        assert res_data["ceos2"]["nornir_salt.plugins.tasks.salt_clear_hcache"]["cache1234"] == True
        assert res_data["ceos1"]["nornir_salt.plugins.tasks.salt_clear_hcache"]["cache4321"] == False
        assert res_data["ceos2"]["nornir_salt.plugins.tasks.salt_clear_hcache"]["cache4321"] == False
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
    pprint.pprint(clear) 
    for worker_name, res_data in clear["nrp1"].items():
        assert res_data['dcache'] == True
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
    for worker_name, res_data in clear["nrp1"].items():
        assert res_data["cache1234"] == True
        assert res_data["cache4321"] == False
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
    # refresh grains
    ret = client.cmd(
        tgt="nrp1",
        fun="saltutil.refresh_grains",
        tgt_type="glob",
        timeout=60,
    )
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
    pprint.pprint(events)
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
    assert all(
        [
            field in e["data"]
            for e in events
            for field in [
                "timestamp",
                "task_name",
                "jid",
                "proxy_id",
                "task_event",
                "task_type",
                "status",
                "function",
                "worker_id",
            ]
        ]
    ), "Not all expected fields present in event data"
    
# test_nr_cli_event_progress()

def test_tf_skip_failed():
    # remove files first
    client.cmd(
        tgt="nrp1",
        fun="nr.file",
        arg=["rm"],
        kwarg={"filegroup": "test_tf_skip_failed"},
        tgt_type="glob",
        timeout=60,
    )     
    no_skip = client.cmd(
        tgt="nrp1",
        fun="nr.task",
        arg=[],
        kwarg={
            "plugin": "nornir_salt.plugins.tasks.nr_test", 
            "excpt": True, 
            "tf": "test_tf_skip_failed", 
            "tf_skip_failed": False, 
            "excpt_msg": "Testing tf_skip_failed"
        },
        tgt_type="glob",
        timeout=60,
    )
    with_skip = client.cmd(
        tgt="nrp1",
        fun="nr.task",
        arg=[],
        kwarg={
            "plugin": "nornir_salt.plugins.tasks.nr_test", 
            "excpt": True, 
            "tf": "test_tf_skip_failed", 
            "tf_skip_failed": True,
            "excpt_msg": "Testing tf_skip_failed"
        },
        tgt_type="glob",
        timeout=60,
    )    
    file_ls = client.cmd(
        tgt="nrp1",
        fun="nr.file",
        arg=["ls"],
        kwarg={"filegroup": "test_tf_skip_failed"},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(file_ls)
    assert file_ls["nrp1"].count("/test_tf_skip_failed__") == 8, "Unexpected number of test_tf_skip_failed filegroup files, should be 8"
    
# test_tf_skip_failed()

  
def test_worker_target_all():
    workers_stats_before = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["worker", "stats"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )      
    for i in range(3):
        client.cmd(
            tgt="nrp1",
            fun="nr.cli",
            arg=["show clock"],
            kwarg={"worker": "all"},
            tgt_type="glob",
            timeout=60,
        )    
    workers_stats_after = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["worker", "stats"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )     
    pprint.pprint(workers_stats_before)
    pprint.pprint(workers_stats_after)
    for wkr_name, wkr in workers_stats_after["nrp1"].items():
        assert wkr["worker_jobs_started"] - workers_stats_before["nrp1"][wkr_name]["worker_jobs_started"] == 3
        assert wkr["worker_jobs_completed"] - workers_stats_before["nrp1"][wkr_name]["worker_jobs_completed"] == 3
        
# test_worker_target_all()


def test_worker_target_worker_2():
    workers_stats_before = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["worker", "stats"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )      
    for i in range(3):
        client.cmd(
            tgt="nrp1",
            fun="nr.cli",
            arg=["show clock"],
            kwarg={"worker": 2},
            tgt_type="glob",
            timeout=60,
        )    
    workers_stats_after = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["worker", "stats"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )     
    pprint.pprint(workers_stats_before)
    pprint.pprint(workers_stats_after)
    for wkr_name, wkr in workers_stats_after["nrp1"].items():
        if wkr_name in ["nornir-worker-1", "nornir-worker-3"]:
            assert wkr["worker_jobs_started"] - workers_stats_before["nrp1"][wkr_name]["worker_jobs_started"] == 0
            assert wkr["worker_jobs_completed"] - workers_stats_before["nrp1"][wkr_name]["worker_jobs_completed"] == 0            
        else:
            assert wkr_name == "nornir-worker-2"
            assert wkr["worker_jobs_started"] - workers_stats_before["nrp1"][wkr_name]["worker_jobs_started"] == 3
            assert wkr["worker_jobs_completed"] - workers_stats_before["nrp1"][wkr_name]["worker_jobs_completed"] == 3
        
# test_worker_target_worker_2()

def test_worker_target_default_ordered_execution():
    workers_stats_before = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["worker", "stats"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )      
    for i in range(3):
        client.cmd(
            tgt="nrp1",
            fun="nr.cli",
            arg=["show clock"],
            kwarg={},
            tgt_type="glob",
            timeout=60,
        )    
    workers_stats_after = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["worker", "stats"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )     
    pprint.pprint(workers_stats_before)
    pprint.pprint(workers_stats_after)
    for wkr_name, wkr in workers_stats_after["nrp1"].items():
        if wkr_name in ["nornir-worker-2", "nornir-worker-3"]:
            assert wkr["worker_jobs_started"] - workers_stats_before["nrp1"][wkr_name]["worker_jobs_started"] == 0
            assert wkr["worker_jobs_completed"] - workers_stats_before["nrp1"][wkr_name]["worker_jobs_completed"] == 0            
        else:
            assert wkr_name == "nornir-worker-1"
            assert wkr["worker_jobs_started"] - workers_stats_before["nrp1"][wkr_name]["worker_jobs_started"] == 3
            assert wkr["worker_jobs_completed"] - workers_stats_before["nrp1"][wkr_name]["worker_jobs_completed"] == 3
    
# test_worker_target_default_ordered_execution()
   
# @pytest.mark.skip(reason="Disabling to check if it will make salt not to stuck")
@pytest.mark.modify_pillar_target("nrp1")
@pytest.mark.modify_pillar_pre_add({"connections_idle_timeout": 30})
@pytest.mark.modify_pillar_post_remove(["connections_idle_timeout"])
def test_connections_idle_timeout(fixture_modify_proxy_pillar):
    # run task on all workers
    client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"worker": "all"},
        tgt_type="glob",
        timeout=60,
    )   
    connections_before = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["connections"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )   
    print("Finished running task on all workers, sleeping 120 seconds for idle timeout to expire...")
    time.sleep(120) # sleep and wait for watchdog to close connections
    connections_after = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["connections"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )  
    print("connections before:")
    pprint.pprint(connections_before)
    print("connections 120s after:")
    pprint.pprint(connections_after)
    
    # verify connections closed
    for worker_name, connections_data in connections_after["nrp1"].items():
        for host_name, host_data in connections_data.items():
            assert host_data["connections"] == [], "All {} host's connections should be closed".format(host_name)
        
# test_connections_idle_timeout()

    
# @pytest.mark.skip(reason="Disabling to check if it will make salt not to stuck")
def test_connections_via_jumphost(remove_hosts_at_the_end):
    """
    Update pillar to add ceos1-1 and ceos2-1 hosts but using
    docker parent VM as a jumphost, verify can get output from host,
    close connection calling nr.nornir disconnect and verfy can 
    get output using another command, remove ceos1-1 host afterwards,
    for removing host probably need to use pytest fixtures to make sure 
    host removed even if test fails.
    
    run this test printing all the print statements:
    
        pytest -vv test_misc.py::test_connections_via_jumphost -s
    """
    add_hosts_via_jumphost(jump_ip="10.0.1.1")
    # run command to establish connection via jumphost
    cli_cmd_1st = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"FB": "ceos*-1"},
        tgt_type="glob",
        timeout=60,
    )
    print("Added ceos1-1 and ceos2-1, run command via jumphost, output:")
    pprint.pprint(cli_cmd_1st)
    
    # list active connections
    active_connections_before = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["connections"],
        kwarg={"FB": "ceos*-1"},
        tgt_type="glob",
        timeout=60,
    )    
    print("Active connections:")
    pprint.pprint(active_connections_before)
    
    # disconnect connection for new hosts
    disconnect_connections = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["disconnect"],
        kwarg={"FB": "ceos*-1"},
        tgt_type="glob",
        timeout=60,
    )  
    print("Disconnected connections for devices:")
    pprint.pprint(disconnect_connections)

    # list active connections after disconnection
    active_connections_after_disconn = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["connections"],
        kwarg={"FB": "ceos*-1"},
        tgt_type="glob",
        timeout=60,
    )    
    print("Active connections after disconnection:")
    pprint.pprint(active_connections_after_disconn)
    
    # run cli command to reconnect via jumphost
    cli_cmd_after_disconnect = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"FB": "ceos*-1"},
        tgt_type="glob",
        timeout=60,
    )
    print("Added ceos1-1 and ceos2-1, run command via jumphost after reconnecting, output:")
    pprint.pprint(cli_cmd_after_disconnect)    

    # list active connections after
    active_connections_after_recon = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["connections"],
        kwarg={"FB": "ceos*-1"},
        tgt_type="glob",
        timeout=60,
    )    
    print("Active connections after reconnecting:")
    pprint.pprint(active_connections_after_recon)
    
    # do checks for first command run
    assert "Clock source" in cli_cmd_1st["nrp1"]["ceos1-1"]["show clock"]
    assert "Clock source" in cli_cmd_1st["nrp1"]["ceos2-1"]["show clock"]
    # verify active connections after first command run
    for host_name, conn_data in active_connections_before["nrp1"]["nornir-worker-1"].items():
        assert len(conn_data["connections"]) > 0, "Has no active connections via nornir-worker-1"
        for item in conn_data["connections"]:
            assert "netmiko" in item["connection_name"] or "jumphost" in item["connection_name"], "Unexpected connection name"
    # verify disconnect call
    for host_name, conn_data in disconnect_connections["nrp1"]["nornir-worker-1"].items():
        assert len(conn_data["connections"]) > 0, "No disconnected connections via nornir-worker-1"
        for item in conn_data["connections"]:
            assert item["status"] == "closed", "Unexpected connection close status, host: {}, connection: {}".format(host_name, item)
    # verify active connections after disconnect
    for host_name, conn_data in active_connections_after_disconn["nrp1"]["nornir-worker-1"].items():
        assert len(conn_data["connections"]) == 0, "Has active connections via nornir-worker-1"    
    # verify command run after disconnection
    assert "Clock source" in cli_cmd_after_disconnect["nrp1"]["ceos1-1"]["show clock"]
    assert "Clock source" in cli_cmd_after_disconnect["nrp1"]["ceos2-1"]["show clock"]
    # verify active connections after last command run
    for host_name, conn_data in active_connections_after_recon["nrp1"]["nornir-worker-1"].items():
        assert len(conn_data["connections"]) > 0, "Has no active connections via nornir-worker-1 after reconnecting"
        for item in conn_data["connections"]:
            assert "netmiko" in item["connection_name"] or "jumphost" in item["connection_name"], "Unexpected connection name"   
            
# test_connections_via_jumphost()


# @pytest.mark.skip(reason="Disabling to check if it will make salt not to stuck")
def test_connections_via_nonexisting_jumphost(remove_hosts_at_the_end):
    """
    Verify RetryRunner bahavior when jumphost is unreachable
    
    run this test printing all the print statements:
    
        pytest -vv test_misc.py::test_connections_via_nonexisting_jumphost -s
    """
    add_hosts_via_jumphost(jump_ip="10.1.2.3")
    # run command to establish connection via jumphost
    cli_cmd_1st = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"FB": "ceos*-1", "add_details": True},
        tgt_type="glob",
        timeout=60,
    )
    print("Added ceos1-1 and ceos2-1, run command via nonexisting jumphost for 1st time, output:")
    pprint.pprint(cli_cmd_1st)

    assert cli_cmd_1st["nrp1"]["ceos1-1"]["nornir_salt.plugins.tasks.netmiko_send_commands"]["failed"] == True
    assert cli_cmd_1st["nrp1"]["ceos2-1"]["nornir_salt.plugins.tasks.netmiko_send_commands"]["failed"] == True
    assert "failed connection to jumphost" in cli_cmd_1st["nrp1"]["ceos1-1"]["nornir_salt.plugins.tasks.netmiko_send_commands"]["exception"]
    assert "failed connection to jumphost" in cli_cmd_1st["nrp1"]["ceos2-1"]["nornir_salt.plugins.tasks.netmiko_send_commands"]["exception"]
    
# test_connections_via_nonexisting_jumphost()
    

# @pytest.mark.skip(reason="Disabling to check if it will make salt not to stuck")
@pytest.mark.modify_pillar_target("nrp1")
@pytest.mark.modify_pillar_pre_add({"proxy_always_alive": False})
@pytest.mark.modify_pillar_post_remove(["proxy_always_alive"])
def test_proxy_always_alive_false(fixture_modify_proxy_pillar, remove_hosts_at_the_end):
    """
    To run with printing to screen::
    
        pytest -vv -s test_misc.py::test_proxy_always_alive_false
    """
    # add hosts using docker vm as a jumphost
    add_hosts_via_jumphost(jump_ip="10.0.1.1")  
    # run tasks on all workers and collect connections status
    connections, tasks = [], []
    for i in range(3):
        tasks.append(client.cmd(
            tgt="nrp1",
            fun="nr.cli",
            arg=["show clock"],
            kwarg={"worker": "all"},
            tgt_type="glob",
            timeout=60,
        ))
        connections.append(client.cmd(
            tgt="nrp1",
            fun="nr.nornir",
            arg=["connections"],
            kwarg={},
            tgt_type="glob",
            timeout=60,
        ))
        
    print("Task results:")
    pprint.pprint(tasks)
    print("Connections statuses:")
    pprint.pprint(connections)
        
    # verify task execution
    for t in tasks:
        for wkr in ["nornir-worker-1", "nornir-worker-2", "nornir-worker-3"]:
            assert isinstance(t["nrp1"][wkr]["ceos1"]["show clock"], str), "Unexpected output from ceos1"
            assert isinstance(t["nrp1"][wkr]["ceos2"]["show clock"], str), "Unexpected output from ceos2"
            assert isinstance(t["nrp1"][wkr]["ceos1-1"]["show clock"], str), "Unexpected output from ceos1-1"
            assert isinstance(t["nrp1"][wkr]["ceos2-1"]["show clock"], str), "Unexpected output from ceos2-1"

            assert "traceback" not in t["nrp1"][wkr]["ceos1"]["show clock"].lower(), "Got traceback output from ceos1"
            assert "traceback" not in t["nrp1"][wkr]["ceos2"]["show clock"].lower(), "Got traceback output from ceos2"
            assert "traceback" not in t["nrp1"][wkr]["ceos1-1"]["show clock"].lower(), "Got traceback output from ceos1-1"
            assert "traceback" not in t["nrp1"][wkr]["ceos2-1"]["show clock"].lower(), "Got traceback output from ceos2-1"
            
    # verify connections status
    for t in connections:
        for wkr in ["nornir-worker-1", "nornir-worker-2", "nornir-worker-3"]:
            assert t["nrp1"][wkr]["ceos1"]["connections"] == [], "Unexpected connections status for ceos1"
            assert t["nrp1"][wkr]["ceos2"]["connections"] == [], "Unexpected connections status for ceos2"
            assert t["nrp1"][wkr]["ceos1-1"]["connections"] == [], "Unexpected connections status for ceos1-1"
            assert t["nrp1"][wkr]["ceos2-1"]["connections"] == [], "Unexpected connections status for ceos2-1"

def test_worker_target_tasks_distribution():
    """
    This test submits 5 sleep tasks in async mode to salt, expectation is that
    these tasks will be picket up by all workers in succession, which should lead
    to completed task counter increase in worker stats.
    """
    # get stats before
    stats_before = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["worker", "stats"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )
    # submit jobs
    jobs = []
    for _ in range(6):
        job = client.run_job(
            tgt="nrp1",
            fun="nr.task",
            arg=[],
            kwarg={"plugin": "nornir_salt.plugins.tasks.sleep", "sleep_for": 1},
            tgt_type="glob",
            timeout=60,
        )
        jobs.append(job)
    print("Started jobs:")
    pprint.pprint(jobs)
    
    print("Waiting for jobs to complete.")
    time.sleep(20)
    
    # get stats after
    stats_after = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["worker", "stats"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )
    print("Stats before:")
    pprint.pprint(stats_before)
    print("Stats after:")
    pprint.pprint(stats_after)

    # verify all workers did some job
    assert stats_after["nrp1"]["nornir-worker-1"]["worker_jobs_completed"] > stats_before["nrp1"]["nornir-worker-1"]["worker_jobs_completed"]
    assert stats_after["nrp1"]["nornir-worker-2"]["worker_jobs_completed"] > stats_before["nrp1"]["nornir-worker-2"]["worker_jobs_completed"]
    assert stats_after["nrp1"]["nornir-worker-3"]["worker_jobs_completed"] > stats_before["nrp1"]["nornir-worker-3"]["worker_jobs_completed"]
    
    
def test_per_host_file_downlod_partially_failed():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg_gen",
        arg=[],
        kwarg={
            "filename": "salt://templates/per_host_cfg_snmp_ceos1/{{ host.name }}.txt",
            "add_details": True,
        },
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert ret["nrp1"]["ceos1"]["salt_cfg_gen"]["failed"] == False
    assert ret["nrp1"]["ceos2"]["salt_cfg_gen"]["failed"] == True    
    
    
def test_nr_nornir_stats_tasks():
    stats_before = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["stats"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )
    workers_stats_before = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["workers", "stats"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )
    _ = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )
    stats_after = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["stats"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )
    workers_stats_after = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["workers", "stats"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(stats_before)
    pprint.pprint(workers_stats_before)
    pprint.pprint(stats_after)
    pprint.pprint(workers_stats_after)
    assert stats_after["nrp1"]["tasks_completed"] - stats_before["nrp1"]["tasks_completed"] == 2
    assert stats_after["nrp1"]["tasks_failed"] - stats_before["nrp1"]["tasks_failed"] == 0
    assert (
        workers_stats_after["nrp1"]["nornir-worker-1"]["worker_tasks_completed"] -
        workers_stats_before["nrp1"]["nornir-worker-1"]["worker_tasks_completed"]
    ) == 2
    
    
def test_RetryRunner_with_run_creds_retry():  
    print("\n(1) Adding ceos1-1 hosts with wrong credentials")
    ret_add_ceos1_1 = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory", "create_host"],
        kwarg={
            "name": "ceos1-1",
            "hostname": "10.0.1.4",
            "platform": "arista_eos",
            "username": "wrong",
            "password": "wrong",       
        },
        tgt_type="glob",
        timeout=60,
    )      
    pprint.pprint(ret_add_ceos1_1)
    print("(2) Connecting to ceos1-1 using run_creds_retry and running show clock")
    ret1_cli_ceos1_1 = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={
            "run_creds_retry": [
                "deprecated_creds",
                "local_account",
            ],
            "FB": "ceos1-1"
        },
        tgt_type="glob",
        timeout=60,
    )   
    pprint.pprint(ret1_cli_ceos1_1)
    print("(3) Closing connection to ceos1-1")
    disconnect = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["disconnect"],
        kwarg={
            "FB": "ceos1-1"
        },
        tgt_type="glob",
        timeout=60,
    )  
    pprint.pprint(disconnect)
    print("(4) ceos1-1 running show clock again using bad creds")
    ret2_cli_ceos1_1 = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"FC": "ceos1-1"},
        tgt_type="glob",
        timeout=60,
    )   
    pprint.pprint(ret2_cli_ceos1_1)
    print("(5) Removing ceos1-1 from inventory")
    remove_ceos1_1 = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory", "delete_host"],
        kwarg={"name": "ceos1-1"},
        tgt_type="glob",
        timeout=60,
    )    
    pprint.pprint(remove_ceos1_1)
    print("(6) Running tests")
    # verify device added
    for v in ret_add_ceos1_1["nrp1"].values():
        assert v["ceos1-1"] == True, "Worker did not add ceos1-1 ?"
    # verify command output
    assert isinstance(ret1_cli_ceos1_1["nrp1"]["ceos1-1"]["show clock"], str)
    assert "Traceback" not in ret1_cli_ceos1_1["nrp1"]["ceos1-1"]["show clock"]
    assert "nornir_salt.plugins.tasks.netmiko_send_commands" in ret2_cli_ceos1_1["nrp1"]["ceos1-1"], "Command not failed, while it should fail due to bad username and password"
    assert "error" in ret2_cli_ceos1_1["nrp1"]["ceos1-1"]["nornir_salt.plugins.tasks.netmiko_send_commands"]
    # verify device deleted
    for v in remove_ceos1_1["nrp1"].values():
        assert v["ceos1-1"] == True, "Worker did not removed ceos1-1 ?"
        
        
def test_RetryRunner_with_run_creds_retry_conn_options():
    """
    This test uses connection options to derive per connection
    parameters while retrying them.
    """
    print("Adding ceos1-1 hosts with wrong credentials")
    ret_add_ceos1_1 = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory", "create_host"],
        kwarg={
            "name": "ceos1-1",
            "hostname": "10.0.1.4",
            "platform": "arista_eos",
            "groups": ["lab", "eos_params"],
            "username": "wrong",
            "password": "wrong",
            "data": {
                "credentials": {
                    "local_creds": {
                        # these params are for Netmiko
                        "username": "nornir",
                        "password": "nornir",
                        "platform": "arista_eos",
                        "port": 22,
                        "extras": {
                            "conn_timeout": 10,
                            "auto_connect": True,
                            "session_timeout": 60
                        },
                        "connection_options": {
                            # Napalm specific parameters
                            "napalm": {
                                "username": "nornir",
                                "platform": "eos",
                                "port": 80,
                                "extras": {
                                    "optional_args": {
                                        "transport": "http",
                                        "eos_autoComplete": None
                                    }
                                }
                            },
                            # Scrapli specific parameters
                            "scrapli": {
                                "password": "nornir",
                                "platform": "arista_eos",
                                "port": 22,
                                "extras": {
                                    "auth_strict_key": False,
                                    "ssh_config_file": False
                                }
                            }
                        }
                    },
                    "local_creds_old": {
                        "username": "nornir",
                        "password": "wrong"
                    }
                }
            }
        },
        tgt_type="glob",
        timeout=60,
    )      
    pprint.pprint(ret_add_ceos1_1)
    
    print("Connecting to ceos1-1 using run_creds_retry and running show clock using Netmiko")
    ret1_cli_ceos1_1_netmiko = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={
            "run_creds_retry": ["local_creds", "local_creds_old"],
            "FB": "ceos1-1",
            "plugin": "netmiko"
        },
        tgt_type="glob",
        timeout=60,
    )   
    pprint.pprint(ret1_cli_ceos1_1_netmiko)
    
    print("Connecting to ceos1-1 using run_creds_retry and running show clock using Scrapli")
    ret1_cli_ceos1_1_scrapli = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={
            "run_creds_retry": ["local_creds", "local_creds_old"],
            "FB": "ceos1-1",
            "plugin": "scrapli"
        },
        tgt_type="glob",
        timeout=60,
    )   
    pprint.pprint(ret1_cli_ceos1_1_scrapli)
    
    print("Connecting to ceos1-1 using run_creds_retry and running show clock using Napalm")
    ret1_cli_ceos1_1_napalm = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={
            "run_creds_retry": ["local_creds", "local_creds_old"],
            "FB": "ceos1-1",
            "plugin": "napalm"
        },
        tgt_type="glob",
        timeout=60,
    )   
    pprint.pprint(ret1_cli_ceos1_1_napalm)
    
    print("Removing ceos1-1 from inventory")
    remove_ceos1_1 = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory", "delete_host"],
        kwarg={"name": "ceos1-1"},
        tgt_type="glob",
        timeout=60,
    )    
    pprint.pprint(remove_ceos1_1)
    
    # verify device added
    for v in ret_add_ceos1_1["nrp1"].values():
        assert v["ceos1-1"] == True, "Worker did not add ceos1-1 ?"
    # verify command output
    assert isinstance(ret1_cli_ceos1_1_netmiko["nrp1"]["ceos1-1"]["show clock"], str)
    assert "Traceback" not in ret1_cli_ceos1_1_netmiko["nrp1"]["ceos1-1"]["show clock"]
    assert isinstance(ret1_cli_ceos1_1_scrapli["nrp1"]["ceos1-1"]["show clock"], str)
    assert "Traceback" not in ret1_cli_ceos1_1_scrapli["nrp1"]["ceos1-1"]["show clock"]
    assert isinstance(ret1_cli_ceos1_1_napalm["nrp1"]["ceos1-1"]["show clock"], str)
    assert "Traceback" not in ret1_cli_ceos1_1_napalm["nrp1"]["ceos1-1"]["show clock"]
    # verify device deleted
    for v in remove_ceos1_1["nrp1"].values():
        assert v["ceos1-1"] == True, "Workers did not removed ceos1-1?"
        
        
def test_RetryRunner_with_run_creds_retry_conn_options_only():
    """
    This test uses connection options to derive per connection
    parameters while retrying them.
    """
    print("Adding ceos1-1 hosts with wrong credentials")
    ret_add_ceos1_1 = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory", "create_host"],
        kwarg={
            "name": "ceos1-1",
            "hostname": "10.0.1.4",
            "platform": "arista_eos",
            "groups": ["lab", "eos_params"],
            "username": "wrong",
            "password": "wrong",
            "data": {
                "credentials": {
                    "local_creds": {
                        "username": "nornir",
                        "password": "nornir",
                        "connection_options": {
                            # Napalm specific parameters
                            "napalm": {
                                "platform": "eos",
                                "port": 80,
                                "extras": {
                                    "optional_args": {
                                        "transport": "http",
                                        "eos_autoComplete": None
                                    }
                                }
                            },
                            # Scrapli specific parameters
                            "scrapli": {
                                "platform": "arista_eos",
                                "port": 22,
                                "extras": {
                                    "auth_strict_key": False,
                                    "ssh_config_file": False
                                }
                            },
                             # these params are for Netmiko
                            "netmiko": {
                                "platform": "arista_eos",
                                "port": 22,
                                "extras": {
                                    "conn_timeout": 10,
                                    "auto_connect": True,
                                    "session_timeout": 60
                                }
                            }
                        }
                    },
                    "local_creds_old": {
                        "username": "nornir",
                        "password": "wrong"
                    }
                }
            }
        },
        tgt_type="glob",
        timeout=60,
    )      
    pprint.pprint(ret_add_ceos1_1)
    
    print("Connecting to ceos1-1 using run_creds_retry and running show clock using Netmiko")
    ret1_cli_ceos1_1_netmiko = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={
            "run_creds_retry": ["local_creds", "local_creds_old"],
            "FB": "ceos1-1",
            "plugin": "netmiko"
        },
        tgt_type="glob",
        timeout=60,
    )   
    pprint.pprint(ret1_cli_ceos1_1_netmiko)
    
    print("Connecting to ceos1-1 using run_creds_retry and running show clock using Scrapli")
    ret1_cli_ceos1_1_scrapli = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={
            "run_creds_retry": ["local_creds", "local_creds_old"],
            "FB": "ceos1-1",
            "plugin": "scrapli"
        },
        tgt_type="glob",
        timeout=60,
    )   
    pprint.pprint(ret1_cli_ceos1_1_scrapli)
    
    print("Connecting to ceos1-1 using run_creds_retry and running show clock using Napalm")
    ret1_cli_ceos1_1_napalm = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={
            "run_creds_retry": ["local_creds", "local_creds_old"],
            "FB": "ceos1-1",
            "plugin": "napalm"
        },
        tgt_type="glob",
        timeout=60,
    )   
    pprint.pprint(ret1_cli_ceos1_1_napalm)
    
    print("Removing ceos1-1 from inventory")
    remove_ceos1_1 = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory", "delete_host"],
        kwarg={"name": "ceos1-1"},
        tgt_type="glob",
        timeout=60,
    )    
    pprint.pprint(remove_ceos1_1)
    
    # verify device added
    for v in ret_add_ceos1_1["nrp1"].values():
        assert v["ceos1-1"] == True, "Worker did not add ceos1-1 ?"
    # verify command output
    assert isinstance(ret1_cli_ceos1_1_netmiko["nrp1"]["ceos1-1"]["show clock"], str)
    assert "Traceback" not in ret1_cli_ceos1_1_netmiko["nrp1"]["ceos1-1"]["show clock"]
    assert isinstance(ret1_cli_ceos1_1_scrapli["nrp1"]["ceos1-1"]["show clock"], str)
    assert "Traceback" not in ret1_cli_ceos1_1_scrapli["nrp1"]["ceos1-1"]["show clock"]
    assert isinstance(ret1_cli_ceos1_1_napalm["nrp1"]["ceos1-1"]["show clock"], str)
    assert "Traceback" not in ret1_cli_ceos1_1_napalm["nrp1"]["ceos1-1"]["show clock"]
    # verify device deleted
    for v in remove_ceos1_1["nrp1"].values():
        assert v["ceos1-1"] == True, "Workers did not removed ceos1-1?"
        
        
def test_RetryRunner_with_run_creds_retry_all_failed():
    print("\n(1) Adding ceos1-1 hosts with wrong credentials")
    ret_add_ceos1_1 = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory", "create_host"],
        kwarg={
            "name": "ceos1-1",
            "hostname": "10.0.1.4",
            "platform": "arista_eos",
            "groups": ["lab", "eos_params"],
            "username": "wrong",
            "password": "wrong",       
        },
        tgt_type="glob",
        timeout=60,
    )      
    pprint.pprint(ret_add_ceos1_1)
    print("(2) Connecting to ceos1-1 using run_creds_retry with all credentials wrong")
    ret1_cli_ceos1_1 = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={
            "run_creds_retry": [
                {
                    "username": "wrong_too",
                    "password": "wrong_again",
                },
            ],
            "FB": "ceos1-1"
        },
        tgt_type="glob",
        timeout=60,
    )   
    pprint.pprint(ret1_cli_ceos1_1)
    print("(3) Removing ceos1-1 from inventory")
    remove_ceos1_1 = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory", "delete_host"],
        kwarg={"name": "ceos1-1"},
        tgt_type="glob",
        timeout=60,
    )    
    pprint.pprint(remove_ceos1_1)
    print("(4) Running tests")
    # verify device added
    for v in ret_add_ceos1_1["nrp1"].values():
        assert v["ceos1-1"] == True, "Worker did not add ceos1-1 ?"
    # verify command output
    assert isinstance(ret1_cli_ceos1_1["nrp1"]["ceos1-1"]["nornir_salt.plugins.tasks.netmiko_send_commands"], str)
    assert "Traceback" in ret1_cli_ceos1_1["nrp1"]["ceos1-1"]["nornir_salt.plugins.tasks.netmiko_send_commands"]
    assert "Authentication" in ret1_cli_ceos1_1["nrp1"]["ceos1-1"]["nornir_salt.plugins.tasks.netmiko_send_commands"]
    # verify device deleted
    for v in remove_ceos1_1["nrp1"].values():
        assert v["ceos1-1"] == True, "Worker did not removed ceos1-1 ?"

    
def test_RetryRunner_with_num_connectors():
    disconnect_call = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["disconnect"]
    )
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"run_num_connectors", 1},
        tgt_type="glob",
        timeout=60,
    )    
    pprint.pprint(ret)
    assert "Traceback" not in ret["nrp1"]["ceos1"]["show clock"]
    assert "Traceback" not in ret["nrp1"]["ceos2"]["show clock"]

def test_RetryRunner_with_num_workers():
    """
    Task task_test_num_workers sleeps for 2 seconds and return timestamp,
    using that timestamp we can verify time diference between when we have 
    1 and 2 workers doing th etask
    """
    ret_1_worker = client.cmd(
        tgt="nrp1",
        fun="nr.task",
        arg=[],
        kwarg={
            "plugin": "salt://tasks/task_test_num_workers.py",
            "run_num_workers": 1,
        },
        tgt_type="glob",
        timeout=60,
    )     
    ret_2_workers = client.cmd(
        tgt="nrp1",
        fun="nr.task",
        arg=[],
        kwarg={
            "plugin": "salt://tasks/task_test_num_workers.py",
            "run_num_workers": 2,
        },
        tgt_type="glob",
        timeout=60,
    )     
    print("ret_1_worker: ")
    pprint.pprint(ret_1_worker)
    print("ret_2_workers: ")
    pprint.pprint(ret_2_workers)
    assert (
        abs(
            float(ret_1_worker["nrp1"]["ceos2"]["salt://tasks/task_test_num_workers.py"]) - 
            float(ret_1_worker["nrp1"]["ceos1"]["salt://tasks/task_test_num_workers.py"])
        ) >= 2
    )
    assert (
        abs(
            float(ret_2_workers["nrp1"]["ceos2"]["salt://tasks/task_test_num_workers.py"]) - 
            float(ret_2_workers["nrp1"]["ceos1"]["salt://tasks/task_test_num_workers.py"])
        ) <= 1
    )
    
def test_RetryRunner_with_run_task_retry():
    ret_task_retry_0 = client.cmd(
        tgt="nrp1",
        fun="nr.task",
        arg=[],
        kwarg={
            "plugin": "nornir_salt.plugins.tasks.nr_test", 
            "excpt": True, 
            "run_task_retry": 0,
            "add_details": True,
        },
        tgt_type="glob",
        timeout=60,
    )
    ret_task_retry_1 = client.cmd(
        tgt="nrp1",
        fun="nr.task",
        arg=[],
        kwarg={
            "plugin": "nornir_salt.plugins.tasks.nr_test", 
            "excpt": True, 
            "run_task_retry": 1,
            "add_details": True,
        },
        tgt_type="glob",
        timeout=60,
    )
    ret_task_retry_5 = client.cmd(
        tgt="nrp1",
        fun="nr.task",
        arg=[],
        kwarg={
            "plugin": "nornir_salt.plugins.tasks.nr_test", 
            "excpt": True, 
            "run_task_retry": 5,
            "run_connect_retry": 5,
            "add_details": True,
        },
        tgt_type="glob",
        timeout=60,
    )
    print("ret_task_retry_0: ")
    pprint.pprint(ret_task_retry_0)
    print("ret_task_retry_1: ")
    pprint.pprint(ret_task_retry_1)
    print("ret_task_retry_5: ")
    pprint.pprint(ret_task_retry_5)
    assert ret_task_retry_0["nrp1"]["ceos1"]["nornir_salt.plugins.tasks.nr_test"]["task_retry"] == 0
    assert ret_task_retry_1["nrp1"]["ceos1"]["nornir_salt.plugins.tasks.nr_test"]["task_retry"] == 1
    assert ret_task_retry_5["nrp1"]["ceos1"]["nornir_salt.plugins.tasks.nr_test"]["task_retry"] == 5

    
def test_RetryRunner_with_run_connect_retry():
    print("Adding ceos1-1 hosts with wrong credentials")
    ret_add_ceos1_1 = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory", "create_host"],
        kwarg={
            "name": "ceos1-1",
            "hostname": "10.0.1.4",
            "platform": "arista_eos",
            "groups": ["lab", "eos_params"],
            "username": "wrong",
            "password": "wrong",       
        },
        tgt_type="glob",
        timeout=60,
    )    
    pprint.pprint(ret_add_ceos1_1)
    ret_connect_retry_0 = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={
            "run_connect_retry": 0,
            "add_details": True,
            "FB": "ceos1-1"
        },
        tgt_type="glob",
        timeout=60,
    )
    ret_connect_retry_1 = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={
            "run_connect_retry": 1,
            "add_details": True,
            "FB": "ceos1-1"
        },
        tgt_type="glob",
        timeout=60,
    )
    ret_connect_retry_5 = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={
            "run_connect_retry": 5,
            "add_details": True,
            "FB": "ceos1-1"
        },
        tgt_type="glob",
        timeout=60,
    )    
    print("Removing ceos1-1 from inventory")
    remove_ceos1_1 = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory", "delete_host"],
        kwarg={"name": "ceos1-1"},
        tgt_type="glob",
        timeout=60,
    )   
    pprint.pprint(remove_ceos1_1)
    print("ret_connect_retry_0: ")
    pprint.pprint(ret_connect_retry_0)
    print("ret_connect_retry_1: ")
    pprint.pprint(ret_connect_retry_1)
    print("ret_connect_retry_5: ")
    pprint.pprint(ret_connect_retry_5)
    # verify device added
    for v in ret_add_ceos1_1["nrp1"].values():
        assert v["ceos1-1"] == True, "Worker did not add ceos1-1 ?"
    # verify connection retry attempts
    assert ret_connect_retry_0["nrp1"]["ceos1-1"]["nornir_salt.plugins.tasks.netmiko_send_commands"]["connection_retry"] == 0
    assert ret_connect_retry_1["nrp1"]["ceos1-1"]["nornir_salt.plugins.tasks.netmiko_send_commands"]["connection_retry"] == 1
    assert ret_connect_retry_5["nrp1"]["ceos1-1"]["nornir_salt.plugins.tasks.netmiko_send_commands"]["connection_retry"] == 5
    # verify device deleted
    for v in remove_ceos1_1["nrp1"].values():
        assert v["ceos1-1"] == True, "Worker did not removed ceos1-1 ?"


def test_RetryRunner_2_different_subtask_connection_plugins():
    """
    Test to test RetryRunner connection_name handling for subtasks
    that uses different connection plugins
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.task",
        arg=[],
        kwarg={
            "plugin": "salt://tasks/task_subtasks_with_different_connections.py", 
            "add_details": True,
        },
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert ret["nrp1"]["ceos1"]["netmiko_send_command"]["failed"] == False
    assert ret["nrp1"]["ceos1"]["scrapli_send_command"]["failed"] == False
    assert ret["nrp1"]["ceos2"]["netmiko_send_command"]["failed"] == False
    assert ret["nrp1"]["ceos2"]["scrapli_send_command"]["failed"] == False
    assert "Clock source" in ret["nrp1"]["ceos1"]["scrapli_send_command"]["result"]
    assert "Clock source" in ret["nrp1"]["ceos2"]["scrapli_send_command"]["result"]
    assert "Clock source" in ret["nrp1"]["ceos1"]["netmiko_send_command"]["result"]
    assert "Clock source" in ret["nrp1"]["ceos2"]["netmiko_send_command"]["result"]


def test_RetryRunner_with_run_creds_retry_via_jumphost():
    print("\n(1) Adding ceos1-1 with wrong username/password, via jumphost")
    ret_add_ceos1_1 = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory", "create_host"],
        kwarg={
            "name": "ceos1-1",
            "hostname": "10.0.1.4",
            "platform": "arista_eos",
            "username": "wrong",
            "password": "wrong",
            "groups": ["lab", "eos_params"],
            "data": {
                "jumphost": {
                    "hostname": "10.0.1.1", 
                    "username": "nornir", 
                    "password": "nornir",
                }
            }        
        },
        tgt_type="glob",
        timeout=60,
    )     
    pprint.pprint(ret_add_ceos1_1)
    print("(2) Running cli task to verify connection fails")
    ret_fail = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"FB": "ceos1-1"},
        tgt_type="glob",
        timeout=60,
    )  
    pprint.pprint(ret_fail)
    print("(3)  Running cli task with run_retry_creds")
    ret_pass = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={
            "run_creds_retry": ["local_account"],
            "FB": "ceos1-1"
        },
        tgt_type="glob",
        timeout=60,
    )   
    pprint.pprint(ret_pass)
    print("(4)  Removing ceos1-1 from inventory")
    remove_ceos1_1 = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory", "delete_host"],
        kwarg={"name": "ceos1-1"},
        tgt_type="glob",
        timeout=60,
    )   
    pprint.pprint(remove_ceos1_1) 
    # verify device added
    for v in ret_add_ceos1_1["nrp1"].values():
        assert v["ceos1-1"] == True, "Worker did not add ceos1-1 ?"
    # verify command output
    assert "Authentication to device failed." in ret_fail["nrp1"]["ceos1-1"]["nornir_salt.plugins.tasks.netmiko_send_commands"]
    assert "Clock source" in ret_pass["nrp1"]["ceos1-1"]["show clock"]
    # verify device deleted
    for v in remove_ceos1_1["nrp1"].values():
        assert v["ceos1-1"] == True, "Worker did not removed ceos1-1 ?"
        
def test_RetryRunner_with_connectors_and_workers_0():
    ret_fail_1 = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"FB": "ceos1", "run_num_connectors": 0},
        tgt_type="glob",
        timeout=60,
    )  
    ret_fail_2 = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"FB": "ceos1", "run_num_workers": 0},
        tgt_type="glob",
        timeout=60,
    )  
    pprint.pprint(ret_fail_1)
    pprint.pprint(ret_fail_2)
    assert "RuntimeError" in ret_fail_1["nrp1"]
    assert "RuntimeError" in ret_fail_2["nrp1"]
    
    
def test_RetryRunner_3_different_subtask_connection_plugins():
    """
    Test to test RetryRunner connection_name handling for subtasks
    that uses different connection plugins, CONNECTION_NAME is a 
    comma separated string of connections to establish.
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.task",
        arg=[],
        kwarg={
            "plugin": "salt://tasks/retryrunner_conn_test.py", 
            "add_details": True,
        },
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret) 
    assert ret["nrp1"]["ceos1"]["Pull Configuration Using Scrapli Netconf"]["failed"] == False
    assert ret["nrp1"]["ceos1"]["Pull Configuration using Netmiko"]["failed"] == False
    assert ret["nrp1"]["ceos1"]["Pull Configuration using Scrapli"]["failed"] == False
    
    assert ret["nrp1"]["ceos2"]["Pull Configuration Using Scrapli Netconf"]["failed"] == False
    assert ret["nrp1"]["ceos2"]["Pull Configuration using Netmiko"]["failed"] == False
    assert ret["nrp1"]["ceos2"]["Pull Configuration using Scrapli"]["failed"] == False
    
    assert "Traceback" not in ret["nrp1"]["ceos1"]["Pull Configuration Using Scrapli Netconf"]["result"]
    assert "Traceback" not in ret["nrp1"]["ceos1"]["Pull Configuration using Netmiko"]["result"] 
    assert "Traceback" not in ret["nrp1"]["ceos1"]["Pull Configuration using Scrapli"]["result"] 
    
    assert "Traceback" not in ret["nrp1"]["ceos2"]["Pull Configuration Using Scrapli Netconf"]["result"]
    assert "Traceback" not in ret["nrp1"]["ceos2"]["Pull Configuration using Netmiko"]["result"] 
    assert "Traceback" not in ret["nrp1"]["ceos2"]["Pull Configuration using Scrapli"]["result"] 
    
     
    
def test_simeltenious_download():
    """
    Test to test Norninr workers simelteniously running task that require 
    download file from master. That is to test fix for GitHub issue #9.
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg_gen",
        arg=[],
        kwarg={"filename": "salt://templates/ntp_config.txt", "worker": "all"},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    for wkr_id, res in ret["nrp1"].items():
        for hostname, hostres in res.items():
            assert "Traceback" not in hostres["salt_cfg_gen"], "wkr {}, host {} returned traceback".format(wkr_id, hostname)
            

def test_nornir_refresh_workers_only():
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
        kwarg={"workers_only": True},
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
    
    
def test_ffun_FT_function_by_string():
    res = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["hosts"],
        kwarg={"FT": "core"},
        tgt_type="glob",
        timeout=60,
    )   
    assert "ceos1" in res["nrp1"]
    assert len(res["nrp1"]) == 1
    
    
def test_ffun_FT_function_by_list():
    res = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["hosts"],
        kwarg={"FT": ["core", "access"]},
        tgt_type="glob",
        timeout=60,
    )   
    assert "ceos1" in res["nrp1"] and "ceos2" in res["nrp1"]
    assert len(res["nrp1"]) == 2
    
    
def test_ffun_FT_function_no_match():
    res = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["hosts"],
        kwarg={"FT": ["EDGE"]},
        tgt_type="glob",
        timeout=60,
    )   
    assert len(res["nrp1"]) == 0
    
    
def test_ffun_FT_function_comma_string():
    res = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["hosts"],
        kwarg={"FT": "core, access"},
        tgt_type="glob",
        timeout=60,
    )   
    assert "ceos1" in res["nrp1"] and "ceos2" in res["nrp1"]
    assert len(res["nrp1"]) == 2    
    
    
def test_big_result():
    """
    Task return over 1 000 000 characters in result data, SALT
    should trim it.
    """
    res = client.cmd(
        tgt="nrp1",
        fun="nr.task",
        arg=[],
        kwarg={"FB": "ceos1", "plugin": "salt://tasks/big_result.py"},
        tgt_type="glob",
        timeout=60,
    )   
    assert "VALUE_TRIMMED" in res["nrp1"]["ceos1"]["job_data_echo"] 