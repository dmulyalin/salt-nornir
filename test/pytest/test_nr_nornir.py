import logging
import pprint
import time

log = logging.getLogger(__name__)

try:
    import salt.client

    from salt.exceptions import CommandExecutionError

    HAS_SALT = True
except:
    HAS_SALT = False
    raise SystemExit("SALT Nonrir Tests - failed importing SALT libraries")

if HAS_SALT:
    # initiate execution modules client to run 'salt xyz command' commands
    client = salt.client.LocalClient()


def test_nr_inventory_call():
    ret = client.cmd(
        tgt="nrp1", fun="nr.nornir", arg=["inventory"], kwarg={}, tgt_type="glob", timeout=60
    )
    assert (
        "nrp1" in ret
        and "defaults" in ret["nrp1"]
        and "groups" in ret["nrp1"]
        and "hosts" in ret["nrp1"]
        and len(ret["nrp1"]["hosts"]) == 2
    )


def test_nr_inventory_call_FB():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory"],
        kwarg={"FB": "ceos1"},
        tgt_type="glob",
        timeout=60,
    )
    assert (
        "nrp1" in ret
        and "defaults" in ret["nrp1"]
        and "groups" in ret["nrp1"]
        and "hosts" in ret["nrp1"]
        and len(ret["nrp1"]["hosts"]) == 1
    )


def test_nr_inventory_call_FL_no_match():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory"],
        kwarg={"FL": ["dummy"]},
        tgt_type="glob",
        timeout=60,
    )
    assert (
        "nrp1" in ret
        and "defaults" in ret["nrp1"]
        and "groups" in ret["nrp1"]
        and "hosts" in ret["nrp1"]
        and len(ret["nrp1"]["hosts"]) == 0
    )

def test_nr_version_call():
    ret = client.cmd(
        tgt="nrp1", fun="nr.nornir", arg=["version"], kwarg={}, tgt_type="glob", timeout=60
    )
    assert "nrp1" in ret
    assert isinstance(ret["nrp1"], str), "Unexpected data type returned"
    assert "Traceback" not in ret["nrp1"], "nr.version returned error"
    
def test_all_stats_call():
    ret = client.cmd(
        tgt="nrp1", fun="nr.nornir", arg=["stats"], kwarg={}, tgt_type="glob", timeout=60
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"].keys()) > 5


def test_single_stat_call():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["stats"],
        kwarg={"stat": "main_process_pid"},
        tgt_type="glob",
        timeout=60,
    )
    assert "nrp1" in ret
    assert len(ret["nrp1"].keys()) == 1

    
def test_connections_list_all_workers():
    # close connections
    client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["disconnect"],
        kwarg={"worker": "all"},
        tgt_type="glob",
        timeout=60,
    )    
    # run some cli commands
    client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"plugin": "netmiko", "worker": "all"},
        tgt_type="glob",
        timeout=60,
    )
    # list active connections
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["connections"],
        kwarg={"worker": "all"},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert len(ret["nrp1"]) == 3, "Was expecting results from 3 workers"
    for worker_name, res_data in ret["nrp1"].items():
        assert len(res_data["ceos1"]["connections:ls"]) == 1
        assert res_data["ceos1"]["connections:ls"][0]["connection_name"] == "netmiko"
        assert len(res_data["ceos2"]["connections:ls"]) == 1
        assert res_data["ceos2"]["connections:ls"][0]["connection_name"] == "netmiko"
    
# test_connections_list_all_workers()


def test_connections_list_worker_1_only():
    # close connections
    client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["disconnect"],
        kwarg={"worker": 1},
        tgt_type="glob",
        timeout=60,
    )    
    # run some cli commands
    client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"plugin": "netmiko", "worker": 1},
        tgt_type="glob",
        timeout=60,
    )
    # list active connections
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["connections"],
        kwarg={"worker": 1},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    assert len(ret["nrp1"]["ceos1"]["connections:ls"]) == 1
    assert ret["nrp1"]["ceos1"]["connections:ls"][0]["connection_name"] == "netmiko"
    assert len(ret["nrp1"]["ceos2"]["connections:ls"]) == 1
    assert ret["nrp1"]["ceos2"]["connections:ls"][0]["connection_name"] == "netmiko"
    
