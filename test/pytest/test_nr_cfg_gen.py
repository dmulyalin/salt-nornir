import logging
import pprint

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


def test_nr_cfg_gen_from_static_file():
    """
    Test configuration generation from file.

    ret should look like::

        nrp1:
            ----------
            ceos1:
                ----------
                Rendered salt://templates/ntp_config.txt config:
                    ntp server 2.2.2.2
                    ntp server 2.2.2.3
            ceos2:
                ----------
                Rendered salt://templates/ntp_config.txt config:
                    ntp server 2.2.2.2
                    ntp server 2.2.2.3
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg_gen",
        arg=[],
        kwarg={"filename": "salt://templates/ntp_config.txt"},
        tgt_type="glob",
        timeout=60,
    )
    task_name = "salt_cfg_gen"
    for host, results in ret["nrp1"].items():
        assert len(results.keys()) == 1, "Got additional results: {}".format(results)
        assert task_name in results
        assert isinstance(results[task_name], str)
        assert len(results[task_name]) > 0


def test_nr_cfg_gen_from_template_file():
    """
    Test configuration generation from template file.

    ret should look like::

        nrp1:
            ----------
            ceos1:
                ----------
                Rendered salt://templates/ntp_config_template.txt config:

                    ntp server 3.3.3.3
                    ntp server 3.3.3.4
                    logging host 1.2.3.4
                    logging host 4.3.2.1
            ceos2:
                ----------
                Rendered salt://templates/ntp_config_template.txt config:

                    ntp server 3.3.3.3
                    ntp server 3.3.3.4
                    logging host 1.2.3.4
                    logging host 4.3.2.1
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg_gen",
        arg=[],
        kwarg={"filename": "salt://templates/ntp_config_template.txt"},
        tgt_type="glob",
        timeout=60,
    )
    for host, results in ret["nrp1"].items():
        assert len(results.keys()) == 1, "Got additional results: {}".format(results)
        assert isinstance(results["salt_cfg_gen"], str)
        assert len(results["salt_cfg_gen"]) > 0
        assert "ntp" in results["salt_cfg_gen"] and "logging" in results["salt_cfg_gen"]


