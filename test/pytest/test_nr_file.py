import logging
import pprint
import pytest
import os

log = logging.getLogger(__name__)

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

def _clean_files():
    _ = client.cmd(
        tgt="nrp1",
        fun="cmd.run",
        arg=["rm -f -r -d /var/salt-nornir/nrp1/files/*"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )
    
def _generate_files():
    _ = client.cmd(
        tgt="nrp1",
        fun="nr.cli",
        arg=["show clock"],
        kwarg={"tf": "clock"},
        tgt_type="glob",
        timeout=60,
    )
    res = client.cmd(
        tgt="nrp1",
        fun="nr.do",
        arg=["interfaces", "facts"],
        kwarg={"tf": True},
        tgt_type="glob",
        timeout=60,
    ) 

def test_nr_file_ls_all():
    _clean_files()
    _generate_files()
    _generate_files()

    # check 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.file",
        arg=["ls"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    assert isinstance(ret["nrp1"], str), "Wrong result type, should be string"
    assert ret["nrp1"].count("clock__") == 4, "Not all files saved"
    assert ret["nrp1"].count("interfaces__") == 4, "Not all files saved"
    assert ret["nrp1"].count("facts__") == 4, "Not all files saved"
    assert "Traceback" not in ret["nrp1"], "Have errors"
    
# test_nr_file_ls_all()


def test_nr_file_ls_filegroup():
    _clean_files()
    _generate_files()
    _generate_files()
    
    # check 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.file",
        arg=["ls"],
        kwarg={"filegroup": "interfaces"},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    assert "clock__" not in ret["nrp1"], "Ls returned clock filegroup"
    assert ret["nrp1"].count("interfaces__") == 4, "Not all files displayed"
    assert "facts__" not in ret["nrp1"], "Ls returned facts filegroup"
    assert "Traceback" not in ret["nrp1"], "Have errors"
    
# test_nr_file_ls_filegroup()


def test_nr_file_ls_filegroup_ceos1_only():
    _clean_files()
    _generate_files()
    
    # check 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.file",
        arg=["ls"],
        kwarg={"filegroup": "interfaces", "FB": "ceos1"},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    assert "clock__" not in ret["nrp1"], "Ls returned clock filegroup"
    assert ret["nrp1"].count("interfaces__") == 1, "Got additonal output"
    assert "facts__" not in ret["nrp1"], "Ls returned facts filegroup"
    assert "Traceback" not in ret["nrp1"], "Have errors"
    
# test_nr_file_ls_filegroup_ceos1_only()


def test_nr_file_read():
    _clean_files()
    _generate_files()
    
    # check 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.file",
        arg=["read"],
        kwarg={"filegroup": "clock"},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    assert "ceos1" in ret["nrp1"], "No data for ceos1"
    assert "ceos2" in ret["nrp1"], "No data for ceos2"    
    assert "show clock" in ret["nrp1"]["ceos1"], "No show clock output for ceos1"
    assert "show clock" in ret["nrp1"]["ceos2"], "No show clock output for ceos2"
    assert "Traceback" not in ret["nrp1"]["ceos1"]["show clock"], "Got errors"
    assert "Traceback" not in ret["nrp1"]["ceos2"]["show clock"], "Got errors"
    
# test_nr_file_read()

def test_nr_file_read_last_2():
    _clean_files()
    _generate_files()
    _generate_files()
    
    # check 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.file",
        arg=["read"],
        kwarg={"filegroup": "clock", "last": 2},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    assert "ceos1" in ret["nrp1"], "No data for ceos1"
    assert "ceos2" in ret["nrp1"], "No data for ceos2"    
    assert "show clock" in ret["nrp1"]["ceos1"], "No show clock output for ceos1"
    assert "show clock" in ret["nrp1"]["ceos2"], "No show clock output for ceos2"
    assert "Traceback" not in ret["nrp1"]["ceos1"]["show clock"], "Got errors"
    assert "Traceback" not in ret["nrp1"]["ceos2"]["show clock"], "Got errors"
    
# test_nr_file_read_last_2()


def test_nr_file_read_no_filegroup_provided():
    _clean_files()
    _generate_files()
    
    # check 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.file",
        arg=["read"],
        kwarg={},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)

    assert "bad filegroup" in ret["nrp1"]["ceos1"]["nornir_salt.plugins.tasks.files"], "No error"
    assert "bad filegroup" in ret["nrp1"]["ceos2"]["nornir_salt.plugins.tasks.files"], "No error"
    
# test_nr_file_read_no_filegroup_provided()


def test_nr_file_read_none_existing_filegroup_provided():
    _clean_files()
    _generate_files()
    
    # check 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.file",
        arg=["read"],
        kwarg={"filegroup": "not_exists"},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)

    assert ret == {'nrp1': {'ceos1': {None: None}, 'ceos2': {None: None}}}
    
# test_nr_file_read_none_existing_filegroup_provided()