# test_connections_list_worker_1_only()


def test_disconnect_worker_all():
    # run some cli commands
    client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"plugin": "netmiko", "worker": "all"},
        tgt_type="glob",
        timeout=60,
    )
    # close connections from all workers by default
    client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["disconnect"],
        tgt_type="glob",
        timeout=60,
    )   
    # list active connections
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["connections"],
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert len(ret["nrp1"]) == 3
    for worker_name, res_data in ret["nrp1"].items():
        assert len(res_data["ceos1"]["connections:ls"]) == 0
        assert len(res_data["ceos2"]["connections:ls"]) == 0
    
# test_disconnect_worker_all()


def test_disconnect_worker_1():
    # run some cli commands
    client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"plugin": "netmiko", "worker": 1},
        tgt_type="glob",
        timeout=60,
    )
    # close connections from 1st worker
    disconnect_ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["disconnect"],
        kwarg={"worker": 1},
        tgt_type="glob",
        timeout=60,
    )   
    # list active connections
    connections_ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["connections"],
        kwarg={"worker": 1},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(disconnect_ret)
    pprint.pprint(connections_ret)

    assert disconnect_ret["nrp1"]["ceos1"]["connections:close"][0]["connection_name"] == "netmiko"
    assert disconnect_ret["nrp1"]["ceos1"]["connections:close"][0]["status"] == "closed"
    assert disconnect_ret["nrp1"]["ceos2"]["connections:close"][0]["connection_name"] == "netmiko"
    assert disconnect_ret["nrp1"]["ceos2"]["connections:close"][0]["status"] == "closed"
    
    assert len(connections_ret["nrp1"]["ceos1"]["connections:ls"]) == 0
    assert len(connections_ret["nrp1"]["ceos2"]["connections:ls"]) == 0
    
# test_disconnect_worker_1()

def test_disconnect_by_name_all_workers():
    # close all connections
    initial_disconnect_all_call = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["disconnect"],
        tgt_type="glob",
        timeout=60,
    ) 
    print("initial_disconnect_all_call:")
    pprint.pprint(initial_disconnect_all_call)
    # run some cli commands
    client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"plugin": "netmiko", "worker": "all"},
        tgt_type="glob",
        timeout=60,
    )
    client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"plugin": "scrapli", "worker": "all"},
        tgt_type="glob",
        timeout=60,
    )
    # get active connections for all workers
    ret_before = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["connections"],
        tgt_type="glob",
        timeout=60,
    )
    print("active connections before disconnect:")
    pprint.pprint(ret_before)
    conn_count_before_ceos1, conn_count_before_ceos2 = [], []
    for worker_name, res_data in ret_before["nrp1"].items():
        conn_count_before_ceos1.append(len(res_data["ceos1"]["connections:ls"]))
        conn_count_before_ceos2.append(len(res_data["ceos2"]["connections:ls"]))
        
    # close scrapli connections for all workers for ceos1 only
    scrapli_disconect_call = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["disconnect"],
        kwarg={"conn_name": "scrapli", "FB": "ceos1"},
        tgt_type="glob",
        timeout=60,
    )  
    print("scrapli_disconect_call:")
    pprint.pprint(scrapli_disconect_call)
    # list active connections
    ret_after = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["connections"],
        tgt_type="glob",
        timeout=60,
    )
    print("active connections after disconnect:")
    pprint.pprint(ret_after)
    conn_count_after_ceos1, conn_count_after_ceos2 = [], []
    for worker_name, res_data in ret_after["nrp1"].items():
        conn_count_after_ceos1.append(len(res_data["ceos1"]["connections:ls"]))
        conn_count_after_ceos2.append(len(res_data["ceos2"]["connections:ls"]))
    
    # verify connections count
    pprint.pprint(conn_count_before_ceos1)
    pprint.pprint(conn_count_after_ceos1)
    assert conn_count_before_ceos1 == [2, 2, 2] and conn_count_after_ceos1 == [1, 1, 1]
    assert conn_count_before_ceos2 == [2, 2, 2] and conn_count_after_ceos2 == [2, 2, 2]
    
    # verify that not-closed connections are netmiko
    for worker_name, res_data in ret_after["nrp1"].items(): 
        assert res_data["ceos1"]["connections:ls"][0]["connection_name"] == "netmiko"
    
