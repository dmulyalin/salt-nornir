*** Comments ***
To run this suite:
robot -P /etc/salt/robot/ /etc/salt/robot/suite_1.robot

*** Settings ***
Library    salt_nornir.salt_nornir_robot

*** Test Cases ***
Test NTP
    Minions    nrp1    
    Hosts      ceos*
    nr.test    show clock    contains    local
    
Test Software Version
    Minions    nrp1    
    Hosts      FM=arista_eos
    nr.test    show version    contains    7.3.2