def test_nr_cfg_gen_from_static_file_per_host():
    """
    Test configuration generation from file per host.

    ret should look like::

        nrp1:
            ----------
            ceos1:
                ----------
                Rendered salt://templates/per_host_cfg_snmp/{{ host.name }}.txt config:
                    snmp-server location "North West Hall DC1"
            ceos2:
                ----------
                Rendered salt://templates/per_host_cfg_snmp/{{ host.name }}.txt config:
                    snmp-server location "East City Warehouse"
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg_gen",
        arg=[],
        kwarg={"filename": "salt://templates/per_host_cfg_snmp/{{ host.name }}.txt"},
        tgt_type="glob",
        timeout=60,
    )
    task_name = "salt_cfg_gen"
    for host, results in ret["nrp1"].items():
        assert len(results.keys()) == 1, "Got additional results: {}".format(results)
        assert task_name in results
        assert isinstance(results[task_name], str)
        assert len(results[task_name]) > 0
    assert "North" in ret["nrp1"]["ceos1"][task_name]
    assert "East" in ret["nrp1"]["ceos2"][task_name]


def test_nr_cfg_gen_from_template_file_per_host():
    """
    Test configuration generation from file per host.

    ret should look like::

        nrp1:
            ----------
            ceos1:
                ----------
                Rendered salt://templates/per_host_cfg_snmp_template/{{ host.name }}.txt config:
                    snmp-server location North West Hall DC1
            ceos2:
                ----------
                Rendered salt://templates/per_host_cfg_snmp_template/{{ host.name }}.txt config:
                    snmp-server location Address East City Warehouse
    """
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg_gen",
        arg=[],
        kwarg={
            "filename": "salt://templates/per_host_cfg_snmp_template/{{ host.name }}.txt"
        },
        tgt_type="glob",
        timeout=60,
    )
    task_name = "salt_cfg_gen"
    for host, results in ret["nrp1"].items():
        assert len(results.keys()) == 1, "Got additional results: {}".format(results)
        assert task_name in results
        assert isinstance(results[task_name], str)
        assert len(results[task_name]) > 0
    assert "North" in ret["nrp1"]["ceos1"][task_name]
    assert "East" in ret["nrp1"]["ceos2"][task_name]

    
def test_jinja_whitespace_handling_template_file():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg_gen",
        arg=[],
        kwarg={
            "filename": "salt://templates/jinja_whitespace_test.j2",
            "FB": "ceos1",
        },
        tgt_type="glob",
        timeout=60,
    )    
    pprint.pprint(ret)
    assert ret == {'nrp1': {'ceos1': {'salt_cfg_gen': '123'}}}
    
def test_jinja_env_config_handling():
    message = """
    jinja_env config for nrp1 should be taken from master config faile::
    
        pillar_opts: true
        jinja_env:
          lstrip_blocks: true
          trim_blocks: true
      
    as a result this template::
    
        {% for i in ['1', '2', '3'] %}
        {{ i }}
        {% endfor %}
        
    should render to this::
    
        {'nrp1': {'ceos1': {'salt_cfg_gen': '1\n2\n3\n'}}}
        
    for nrp2 config should be taken from pillar::
    
        jinja_env:
          lstrip_blocks: false
          trim_blocks: false
          
    as a result same template should render to::
    
        {'nrp1': {'ceos1': {'salt_cfg_gen': '\n1\n\n2\n\n3\n'}}}    
    """
    ret_nrp1 = client.cmd(
        tgt="nrp1",
        fun="nr.cfg_gen",
        arg=[],
        kwarg={
            "filename": "salt://templates/jinja_trim_lstrip_test.j2",
            "FB": "ceos1",
        },
        tgt_type="glob",
        timeout=60,
    ) 
    ret_nrp2 = client.cmd(
        tgt="nrp2",
        fun="nr.cfg_gen",
        arg=[],
        kwarg={
            "filename": "salt://templates/jinja_trim_lstrip_test.j2",
            "FB": "*1000*",
        },
        tgt_type="glob",
        timeout=60,
    ) 
    print("ret_nrp1:")
    pprint.pprint(ret_nrp1)
    print("ret_nrp2:")
    pprint.pprint(ret_nrp2)
    assert ret_nrp1 == {'nrp1': {'ceos1': {'salt_cfg_gen': '1\n2\n3\n'}}}, message
    assert ret_nrp2 == {'nrp2': {'csr1000v-1': {'salt_cfg_gen': '\n1\n\n2\n\n3\n'}}}, message
    
   
def test_nr_cg_gen_inline_newline_escape_handling():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg_gen",
        arg=["test\\nstring\\n"],
        kwarg={
            "FB": "ceos1",
        },
        tgt_type="glob",
        timeout=60,
    )     
    pprint.pprint(ret)
    assert ret == {'nrp1': {'ceos1': {'salt_cfg_gen': 'test\\nstring\\n'}}}
    
    
def test_nr_cg_gen_inline_newline_literal_string():
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg_gen",
        arg=['"test\nstring\n"'],
        kwarg={
            "FB": "ceos1",
        },
        tgt_type="glob",
        timeout=60,
    )     
    pprint.pprint(ret)
    assert ret == {'nrp1': {'ceos1': {'salt_cfg_gen': '"test\nstring\n"'}}}
    
    
def test_nr_cfg_gen_job_data_string_path():
    expected = [
        'bgp', 'asn', '65555', 'rid', '1.1.1.1', 'peers',
        'ip', '1.2.3.4', 'asn', '65000', '4.3.2.1', '65123', 
        'ntp', 'servers', '3.3.3.3', '4.4.4.4'        
    ]
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg_gen",
        arg=["{{ job_data }}"],
        kwarg={
            "FB": "ceos1",
            "job_data": "salt://data/params.yaml"
        },
        tgt_type="glob",
        timeout=60,
    )         
    pprint.pprint(ret)
    assert isinstance(ret['nrp1']['ceos1']['salt_cfg_gen'], str)
    assert "Traceback" not in ret['nrp1']['ceos1']['salt_cfg_gen']
    assert all(k in ret['nrp1']['ceos1']['salt_cfg_gen'] for k in expected)
    
    
def test_nr_cfg_gen_job_data_list_of_paths():
    expected = [
        'bgp', 'asn', '65555', 'rid', '1.1.1.1', 'peers',
        'ip', '1.2.3.4', 'asn', '65000', '4.3.2.1', '65123', 
        'ntp', 'servers', '3.3.3.3', '4.4.4.4', '1.2.3.4',
        'facility', 'local', 'bufered_size', '64242'
    ]
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg_gen",
        arg=["{{ job_data }}"],
        kwarg={
            "FB": "ceos1",
            "job_data": ["salt://data/params.yaml", "salt://data/syslog.json"]
        },
        tgt_type="glob",
        timeout=60,
    )         
    pprint.pprint(ret)
    assert isinstance(ret['nrp1']['ceos1']['salt_cfg_gen'], str)
    assert "Traceback" not in ret['nrp1']['ceos1']['salt_cfg_gen']
    assert all(k in ret['nrp1']['ceos1']['salt_cfg_gen'] for k in expected)
    
    
def test_nr_cfg_gen_job_data_dict_of_paths():
    expected = [
        'bgp', 'asn', '65555', 'rid', '1.1.1.1', 'peers',
        'ip', '1.2.3.4', 'asn', '65000', '4.3.2.1', '65123', 
        'ntp', 'servers', '3.3.3.3', '4.4.4.4', '1.2.3.4',
        'facility', 'local', 'bufered_size', '64242', 'foobar', 
        'barfoo'
    ]
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.cfg_gen",
        arg=["{{ job_data }}"],
        kwarg={
            "FB": "ceos1",
            "job_data": {"foobar": "salt://data/params.yaml", "barfoo": "salt://data/syslog.json"}
        },
        tgt_type="glob",
        timeout=60,
    )         
    pprint.pprint(ret)
    assert isinstance(ret['nrp1']['ceos1']['salt_cfg_gen'], str)
    assert "Traceback" not in ret['nrp1']['ceos1']['salt_cfg_gen']
    assert all(k in ret['nrp1']['ceos1']['salt_cfg_gen'] for k in expected)