# test_disconnect_by_name_all_workers()


def test_inventory_create_and_delete_host_all_workers():
    # add new host
    res = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory"],
        kwarg={
            "call": "create",
            "name": "ceos1-1",
            "hostname": "10.0.1.4",
            "platform": "arista_eos",
            "groups": ["lab", "eos_params"],
        },
        tgt_type="glob",
        timeout=60,
    ) 
    print("ceos1-1 host add results:")
    pprint.pprint(res)
    for worker_name, res_data in res["nrp1"].items():
        assert res_data == {"ceos1-1": True}, "Failed to create new host, worker: {}".format(worker_name)
    
    # verify new host added
    hosts_list = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["hosts"]
    ) 
    # pprint.pprint(hosts_list)
    assert "ceos1-1" in hosts_list["nrp1"], "New host not in hosts list"
    
    # try to get commands output from new host
    output = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock", "show hostname"],
        kwarg={"FB": "ceos1-1", "add_details": True},
        tgt_type="glob",
        timeout=60,
    ) 
    # pprint.pprint(output)
    assert output["nrp1"]["ceos1-1"]["show clock"]["exception"] == None
    assert output["nrp1"]["ceos1-1"]["show clock"]["failed"] == False
    assert output["nrp1"]["ceos1-1"]["show hostname"]["exception"] == None
    assert output["nrp1"]["ceos1-1"]["show hostname"]["failed"] == False
    
    # delete new host from inventory
    delete_res = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory"],
        kwarg={
            "call": "delete",
            "name": "ceos1-1"
        },
        tgt_type="glob",
        timeout=60,
    )     
    print("ceos1-1 host delete results:")
    pprint.pprint(delete_res)
    for worker_name, res_data in res["nrp1"].items():
        assert res_data == {"ceos1-1": True}, "Failed to delete host ceos1-1, worker: {}".format(worker_name)
    
    # verify host deleted
    hosts_list = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["hosts"]
    ) 
    assert "ceos1-1" not in hosts_list["nrp1"], "Host not deleted from inventory"
    
# test_inventory_create_and_delete_host_all_workers()


def test_inventory_update_host_data():
    # update host data
    res = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory"],
        kwarg={
            "call": "update",
            "name": "ceos1",
            "data": {
                "Loopback123": {
                    "ip": "1.2.3.4",
                    "description": "Host update test"
                }
            }
        },
        tgt_type="glob",
        timeout=60,
    ) 
    
    # generate config using updated data
    cfg_gen_result = client.cmd(
        tgt="nrp1",
        fun="nr.cfg_gen",
        arg=[
            """
            interface Loopback123 
             ip address {{ host["Loopback123"]["ip"] }}
             description {{ host["Loopback123"]["description"] }}
        """],
        kwarg={"FB": "ceos1"},
        tgt_type="glob",
        timeout=60,
    )     
    # pprint.pprint(cfg_gen_result)
    # {'nrp1': {'ceos1': {'salt_cfg_gen': '\n'
    #                     '            interface Loopback123 \n'
    #                     '             ip address 1.2.3.4\n'
    #                     '             description Host update '
    #                     'test\n'
    #                     '        '}}}
    assert "ip address 1.2.3.4" in cfg_gen_result["nrp1"]["ceos1"]["salt_cfg_gen"]
    assert "description Host update test" in cfg_gen_result["nrp1"]["ceos1"]["salt_cfg_gen"]
    
