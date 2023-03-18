"""
File to store common utility functions adn pytest fixtures.
"""
import logging
import pprint
import json
import time
import yaml
import pytest
import copy

try:
    import salt.client
    import salt.exceptions

    HAS_SALT = True
except:
    HAS_SALT = False
    raise SystemExit("SALT Nonrir Tests - failed importing SALT libraries")

if HAS_SALT:
    # initiate execution modules client to run 'salt xyz command' commands
    client = salt.client.LocalClient()
    
def refresh_nornir_proxy(target):   
    print(f"refresh_nornir_proxy:nr.nornir refreshing {target}")
    refresh_res = client.cmd(
        tgt=target,
        fun="nr.nornir",
        arg=["refresh"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )     
    print(f"refresh_nornir_proxy:nr.nornir '{target}' refresh call result: {refresh_res}")
    time.sleep(10)
    # wait for pillar to refresh
    start_time = time.time()
    while (time.time() - start_time) < 60:
        hosts = client.cmd(
            tgt=target,
            fun="nr.nornir",
            arg=["hosts"],
            kwarg={"FB": "*"},
            tgt_type="glob",
            timeout=60,
        ) 
        print(f"refresh_nornir_proxy:nornir hosts retrieved: {hosts}")
        if isinstance(hosts[target], list):
            break
        time.sleep(5)
    else:
        raise TimeoutError(f"'{target}' nr.nornir hosts no return in 60 seconds")
    client.cmd(
        tgt=target,
        fun="nr.nornir",
        arg=["refresh"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )     
    time.sleep(10) # give proxy minion some time to refresh
    
    
def updata_proxy_params_pillar(target, add=None, remove=None):
    """
    :param target: (str) minion id/name to refresh pillar for
    :param add: (dict) items to add to pillar
    :param remove: (list) items to remove from pillar
    """
    add = add or {}
    remove = remove or []
    print("\nUpdating '{}' proxy params pillar to add '{}' and remove '{}'".format(target, add, remove))
    # first update proxy pillar and refresh it
    with open("/etc/salt/pillar/{}.sls".format(target), "r") as f:
        pillar_data = yaml.safe_load(f.read())
        old_pillar_data = copy.deepcopy(pillar_data)
    # add items
    pillar_data["proxy"].update(add)
    # delete items
    for k in remove:
        _ = pillar_data["proxy"].pop(k)
    # save updates to pillar file
    with open("/etc/salt/pillar/nrp1.sls", "w") as f:
        yaml.dump(pillar_data, f, default_flow_style=False)
    time.sleep(5)
    # refresh nornir proxy
    refresh_nornir_proxy(target)
    # retrieve loaded pillar data
    proxy_pillar = client.cmd(
        tgt=target,
        fun="pillar.raw",
        arg=[],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )   
    print("Refreshed '{}', retrieved new proxy params pillar:".format(target))
    pprint.pprint(proxy_pillar["nrp1"]["proxy"])
    # verify pillar content
    try:
        for k, v in add.items():
            assert proxy_pillar["nrp1"]["proxy"][k] == v, "Proxy '{}' add param not added".format(k)
        for k in remove:
            assert k not in proxy_pillar["nrp1"]["proxy"], "Proxy '{}' del param not deleted".format(k)
    except Exception as e:
        print(f"Experienced error '{e}', restoring old pillar data.")
        with open("/etc/salt/pillar/nrp1.sls", "w") as f:
            yaml.dump(old_pillar_data, f, default_flow_style=False)        
        raise e

        
@pytest.fixture
def fixture_modify_proxy_pillar(request):
    """
    Fixture to update proxy parms pillar before stating test
    and remove same parameters after test finishes
    
    Expects one or several marker added to test:
    
    modify_pillar_target - proxy minion name to modify pillar for
    modify_pillar_pre_add - dictionry to merge with pillar params before running test
    modify_pillar_pre_remove - list of params names to remove before running test
    modify_pillar_post_add - dictionry to merge with pillar params after running test
    modify_pillar_post_remove - list of params names to remove after running test
    """
    target = request.node.get_closest_marker("modify_pillar_target")
    pre_add = request.node.get_closest_marker("modify_pillar_pre_add")
    pre_remove = request.node.get_closest_marker("modify_pillar_pre_remove")
    post_add = request.node.get_closest_marker("modify_pillar_post_add")
    post_remove = request.node.get_closest_marker("modify_pillar_post_remove")
    
    assert target, "Target required but not set"
    
    # extract first argument
    target = target.args[0]
    pre_add = pre_add.args[0] if pre_add else {}
    pre_remove = pre_remove.args[0] if pre_remove else []
    post_add = post_add.args[0] if post_add else {}
    post_remove = post_remove.args[0] if post_remove else []
    
    if pre_add or pre_remove:
        updata_proxy_params_pillar(target, add=pre_add, remove=pre_remove)
    
    def post_test():
        if post_add or post_remove:
            updata_proxy_params_pillar(target, add=post_add, remove=post_remove)
        
    request.addfinalizer(post_test)
    