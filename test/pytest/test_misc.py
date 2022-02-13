import logging
import pprint
import json
import time
import yaml
import pytest

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


@pytest.fixture
def restore_pillar_connections_idle_timeout(request):
    def restore():
        # restore pillar settings
        with open("/etc/salt/pillar/nrp1.sls", "r") as f:
            pillar_data = yaml.safe_load(f.read())
        pillar_data["proxy"].pop("connections_idle_timeout", None)
        with open("/etc/salt/pillar/nrp1.sls", "w") as f:
            yaml.dump(pillar_data, f, default_flow_style=False)
        refresh_nrp1_pillar()
        # verify pillar data loaded
        proxy_pillar = client.cmd(
            tgt="nrp1",
            fun="pillar.raw",
            arg=[],
            kwarg={"key": "proxy"},
            tgt_type="glob",
            timeout=60,
        )   
        print("Restored nrp1 proxy pillar:")
        pprint.pprint(proxy_pillar)
        
    request.addfinalizer(restore)
    

def test_connections_idle_timeout(restore_pillar_connections_idle_timeout):
    # first update proxy pillar and refresh it
    with open("/etc/salt/pillar/nrp1.sls", "r") as f:
        pillar_data = yaml.safe_load(f.read())
    pillar_data["proxy"]["connections_idle_timeout"] = 30
    with open("/etc/salt/pillar/nrp1.sls", "w") as f:
        yaml.dump(pillar_data, f, default_flow_style=False)
    refresh_nrp1_pillar()
    # verify new pillar data loaded
    proxy_pillar = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["stats"],
        kwarg={"stat": "hosts_connections_idle_timeout"},
        tgt_type="glob",
        timeout=60,
    )   
    print("Refreshed nrp1 proxy params:")
    pprint.pprint(proxy_pillar)
    assert proxy_pillar["nrp1"]["hosts_connections_idle_timeout"] == 30, "Proxy not refreshed?"
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
            assert host_data["nornir_salt.plugins.tasks.connections"] == [], "All {} host's connections should be closed".format(host_name)
        
# test_connections_idle_timeout()

    
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
        assert len(conn_data["nornir_salt.plugins.tasks.connections"]) > 0, "Has no active connections via nornir-worker-1"
        for item in conn_data["nornir_salt.plugins.tasks.connections"]:
            assert "netmiko" in item["connection_name"] or "jumphost" in item["connection_name"], "Unexpected connection name"
    # verify disconnect call
    for host_name, conn_data in disconnect_connections["nrp1"]["nornir-worker-1"].items():
        assert len(conn_data["nornir_salt.plugins.tasks.connections"]) > 0, "No disconnected connections via nornir-worker-1"
        for item in conn_data["nornir_salt.plugins.tasks.connections"]:
            assert item["status"] == "closed", "Unexpected connection close status, host: {}, connection: {}".format(host_name, item)
    # verify active connections after disconnect
    for host_name, conn_data in active_connections_after_disconn["nrp1"]["nornir-worker-1"].items():
        assert len(conn_data["nornir_salt.plugins.tasks.connections"]) == 0, "Has active connections via nornir-worker-1"    
    # verify command run after disconnection
    assert "Clock source" in cli_cmd_after_disconnect["nrp1"]["ceos1-1"]["show clock"]
    assert "Clock source" in cli_cmd_after_disconnect["nrp1"]["ceos2-1"]["show clock"]
    # verify active connections after last command run
    for host_name, conn_data in active_connections_after_recon["nrp1"]["nornir-worker-1"].items():
        assert len(conn_data["nornir_salt.plugins.tasks.connections"]) > 0, "Has no active connections via nornir-worker-1 after reconnecting"
        for item in conn_data["nornir_salt.plugins.tasks.connections"]:
            assert "netmiko" in item["connection_name"] or "jumphost" in item["connection_name"], "Unexpected connection name"   
            
# test_connections_via_jumphost()


 
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