# test_inventory_update_host_data()

def test_inventory_read_host_data():
    # read host data
    res = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory"],
        kwarg={
            "call": "read",
            "FB": "ceos2",
        },
        tgt_type="glob",
        timeout=60,
    ) 
    # pprint.pprint(res)
    assert isinstance(res["nrp1"]["ceos2"], dict)
    assert "platform" in res["nrp1"]["ceos2"]
    assert "hostname" in res["nrp1"]["ceos2"]
    
# test_inventory_read_host_data()

def test_inventory_read_host_data_using_arg():
    # read host data
    res = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory", "read_host"],
        kwarg={
            "FB": "ceos2",
        },
        tgt_type="glob",
        timeout=60,
    ) 
    # pprint.pprint(res)
    assert isinstance(res["nrp1"]["ceos2"], dict)
    assert "platform" in res["nrp1"]["ceos2"]
    assert "hostname" in res["nrp1"]["ceos2"]
    
# test_inventory_read_host_data_using_arg()

def test_nr_nornir_worker_stats_using_args():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["worker", "stats"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )      
    pprint.pprint(ret)
    assert len(ret["nrp1"]) == 3, "Unexpected number of workers, was expecting 3"
    for name, wkr in ret["nrp1"].items():
        assert "is_busy" in wkr
        assert "worker_connections" in wkr
        assert "worker_hosts_tasks_failed" in wkr
        assert "worker_jobs_completed" in wkr
        assert "worker_jobs_failed" in wkr
        assert "worker_jobs_queue" in wkr
        assert "worker_jobs_started" in wkr
        
# test_nr_nornir_worker_stats_using_args()


def test_nr_nornir_worker_stats_using_args_and_kwargs():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["worker"],
        kwarg={"call": "stats"},
        tgt_type="glob",
        timeout=60,
    )      
    pprint.pprint(ret)
    assert len(ret["nrp1"]) == 3, "Unexpected number of workers, was expecting 3"
    for name, wkr in ret["nrp1"].items():
        assert "is_busy" in wkr
        assert "worker_connections" in wkr
        assert "worker_hosts_tasks_failed" in wkr
        assert "worker_jobs_completed" in wkr
        assert "worker_jobs_failed" in wkr
        assert "worker_jobs_queue" in wkr
        assert "worker_jobs_started" in wkr
        
# test_nr_nornir_worker_stats_using_args_and_kwargs()


def test_nr_nornir_results_queue_dump():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["results_queue_dump"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )      
    pprint.pprint(ret)
    assert ret["nrp1"] == [], "Unexpected return for results_queue_dump"
    

def test_nr_nornir_connect_netmiko_use_inventory():
    _ = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["disconnect"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    ) 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["connect", "netmiko"],
        kwarg={"add_details": True},
        tgt_type="glob",
        timeout=60,
    )      
    pprint.pprint(ret)
    # verify result contain message: Connected with 'kwargs' parameters
    assert "connected" in ret["nrp1"]["ceos1"]['connections:open:netmiko']["result"]
    assert "primary connection parameters" in ret["nrp1"]["ceos1"]['connections:open:netmiko']["result"]
    assert "connected" in ret["nrp1"]["ceos2"]['connections:open:netmiko']["result"]
    assert "primary connection parameters" in ret["nrp1"]["ceos2"]['connections:open:netmiko']["result"]
    
    
