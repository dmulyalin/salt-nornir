import logging
import pprint
import pytest
import json

log = logging.getLogger(__name__)

try:
    import salt.client

    from salt.exceptions import CommandExecutionError

    HAS_SALT = True
except:
    HAS_SALT = False
    raise SystemExit("SALT Nonrir Tests - failed importing SALT libraries")

try:
    import requests
    HAS_REQUESTS = True
except:
    HAS_REQUESTS = False
    
if HAS_SALT:
    # initiate execution modules client to run 'salt xyz command' commands
    client = salt.client.LocalClient()


SALT_API_URL = "http://127.0.0.1:8000/run"
SALT_API_HEADERS = {"Accept": "application/json", "Content-type": "application/json"}


def test_cherrypy_api_nr_cli():
    payload = [
        {
            "client": "local", 
            "tgt": "nrp1", 
            "fun": "nr.cli", 
            "username": "saltuser", 
            "password": "saltpass", 
            "eauth": "sharedsecret", 
            "arg": ["show clock", "show hostname"],
            "kwarg": {"FB": "*"},
        }
    ]
    ret = requests.post(
        SALT_API_URL, 
        data=json.dumps(payload),
        headers=SALT_API_HEADERS,
    )
    res = ret.json()
    pprint.pprint(res)
    assert "Traceback" not in res["return"][0]["nrp1"]["ceos1"]["show clock"]
    assert "Traceback" not in res["return"][0]["nrp1"]["ceos1"]["show hostname"]
    assert "Traceback" not in res["return"][0]["nrp1"]["ceos2"]["show clock"]
    assert "Traceback" not in res["return"][0]["nrp1"]["ceos2"]["show hostname"]
    
# test_nr_cli()


def test_cherrypy_api_nr_cfg():
    payload = [
        {
            "client": "local", 
            "tgt": "nrp1", 
            "fun": "nr.cfg", 
            "username": "saltuser", 
            "password": "saltpass", 
            "eauth": "sharedsecret", 
            "arg": ["vlan 3900", "name VLAN3900"],
            "kwarg": {"FB": "ceos1", "plugin": "netmiko"},
        }
    ]
    ret = requests.post(
        SALT_API_URL, 
        data=json.dumps(payload),
        headers=SALT_API_HEADERS,
    )
    res = ret.json()
    pprint.pprint(res, width=150)
    assert res["return"][0]["nrp1"]["ceos1"]["netmiko_send_config"]["failed"] == False
    assert "Traceback" not in res["return"][0]["nrp1"]["ceos1"]["netmiko_send_config"]["result"]
    
# test_cherrypy_api_nr_cfg()


def test_cherrypy_api_nr_cfg_multiline():
    payload = [
        {
            "client": "local", 
            "tgt": "nrp1", 
            "fun": "nr.cfg", 
            "username": "saltuser", 
            "password": "saltpass", 
            "eauth": "sharedsecret", 
            "arg": ["vlan 3900\nname VLAN3900"],
            "kwarg": {"FB": "ceos1", "plugin": "netmiko"},
        }
    ]
    ret = requests.post(
        SALT_API_URL, 
        data=json.dumps(payload),
        headers=SALT_API_HEADERS,
    )
    res = ret.json()
    pprint.pprint(res, width=150)
    assert res["return"][0]["nrp1"]["ceos1"]["netmiko_send_config"]["failed"] == False
    assert "Traceback" not in res["return"][0]["nrp1"]["ceos1"]["netmiko_send_config"]["result"]
    
   
def test_cherrypy_api_nr_cfg_escaped_multiline():
    payload = [
        {
            "client": "local", 
            "tgt": "nrp1", 
            "fun": "nr.cfg", 
            "username": "saltuser", 
            "password": "saltpass", 
            "eauth": "sharedsecret", 
            "arg": ["vlan 3900\\nname VLAN3900"],
            "kwarg": {"FB": "ceos1", "plugin": "netmiko"},
        }
    ]
    ret = requests.post(
        SALT_API_URL, 
        data=json.dumps(payload),
        headers=SALT_API_HEADERS,
    )
    res = ret.json()
    pprint.pprint(res, width=150)
    assert res["return"][0]["nrp1"]["ceos1"]["netmiko_send_config"]["failed"] == False
    assert "Traceback" not in res["return"][0]["nrp1"]["ceos1"]["netmiko_send_config"]["result"]