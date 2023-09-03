# import salt libs, wrapping it in try/except for docs to generate
import salt.client
import salt.config
import salt.utils.event
import salt.runner
from salt.exceptions import CommandExecutionError

# import pydatic staff
from enum import Enum
from pydantic import (
    BaseModel,
    Field,
    root_validator,
    StrictBool,
    StrictInt,
    StrictStr,
    conlist,
)
from typing import Union, Optional, List, Any, Dict, Callable

# import picle modules
from picle import Cache as PicleCache
from picle.utils import run_print_exception

# import pydantic models
from salt_nornir.pydantic_models import (
    SaltNornirExecutionFunctions,
    SaltNornirStateFunctions,
    SaltNornirRunnerFunctions,
    model_runner_nr_cfg,
    model_runner_nr_diagram,
)


# instantiate salt runner client
opts = salt.config.master_config("/etc/salt/master")
opts["quiet"] = True
salt_runner = salt.runner.RunnerClient(opts)

# instantiate cache object
GLOBAL_CACHE = PicleCache("/var/salt-nornir/master/cache/picle.cache")


class ShowNornirCommandModel(BaseModel):
    version: Callable = Field(
        "show_version", description="Show Nornir Proxy Minions software version"
    )
    minions: Callable = Field("source_minions", description="List Nornir Proxy Minions")

    @staticmethod
    @run_print_exception
    def show_version(minions: list = None):
        minions = minions or GLOBAL_CACHE["minions"]
        ret = salt_runner.cmd(
            "nr.call",
            arg=["nornir", "version"],
            kwarg={"tgt": minions, "tgt_type": "list"},
        )
        for k, v in ret.items():
            print(f"{k}\n{v}\n\n")

    @staticmethod
    @run_print_exception
    def source_minions():
        return "\n".join(GLOBAL_CACHE["minions"])


class ShowCommandModel(BaseModel):
    version: Callable = Field("show_version", description="Show software version")
    nornir: ShowNornirCommandModel = Field(None, description="Nornir show commands")

    @staticmethod
    def show_version():
        return "Salt-Nornir Version 0.20.3"


class SaltNornirShell(BaseModel):
    execution: SaltNornirExecutionFunctions = Field(
        None, description="Salt-Nornir Execution modules"
    )
    state: SaltNornirStateFunctions = Field(
        None, description="Salt-Nornir State modules"
    )
    runner: SaltNornirRunnerFunctions = Field(
        None, description="Salt-Nornir Runner modules"
    )
    show: ShowCommandModel = Field(None, description="Show commands")
    hosts: StrictStr = Field(None, description="Nornir Hosts")

    class PicleConfig:
        subshell = True
        prompt = "salt#"
        intro = "Welcome to Salt-Nornir Interactive Shell."
        methods_override = {"preloop": "cmd_preloop_override"}

    @classmethod
    def cmd_preloop_override(self):
        """This Methos called before CMD loop starts"""
        print("Collecting hosts inventory...")
        hosts = salt_runner.cmd(
            "nr.inventory",
            arg=[],
            kwarg={"job_retry": 0, "job_timeout": 5, "FB": "*", "table": False},
        )
        GLOBAL_CACHE["minions"] = set()
        GLOBAL_CACHE["hosts"] = {}
        for host in hosts:
            GLOBAL_CACHE["minions"].add(host["minion"])
            GLOBAL_CACHE["hosts"][host.pop("host")] = host

    @classmethod
    def source_hosts(self):
        return list(GLOBAL_CACHE["hosts"])