def test_nr_nornir_connect_netmiko_use_kwargs():
    _ = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["disconnect"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    ) 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["connect", "netmiko"],
        kwarg={"add_details": True, "username": "nornir", "password": "nornir", "port": 22},
        tgt_type="glob",
        timeout=60,
    )      
    pprint.pprint(ret)
    # verify result contain message: Connected with 'kwargs' parameters
    assert "connected" in ret["nrp1"]["ceos1"]['connections:open:netmiko']["result"]
    assert "primary connection parameters" in ret["nrp1"]["ceos1"]['connections:open:netmiko']["result"]
    assert "connected" in ret["nrp1"]["ceos2"]['connections:open:netmiko']["result"]
    assert "primary connection parameters" in ret["nrp1"]["ceos2"]['connections:open:netmiko']["result"]
    
    
def test_nr_nornir_connect_netmiko_use_reconnect():
    _ = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["disconnect"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    ) 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["connect", "netmiko"],
        kwarg={
            "add_details": True, 
            "username": "wrong", 
            "password": "wrong", 
            "reconnect": [
                {
                    "username": "wrong_port",
                    "password": "wrong_port",
                    "port": 2022,
                },
                {
                    "username": "nornir",
                    "password": "nornir",
                    "port": 22,
                }
            ]
        },
        tgt_type="glob",
        timeout=60,
    )      
    pprint.pprint(ret)
    # verify result contain message: "Connected with reconnect index '1'"
    assert "connected" in ret["nrp1"]["ceos1"]['connections:open:netmiko']["result"]
    assert "index '1'" in ret["nrp1"]["ceos1"]['connections:open:netmiko']["result"]
    assert "connected" in ret["nrp1"]["ceos2"]['connections:open:netmiko']["result"]
    assert "index '1'" in ret["nrp1"]["ceos2"]['connections:open:netmiko']["result"]
    

def test_nr_nornir_connect_netmiko_use_reconnect_credentials():
    _ = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["disconnect"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    ) 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["connect", "netmiko"],
        kwarg={
            "add_details": True, 
            "username": "wrong", 
            "password": "wrong", 
            "reconnect": [
                {
                    "username": "wrong_port",
                    "password": "wrong_port",
                    "port": 2022,
                },
                "deprecated_creds",
                "local_account",
            ]
        },
        tgt_type="glob",
        timeout=60,
    )      
    pprint.pprint(ret)
    # verify result contain message: "Connected with 'local_account' parameters, reconnect index '2'"
    assert "connected" in ret["nrp1"]["ceos1"]['connections:open:netmiko']["result"]
    assert "local_account" in ret["nrp1"]["ceos1"]['connections:open:netmiko']["result"]
    assert "connected" in ret["nrp1"]["ceos2"]['connections:open:netmiko']["result"]
    assert "local_account" in ret["nrp1"]["ceos2"]['connections:open:netmiko']["result"]
    
    
def test_nr_nornir_connect_netmiko_close_open():
    _ = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["disconnect"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    ) 
    connect_res = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["connect", "netmiko"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )    
    connect_close_open_false = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["connect", "netmiko"],
        kwarg={"close_open": False},
        tgt_type="glob",
        timeout=60,
    ) 
    connect_close_open_true = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["connect", "netmiko"],
        kwarg={"close_open": True},
        tgt_type="glob",
        timeout=60,
    ) 
    print("Initial connection result:")
    pprint.pprint(connect_res)
    print("Connection result close_open=False:")
    pprint.pprint(connect_close_open_false)
    print("Connection result close_open=True:")
    pprint.pprint(connect_close_open_true)

    # verify connection left intact on close_open=False
    assert "Connection already open" in connect_close_open_false["nrp1"]["ceos1"]['connections:open:netmiko']
    assert "Connection already open" in connect_close_open_false["nrp1"]["ceos2"]['connections:open:netmiko']
    
    # verify connection re-established on close_open=True
    assert "connected" in connect_close_open_true["nrp1"]["ceos1"]['connections:open:netmiko']
    assert "primary connection parameters" in connect_close_open_true["nrp1"]["ceos1"]['connections:open:netmiko']
    assert "connected" in connect_close_open_true["nrp1"]["ceos2"]['connections:open:netmiko']
    assert "primary connection parameters" in connect_close_open_true["nrp1"]["ceos2"]['connections:open:netmiko']
    
    