@pytest.fixture
def restore_pillar_proxy_always_alive(request):
    def restore():
        # restore pillar settings
        with open("/etc/salt/pillar/nrp1.sls", "r") as f:
            pillar_data = yaml.safe_load(f.read())
        pillar_data["proxy"].pop("proxy_always_alive", None)
        with open("/etc/salt/pillar/nrp1.sls", "w") as f:
            yaml.dump(pillar_data, f, default_flow_style=False)
        refresh_nrp1_pillar()
        # verify pillar data loaded
        proxy_pillar = client.cmd(
            tgt="nrp1",
            fun="pillar.raw",
            arg=[],
            kwarg={"key": "proxy"},
            tgt_type="glob",
            timeout=60,
        )   
        print("Restored nrp1 proxy pillar:")
        pprint.pprint(proxy_pillar)
        
    request.addfinalizer(restore)
    
def test_proxy_always_alive_false(restore_pillar_proxy_always_alive, remove_hosts_at_the_end):
    """
    To run with printing to screen::
    
        pytest -vv -s test_misc.py::test_proxy_always_alive_false
    """
    print("Updating proxy pillar.")
    # first update proxy pillar and refresh it
    with open("/etc/salt/pillar/nrp1.sls", "r") as f:
        pillar_data = yaml.safe_load(f.read())
    pillar_data["proxy"]["proxy_always_alive"] = False
    with open("/etc/salt/pillar/nrp1.sls", "w") as f:
        yaml.dump(pillar_data, f, default_flow_style=False)
    refresh_nrp1_pillar()
    # verify new pillar data loaded
    proxy_pillar = client.cmd(
        tgt="nrp1",
        fun="pillar.raw",
        arg=[],
        kwarg={"key": "proxy"},
        tgt_type="glob",
        timeout=60,
    )   
    print("Refreshed nrp1 proxy pillar:")
    pprint.pprint(proxy_pillar)
    assert proxy_pillar["nrp1"]["proxy_always_alive"] == False, "Proxy pillar not refreshed?"
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
            assert "clock" in t["nrp1"][wkr]["ceos1"]["show clock"].lower(), "Unexpected output from ceos1"
            assert "clock" in t["nrp1"][wkr]["ceos2"]["show clock"].lower(), "Unexpected output from ceos2"
            assert "clock" in t["nrp1"][wkr]["ceos1-1"]["show clock"].lower(), "Unexpected output from ceos1-1"
            assert "clock" in t["nrp1"][wkr]["ceos2-1"]["show clock"].lower(), "Unexpected output from ceos2-1"

            assert "traceback" not in t["nrp1"][wkr]["ceos1"]["show clock"].lower(), "Got traceback output from ceos1"
            assert "traceback" not in t["nrp1"][wkr]["ceos2"]["show clock"].lower(), "Got traceback output from ceos2"
            assert "traceback" not in t["nrp1"][wkr]["ceos1-1"]["show clock"].lower(), "Got traceback output from ceos1-1"
            assert "traceback" not in t["nrp1"][wkr]["ceos2-1"]["show clock"].lower(), "Got traceback output from ceos2-1"
            
    # verify connections status
    for t in connections:
        for wkr in ["nornir-worker-1", "nornir-worker-2", "nornir-worker-3"]:
            assert t["nrp1"][wkr]["ceos1"]["nornir_salt.plugins.tasks.connections"] == [], "Unexpected connections status for ceos1"
            assert t["nrp1"][wkr]["ceos2"]["nornir_salt.plugins.tasks.connections"] == [], "Unexpected connections status for ceos2"
            assert t["nrp1"][wkr]["ceos1-1"]["nornir_salt.plugins.tasks.connections"] == [], "Unexpected connections status for ceos1-1"
            assert t["nrp1"][wkr]["ceos2-1"]["nornir_salt.plugins.tasks.connections"] == [], "Unexpected connections status for ceos2-1"

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