*** Comments ***
To run this suite:
robot -P /etc/salt/robot/ /etc/salt/robot/suite_2.robot

*** Settings ***
Library    salt_nornir.salt_nornir_robot

*** Test Cases ***
Test NTP ceos1
    Minions           nrp1    
    Hosts             ceos1
    ${result} =       nr.cli    show clock
    Should Contain    ${result['nrp1'][0]['result']}   NTP

Test NTP ceos2
    Minions           nrp1    
    Hosts             ceos2
    ${result} =       nr.cli    show clock
    Should Contain    ${result['nrp1'][0]['result']}   local