def test_nr_nornir_connect_netmiko_all_failed():
    _ = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["disconnect"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    ) 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["connect", "netmiko"],
        kwarg={
            "add_details": True, 
            "username": "wrong", 
            "password": "wrong", 
            "reconnect": [
                {
                    "username": "wrong_too",
                    "password": "wrong_too",
                }
            ]
        },
        tgt_type="glob",
        timeout=60,
    )      
    pprint.pprint(ret)
    assert "Traceback" in ret["nrp1"]["ceos1"]['connections:open:netmiko']["result"]
    assert "Traceback" in ret["nrp1"]["ceos2"]['connections:open:netmiko']["result"]
    assert ret["nrp1"]["ceos1"]['connections:open:netmiko']["failed"] == True
    assert ret["nrp1"]["ceos2"]['connections:open:netmiko']["failed"] == True
    
    
def test_nr_nornir_connect_wrong_conn_name():
    _ = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["disconnect"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    ) 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["connect", "netmikosss"],
        kwarg={"add_details": True},
        tgt_type="glob",
        timeout=60,
    )      
    pprint.pprint(ret)
    assert "Traceback" in ret["nrp1"]["ceos1"]['connections:open:netmikosss']["result"]
    assert "Traceback" in ret["nrp1"]["ceos2"]['connections:open:netmikosss']["result"]
    assert ret["nrp1"]["ceos1"]['connections:open:netmikosss']["failed"] == True
    assert ret["nrp1"]["ceos2"]['connections:open:netmikosss']["failed"] == True
    assert "PluginNotRegistered" in ret["nrp1"]["ceos1"]['connections:open:netmikosss']["result"]
    assert "PluginNotRegistered" in ret["nrp1"]["ceos2"]['connections:open:netmikosss']["result"]
    
    
def test_nr_nornir_connect_wrong_creds_set():
    _ = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["disconnect"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    ) 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["connect", "netmikosss"],
        kwarg={
            "add_details": True,
            "username": "wrong",
            "reconnect": [
                "not_exists",                
            ]
        },
        tgt_type="glob",
        timeout=60,
    )      
    pprint.pprint(ret)
    assert "Traceback" in ret["nrp1"]["ceos1"]['connections:open:netmikosss']["result"]
    assert "Traceback" in ret["nrp1"]["ceos2"]['connections:open:netmikosss']["result"]
    assert "parameters not found or invalid" in ret["nrp1"]["ceos1"]['connections:open:netmikosss']["result"]
    assert "parameters not found or invalid" in ret["nrp1"]["ceos2"]['connections:open:netmikosss']["result"]
    
    
def test_nr_nornir_connect_scrapli_use_inventory():
    _ = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["disconnect"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    ) 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["connect", "scrapli"],
        kwarg={"add_details": True},
        tgt_type="glob",
        timeout=60,
    )      
    pprint.pprint(ret)
    # verify result contain message: Connected with 'kwargs' parameters
    assert "connected" in ret["nrp1"]["ceos1"]['connections:open:scrapli']["result"]
    assert "primary connection parameters" in ret["nrp1"]["ceos1"]['connections:open:scrapli']["result"]
    assert "connected" in ret["nrp1"]["ceos2"]['connections:open:scrapli']["result"]
    assert "primary connection parameters" in ret["nrp1"]["ceos2"]['connections:open:scrapli']["result"]
    
    
