*** Comments ***
To run this suite:
robot /etc/salt/robot/workflow_nr_cfg_test_1.robot

*** Settings ***
Library    salt_nornir.salt_nornir_robot

*** Test Cases ***
Change 1
    Minions    nrp1    
    Hosts      ceos*
    nr.cfg     config=salt://templates/ntp_configs.txt    plugin=netmiko
    
Change 2
    Minions    nrp1    
    Hosts      FM=arista_eos
    nr.cfg     commands="logging host 1.2.3.4"    plugin=netmiko
