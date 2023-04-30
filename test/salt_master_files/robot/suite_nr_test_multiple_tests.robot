*** Comments ***
To run this suite:
robot /etc/salt/robot/suite_nr_test_multiple_tests.robot

*** Settings ***
Library    salt_nornir.salt_nornir_robot

*** Test Cases ***
Test suite 1
    Minions    nrp1    
    Hosts      ceos*
    nr.test    suite=salt://tests/test_suite_1.txt
    
Test suite 2
    Minions    nrp1    
    Hosts      FM=arista_eos
    nr.test    suite=salt://tests/test_suite_2.txt
    
Test suite 3
    Minions    nrp1    
    Hosts      *
    nr.test    suite=salt://tests/test_suite_3.txt
    
Test suite 5
    Minions    nrp1    
    Hosts      *
    nr.test    suite=salt://tests/test_suite_5.txt