def test_nr_nornir_connect_napalm_reconnect_several_good_creds():
    _ = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["disconnect"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    ) 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["connect", "napalm"],
        kwarg={
            "add_details": True, 
            "username": "wrong", 
            "password": "wrong", 
            "reconnect": [
                {
                    "username": "nornir",
                    "password": "nornir",
                },
                "local_account",
            ]
        },
        tgt_type="glob",
        timeout=60,
    )      
    pprint.pprint(ret)
    # verify result contain message: "Connected with reconnect index '1'"
    assert "connected" in ret["nrp1"]["ceos1"]['connections:open:napalm']["result"]
    assert "index '0'" in ret["nrp1"]["ceos1"]['connections:open:napalm']["result"]
    assert "connected" in ret["nrp1"]["ceos2"]['connections:open:napalm']["result"]
    assert "index '0'" in ret["nrp1"]["ceos2"]['connections:open:napalm']["result"]
    
    
def test_connect_netmiko_via():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["connect", "netmiko"],
        kwarg={"add_details": True, "via": "inband"},
        tgt_type="glob",
        timeout=60,
    )      
    pprint.pprint(ret)    
    assert ret["nrp1"]["ceos1"]["connections:open:netmiko"]["failed"] == False
    assert "'netmiko' connected via 'inband'" in ret["nrp1"]["ceos1"]["connections:open:netmiko"]["result"]
    assert ret["nrp1"]["ceos2"]["connections:open:netmiko"]["failed"] == True
    assert "'inband' parameters not found" in ret["nrp1"]["ceos2"]["connections:open:netmiko"]["result"]
    
    
def test_connect_scrapli_via():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["connect", "scrapli"],
        kwarg={"add_details": True, "via": "inband"},
        tgt_type="glob",
        timeout=60,
    )      
    pprint.pprint(ret)    
    assert ret["nrp1"]["ceos1"]["connections:open:scrapli"]["failed"] == False
    assert "'scrapli' connected via 'inband'" in ret["nrp1"]["ceos1"]["connections:open:scrapli"]["result"]
    assert ret["nrp1"]["ceos2"]["connections:open:scrapli"]["failed"] == True
    assert "'inband' parameters not found" in ret["nrp1"]["ceos2"]["connections:open:scrapli"]["result"]
    
    
def test_connect_netmiko_via_redispatch():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["connect", "netmiko"],
        kwarg={"add_details": True, "via": "console"},
        tgt_type="glob",
        timeout=60,
    )      
    pprint.pprint(ret)    
    assert ret["nrp1"]["ceos1"]["connections:open:netmiko"]["failed"] == False
    assert "'netmiko' connected using 'console'" in ret["nrp1"]["ceos1"]["connections:open:netmiko"]["result"]
    assert ret["nrp1"]["ceos2"]["connections:open:netmiko"]["failed"] == True
    assert "'console' parameters not found" in ret["nrp1"]["ceos2"]["connections:open:netmiko"]["result"]
    
    
def test_connect_scrapli_via_redispatch():
    """scrapli not supported for redispatch, so should fail"""
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["connect", "scrapli"],
        kwarg={"add_details": True, "via": "console", "FB": "ceos1"},
        tgt_type="glob",
        timeout=60,
    )      
    pprint.pprint(ret)    
    assert ret["nrp1"]["ceos1"]["connections:open:scrapli"]["failed"] == True
    assert "'scrapli' redispatch not supported" in ret["nrp1"]["ceos1"]["connections:open:scrapli"]["result"]

    
def test_connect_netmiko_via_redispatch_console2():
    """console2 has reduced set of parameters to establish connection"""
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["connect", "netmiko"],
        kwarg={"add_details": True, "via": "console2", "FB": "ceos1"},
        tgt_type="glob",
        timeout=60,
    )      
    pprint.pprint(ret)    
    assert ret["nrp1"]["ceos1"]["connections:open:netmiko"]["failed"] == False
    assert "'netmiko' connected using 'console2'" in ret["nrp1"]["ceos1"]["connections:open:netmiko"]["result"]
    assert "redispatch" in ret["nrp1"]["ceos1"]["connections:open:netmiko"]["result"]
    

