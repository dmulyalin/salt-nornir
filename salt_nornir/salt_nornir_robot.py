"""
Salt Nornir Robot
=================

SaltNornirRobot is a Robot Framework test library to use with
Salt-Nornir.

Robot Framework need to bs installed on Salt Master::

    pip install robotframework
    
Keywords
++++++++

* ``Minions`` - glob patterns of minions to target using Salt local 
    client ``cmd.run`` function, additional parameters can be passed 
    as key-word arguments
* ``Hosts`` - hosts to target, supports ``Fx`` filters as key-word
    arguments, by default expects a list of glob patterns to use with 
    ``FB` filter
* ``nr.test`` - run Salt-Nornir ``nr.test`` execution function with 
    provided arguments and key-word arguments
* ``nr.cli`` - run Salt-Nornir ``nr.cli`` execution function with 
    provided arguments and key-word arguments, returns result for 
    first host first command only, does not support multiple commands 
    or hosts targeting
    
Examples
++++++++

This test suite runs two tests using ``nr.test``::

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
    
Run test suite from Salt Master using ``robot`` command line tool::

    robot /path/to/salt_nornir_robot_suite.robot
    
This test suite runs two tests using ``nr.cli``::

    *** Settings ***
    Library    salt_nornir.salt_nornir_robot
    
    *** Test Cases ***
    Test NTP ceos1
        Minions           nrp1    
        Hosts             ceos1
        ${result} =       nr.cli    show clock
        Should Contain    ${result}   NTP
    
    Test NTP ceos2
        Minions           nrp1    
        Hosts             ceos2
        ${result} =       nr.cli    show clock
        Should Contain    ${result}   local
        
To run nr.test tests suite::

    *** Settings ***
    Library    salt_nornir.salt_nornir_robot
    
    *** Test Cases ***
    Run Test suite 1
        Minions    nrp1    
        Hosts      ceos*
        nr.test    suite=salt://tests/test_suite_1.txt
        
    Run Test suite 2
        Minions    nrp1    
        Hosts      FM=arista_eos
        nr.test    suite=salt://tests/test_suite_2.txt
"""
import logging
import pprint
from robot.api import logger

log = logging.getLogger(__name__)

# Import salt modules
try:
    import salt.client
    from salt.exceptions import CommandExecutionError

    HAS_SALT = True
except:
    log.error("Nornir Runner Module - failed importing SALT libraries")
    HAS_SALT = False

try:
    from robot.api.deco import keyword
    from robot.api import ContinuableFailure, FatalError, Error

    HAS_ROBOT = True
except:
    log.error("SaltNornirRobot - failed importing ROBOT libraries")
    HAS_ROBOT = False

try:
    from nornir_salt.plugins.functions import TabulateFormatter

    HAS_NORNIR = True
except ImportError:
    log.error("SaltNornirRobot - failed importing Nornir-Salt libraries")
    HAS_NORNIR = False


# ROBOT framework parameters
ROBOT_LIBRARY_SCOPE = "SUITE"
ROBOT_AUTO_KEYWORDS = False
__version__ = "0.1"


# Global vars
DATA = {}


if HAS_SALT:
    # initiate local client to run execution module commands 'salt "*" ...'
    client = salt.client.LocalClient()


def clean_global_data():
    global DATA
    DATA.clear()


@keyword("Hosts")
def hosts(*args, **kwargs):
    """Collect hosts to target"""
    DATA["hosts"] = {"FB": ", ".join(args) if args else "*", **kwargs}


@keyword("Minions")
def minions(*args, **kwargs):
    """Collect minions to target"""
    DATA["minions"] = {
        "tgt": args[0] if len(args) == 1 else args,
        "tgt_type": "glob",
        **kwargs,
    }


@keyword("nr.test")
def nr_test(*args, **kwargs):
    """Run Salt-Nornir nr.test execution function"""
    logger.info(
        f"Running nr.test with args '{args}', kwargs '{kwargs}', global DATA '{DATA}'"
    )
    has_errors = False
    # run this function
    ret = client.cmd(
        **DATA["minions"],
        fun="nr.test",
        arg=args,
        kwarg={
            **DATA.get("hosts", {}),
            "remove_tasks": False,
            **kwargs,
            "add_details": True,
        },
    )
    # iterate over results and log tests statuses
    for minion, minion_results in ret.items():
        for result in minion_results:
            host = result["host"]
            # evaluate and log test result
            if "success" in result:
                if (
                    result["failed"]
                    or result["exception"]
                    or not result["success"]
                    or "traceback" in str(result["result"]).lower()
                ):
                    has_errors = True
                    logger.error(
                        (
                            f'{minion} minion, {host} test "{result["name"]}" - '
                            f'<span style="background-color: #CE3E01">failure: "{result["exception"]}"</span>'
                        ),
                        html=True,
                    )
                else:
                    logger.info(
                        (
                            f'{minion} minion, {host} test "{result["name"]}" - '
                            f'<span style="background-color: #97BD61">success</span>'
                        ),
                        html=True,
                    )
    # clea global state to prep for next test
    clean_global_data()

    # transform results into HTML tables
    tests_results = [
        {"minion": minion, **result}
        for minion, results in ret.items()
        for result in results
        if "success" in result
    ]
    commands_output = [
        {"minion": minion, **result}
        for minion, results in ret.items()
        for result in results
        if "success" not in result
    ]
    tests_results_html_table = TabulateFormatter(
        tests_results,
        tabulate={"tablefmt": "html"},
        headers=[
            "minion",
            "host",
            "name",
            "result",
            "failed",
            "task",
            "test",
            "criteria",
            "exception",
        ],
    )
    commands_output_html_table = TabulateFormatter(
        commands_output,
        tabulate={"tablefmt": "html"},
        headers=[
            "minion",
            "host",
            "name",
            "result",
            "exception",
        ],
    )
    ret = (
        f"<h3>Test Suite Results</h3>"
        f"<details><summary>...</summary><p>{tests_results_html_table}</p></details>"
        f"<h3>Collected Devices Output</h3>"
        f"<details><summary>...</summary><p>{commands_output_html_table}</p></details>"
    )
    logger.info(ret, html=True)

    # raise if has errors
    if has_errors:
        raise ContinuableFailure("Tests failed")
    # return ret with no errors in structured format
    return ret


@keyword("nr.cli")
def nr_cli(*args, **kwargs):
    """Run Salt-Nornir nr.cli execution function"""
    log.info(
        f"Running nr.cli with args '{args}', kwargs '{kwargs}', global DATA '{DATA}'"
    )
    has_errors = False
    # run this function
    ret = client.cmd(
        **DATA["minions"],
        fun="nr.cli",
        arg=args,
        kwarg={
            **DATA.get("hosts", {}),
            **kwargs,
            "to_dict": False,
            "add_details": True,
        },
    )
    # extract results for the host
    for minion_name, minion_results in ret.items():
        result = minion_results[0]
        if (
            result["failed"]
            or result["exception"]
            or "traceback" in str(result["result"]).lower()
        ):
            has_errors = True
            log.error(
                f"{minion_name} minion, {result['host']} cli command '{result['name']}' failed"
            )
    # clean global state to prep for next test
    clean_global_data()
    # raise exception if cli command failed
    if has_errors:
        raise ContinuableFailure(result)
    # return ret with no errors in structured format
    return result["result"]
