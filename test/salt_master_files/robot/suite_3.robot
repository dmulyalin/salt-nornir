*** Comments ***
To run this suite:
robot -P /etc/salt/robot/ /etc/salt/robot/suite_3.robot

*** Settings ***
Library    salt_nornir.salt_nornir_robot

*** Test Cases ***
Test with comma in pattern
    Minions           nrp1    
    Hosts             *
    nr.test           suite=salt://tests/test_suite_with_commas_in_pattern.txt