def test_read_host_data():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory", "read_host_data"],
        kwarg={"keys": ["tests.suite1", "interfaces_test", "foo.bar"]},
        tgt_type="glob",
        timeout=60,
    )      
    pprint.pprint(ret)
    assert ret["nrp1"]["ceos1"]["foo.bar"] is None
    assert ret["nrp1"]["ceos1"]["interfaces_test"] is not None
    assert ret["nrp1"]["ceos1"]["tests.suite1"] is not None
    assert ret["nrp1"]["ceos2"]["foo.bar"] is None
    assert ret["nrp1"]["ceos2"]["interfaces_test"] is None
    assert ret["nrp1"]["ceos2"]["tests.suite1"] is None
    
    
def test_nr_nornir_inventory_update_defaults():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory", "update_defaults"],
        kwarg={
            "username": "foo",
            "password": "bar",
            "data": {"foo1": "bar1"},
            "connection_options": {"foo_conn": {"platform": "bar", "username": "bar2"}},
            "port": 1234,
            "platform": "foobar",
            "foo123": "bar123",
        },
        tgt_type="glob",
        timeout=60,
    )      
    pprint.pprint(ret)    
    inventory_data = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )      
    pprint.pprint(inventory_data)
    # trigger inventory refresh to wipe out defaults changes
    _ = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["refresh"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    ) 
    time.sleep(20)
    assert ret == {'nrp1': {'nornir-worker-1': True,
          'nornir-worker-2': True,
          'nornir-worker-3': True}}
    assert inventory_data["nrp1"]["defaults"]["connection_options"]["foo_conn"]["username"] == "bar2"
    assert inventory_data["nrp1"]["defaults"]["connection_options"]["foo_conn"]["platform"] == "bar"
    assert inventory_data["nrp1"]["defaults"]["data"]["foo1"] == "bar1"
    assert inventory_data["nrp1"]["defaults"]["data"]["foo123"] == "bar123"    
    assert inventory_data["nrp1"]["defaults"]["platform"] == "foobar"    
    assert inventory_data["nrp1"]["defaults"]["port"] == 1234        
    assert inventory_data["nrp1"]["defaults"]["username"] == "foo"   
    assert inventory_data["nrp1"]["defaults"]["password"] == "bar" 

    
def test_nr_nornir_inventory_update_defaults_to_none():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory", "update_defaults"],
        kwarg={
            "username": "foo",
            "password": "bar",
            "port": 1234,
            "platform": "foobar",
        },
        tgt_type="glob",
        timeout=60,
    )      
    pprint.pprint(ret)    
    inventory_data = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )      
    pprint.pprint(inventory_data)
    ret2 = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory", "update_defaults"],
        kwarg={
            "username": None,
            "password": None,
            "port": None,
            "platform": None,
        },
        tgt_type="glob",
        timeout=60,
    )     
    inventory_data2 = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["inventory"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )  
    # trigger inventory refresh to wipe out defaults changes
    _ = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["refresh"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    ) 
    time.sleep(20)
    # verify inventory was updated
    assert ret == {'nrp1': {'nornir-worker-1': True,
          'nornir-worker-2': True,
          'nornir-worker-3': True}}  
    assert inventory_data["nrp1"]["defaults"]["platform"] == "foobar"    
    assert inventory_data["nrp1"]["defaults"]["port"] == 1234        
    assert inventory_data["nrp1"]["defaults"]["username"] == "foo" 
    assert inventory_data["nrp1"]["defaults"]["password"] == "bar" 
    # verify params set to None
    assert ret2 == {'nrp1': {'nornir-worker-1': True,
          'nornir-worker-2': True,
          'nornir-worker-3': True}}
    assert inventory_data2["nrp1"]["defaults"]["platform"] == None 
    assert inventory_data2["nrp1"]["defaults"]["port"] == None        
    assert inventory_data2["nrp1"]["defaults"]["username"] == None
    assert inventory_data2["nrp1"]["defaults"]["password"] == None