def test_nr_file_rm_filegroup_all():
    _clean_files()
    _generate_files()
    _generate_files()
    
    # check 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.file",
        arg=["rm"],
        kwarg={"filegroup": "interfaces"},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)

    assert ret["nrp1"].count("interfaces__") == 4, "Not all files removed"
    assert ret["nrp1"].count("clock__") == 0, "Clock files removed"
    assert ret["nrp1"].count("facts__") == 0, "Facts files removed"
    
# test_nr_file_rm_filegroup_all()


def test_nr_file_rm_all():
    _clean_files()
    _generate_files()
    _generate_files()
    
    # check 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.file",
        arg=["rm"],
        kwarg={"filegroup": True},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)

    assert ret["nrp1"].count("clock__") == 4, "Not all files removed"
    assert ret["nrp1"].count("facts__") == 4, "Not all files removed"
    
# test_nr_file_rm_all()


def test_nr_file_diff_last_1_2():
    _clean_files()
    _generate_files()
    _generate_files()
    
    # check 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.file",
        arg=["diff"],
        kwarg={"filegroup": ["interfaces", "clock"]},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    
    assert ret["nrp1"]["ceos1"]["interfaces"] == True
    assert "/clock__" in ret["nrp1"]["ceos1"]["clock"]
    assert ret["nrp1"]["ceos2"]["interfaces"] == True
    assert "/clock__" in ret["nrp1"]["ceos2"]["clock"]
    
# test_nr_file_diff_last_1_2()


def test_nr_file_diff_last_1_2_ceos2_only():
    _clean_files()
    _generate_files()
    _generate_files()
    
    # check 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.file",
        arg=["diff"],
        kwarg={"filegroup": ["interfaces", "clock"], "FB": "ceos2"},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret)
    
    assert ret["nrp1"]["ceos2"]["interfaces"] == True
    assert "/clock__" in ret["nrp1"]["ceos2"]["clock"]
    assert "ceos1" not in ret["nrp1"]
    
# test_nr_file_diff_last_1_2_ceos2_only()


def test_nr_file_diff_last_2_ceos1():
    _clean_files()
    _generate_files()
    _generate_files()
    
    # check 
    ret = client.cmd(
        tgt="nrp1",
        fun="nr.file",
        arg=["diff"],
        kwarg={"filegroup": ["interfaces", "clock"], "last": 2, "FB": "ceos1"},
        tgt_type="glob",
        timeout=60,
    )
    pprint.pprint(ret)
    
    assert ret["nrp1"]["ceos1"]["interfaces"] == True
    assert "/clock__" in ret["nrp1"]["ceos1"]["clock"]
    
# test_nr_file_diff_last_2_ceos1()


def test_nr_file_diff_last_1_2_and_last_2_3_ceos1():
    _clean_files()
    _generate_files()
    _generate_files()
    _generate_files()
    
    # check 
    ret_1_2 = client.cmd(
        tgt="nrp1",
        fun="nr.file",
        arg=["diff"],
        kwarg={"filegroup": ["interfaces", "clock"], "last": [1, 2], "FB": "ceos1"},
        tgt_type="glob",
        timeout=60,
    )
    ret_2_3 = client.cmd(
        tgt="nrp1",
        fun="nr.file",
        arg=["diff"],
        kwarg={"filegroup": ["interfaces", "clock"], "last": [2, 3], "FB": "ceos1"},
        tgt_type="glob",
        timeout=60,
    )
    # pprint.pprint(ret_1_2)
    # pprint.pprint(ret_2_3)
    
    assert ret_1_2["nrp1"]["ceos1"]["interfaces"] == True
    assert "/clock__" in ret_1_2["nrp1"]["ceos1"]["clock"]
    assert ret_2_3["nrp1"]["ceos1"]["interfaces"] == True
    assert "/clock__" in ret_2_3["nrp1"]["ceos1"]["clock"]
    assert ret_1_2["nrp1"]["ceos1"]["clock"] != ret_2_3["nrp1"]["ceos1"]["clock"]
    
# test_nr_file_diff_last_1_2_and_last_2_3_ceos1()


def test_nr_file_diff_last_1_2_string_ceos1():
    _clean_files()
    _generate_files()
    _generate_files()
    
    # check 
    ret_1_2_list = client.cmd(
        tgt="nrp1",
        fun="nr.file",
        arg=["diff"],
        kwarg={"filegroup": ["interfaces", "clock"], "last": [1, 2], "FB": "ceos1"},
        tgt_type="glob",
        timeout=60,
    )
    ret_1_2_string = client.cmd(
        tgt="nrp1",
        fun="nr.file",
        arg=["diff"],
        kwarg={"filegroup": ["interfaces", "clock"], "last": "1, 2", "FB": "ceos1"},
        tgt_type="glob",
        timeout=60,
    )
    
    assert ret_1_2_list["nrp1"]["ceos1"]["clock"] == ret_1_2_string["nrp1"]["ceos1"]["clock"]
    
# test_nr_file_diff_last_1_2_string_ceos1()