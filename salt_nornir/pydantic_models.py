"""
File to contain pydantic models for Salt-Nornir modules functions
"""
import logging
import os

log = logging.getLogger(__name__)

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
from nornir_salt.utils.pydantic_models import FilesCallsEnum, model_ffun_fx_filters
from nornir_salt.plugins.functions import FFun_functions  # list of Fx names


# ---------------------------------------------------------------
# Execution Module Function Models
# ---------------------------------------------------------------


class EnumExecTableTypes(str, Enum):
    table_brief = "brief"
    table_terse = "terse"
    table_extend = "extend"


class EnumExecTTPStructTypes(str, Enum):
    ttp_res_struct_list = "list"
    ttp_res_struct_dict = "dictionary"
    ttp_res_struct_flat_list = "flat_list"


class ModelExecCommonArgs(model_ffun_fx_filters):
    render: Optional[Union[List[StrictStr], StrictStr]] = None
    context: Optional[Dict] = None
    dcache: Optional[Union[StrictStr, StrictBool]] = None
    defaults: Optional[Dict] = None
    diff: Optional[StrictStr] = None
    dp: Optional[Union[StrictStr, List[Union[StrictStr, Dict]]]] = None
    download: Optional[List[StrictStr]] = None
    dump: Optional[StrictStr] = None
    event_failed: Optional[StrictBool] = None
    event_progress: Optional[StrictBool] = None
    hcache: Optional[Union[StrictStr, StrictBool]] = None
    iplkp: Optional[StrictStr] = None
    jmespath: Optional[StrictStr] = None
    match: Optional[StrictStr] = None
    before: Optional[StrictInt] = None
    ntfsm: Optional[StrictBool] = None
    run_connect_retry: Optional[StrictInt] = None
    run_task_retry: Optional[StrictInt] = None
    run_creds_retry: Optional[List[Union[StrictStr, Dict]]] = None
    run_num_workers: Optional[StrictInt] = None
    run_num_connectors: Optional[StrictInt] = None
    run_reconnect_on_fail: Optional[StrictBool] = None
    render: Optional[Union[List[StrictStr], StrictStr]] = None
    run_ttp: Optional[StrictStr] = None
    ttp_structure: Optional[EnumExecTTPStructTypes] = "flat_list"
    table: Optional[Union[EnumExecTableTypes, Dict, StrictBool]] = "brief"
    headers: Optional[Union[StrictStr, List[StrictStr]]] = None
    headers_exclude: Optional[Union[StrictStr, List[StrictStr]]] = None
    sortby: Optional[StrictStr] = None
    reverse: Optional[StrictBool] = None
    tests: Optional[
        Union[List[List[StrictStr]], List[Dict], Dict[StrictStr, List[Dict]]]
    ] = None
    failed_only: Optional[StrictBool] = None
    remove_tasks: Optional[StrictBool] = None
    tf: Optional[StrictStr] = None
    tf_skip_failed: Optional[StrictBool] = None
    to_dict: Optional[StrictBool] = None
    add_details: Optional[StrictBool] = None
    xml_flake: Optional[StrictStr] = None
    xpath: Optional[StrictStr] = None
    worker: Optional[Union[StrictInt, StrictStr]] = None
    job_data: Optional[Union[StrictStr, List, Dict]] = None


class EnumExecNrCliPlugins(str, Enum):
    plugin_netmiko = "netmiko"
    plugin_scrapli = "scrapli"
    plugin_napalm = "napalm"
    plugin_pyats = "pyats"


class model_exec_nr_cli(ModelExecCommonArgs):
    """Model for salt_nornir.modules.nornir_proxy_execution_module.cli function arguments"""

    args: Optional[Union[List[StrictStr], StrictStr]] = Field(
        None, description="CLI arguments list"
    )
    commands: Optional[Union[List[StrictStr], StrictStr]] = Field(
        None, description="Show commands to collect from devices"
    )
    plugin: Optional[EnumExecNrCliPlugins] = Field(
        "netmiko", description="Connection plugin to use"
    )
    filename: Optional[StrictStr] = Field(
        "netmiko", description="URL to file with multiline commands string"
    )

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"

    @staticmethod
    def run(*args, **kwargs):
        return salt_runner.cmd("nr.call", arg=["cli"], kwarg=kwargs)

    @staticmethod
    def source_filename():
        try:
            return os.listdir("/etc/salt/cli/")
        except FileNotFoundError:
            return [
                "Cannot source filenames chaoices, OS path '/etc/salt/cli/' does not exists"
            ]

    @root_validator(pre=True)
    def check_commands_given(cls, values):
        assert (
            values.get("args")
            or values.get("commands")
            or values.get("filename")
            # ttp template's inputs contains cli commands
            or values.get("run_ttp")
            # TestsProcessor adds cli commands from tests
            or values.get("tests")
        ), "No CLI commands, filename, run_ttp or tests to run provided"
        return values


class model_exec_nr_task(ModelExecCommonArgs):
    """Model for salt_nornir.modules.nornir_proxy_execution_module.task function arguments"""

    plugin: StrictStr

    class Config:
        extra = "allow"


class EnumExecNrCfgPlugins(str, Enum):
    plugin_netmiko = "netmiko"
    plugin_scrapli = "scrapli"
    plugin_napalm = "napalm"
    plugin_pyats = "pyats"


class model_exec_nr_cfg(ModelExecCommonArgs):
    """Model for salt_nornir.modules.nornir_proxy_execution_module.cfg function arguments"""

    args: Optional[List[Union[StrictStr]]] = None
    commands: Optional[Union[List[StrictStr], StrictStr]] = None
    plugin: Optional[EnumExecNrCfgPlugins] = "netmiko"
    filename: Optional[StrictStr] = None
    config: Optional[Union[Dict, StrictStr]] = None

    class Config:
        extra = "allow"

    @root_validator(pre=True)
    def check_commands_given(cls, values):
        assert (
            values.get("args")
            or values.get("commands")
            or values.get("filename")
            or values.get("config")
        ), "No CLI commands, filename or config provided"
        return values


class model_exec_nr_tping(ModelExecCommonArgs):
    """Model for salt_nornir.modules.nornir_proxy_execution_module.tping function arguments"""

    ports: Optional[Union[List[StrictInt], StrictInt]] = None
    timeout: Optional[StrictInt] = None
    host: Optional[StrictStr] = None

    class Config:
        extra = "allow"


class model_exec_nr_test(BaseModel):
    name: Optional[StrictStr] = None
    test: Optional[StrictStr] = None
    pattern: Optional[StrictStr] = None
    function_file: Optional[StrictStr] = None
    saltenv: Optional[StrictStr] = None
    suite: Optional[Union[StrictStr, List[Dict[StrictStr, Any]]]] = None
    subset: Optional[Union[StrictStr, List[StrictStr]]] = None
    dump: Optional[StrictStr] = None
    commands: Optional[Union[StrictStr, List[StrictStr]]] = None
    plugin: Optional[EnumExecNrCliPlugins] = None
    use_ps: Optional[StrictBool] = None
    cli: Optional[
        Dict
    ] = None  # if reference model_exec_nr_cli here it fails as test's cli might not contain commands and its normal
    failed_only: Optional[StrictBool] = None
    remove_tasks: Optional[StrictBool] = None
    table: Optional[Union[EnumExecTableTypes, Dict, StrictBool]] = "brief"
    headers: Optional[Union[StrictStr, List[StrictStr]]] = None
    sortby: Optional[StrictStr] = None
    reverse: Optional[StrictBool] = None
    tests: Optional[Union[StrictStr, List[StrictStr]]] = None
    worker: Optional[StrictInt] = None

    class Config:
        extra = "allow"


class EnumExecNrNcPlugins(str, Enum):
    plugin_netmiko = "ncclient"
    plugin_scrapli = "scrapli"


class model_exec_nr_nc(ModelExecCommonArgs):
    """Model for salt_nornir.modules.nornir_proxy_execution_module.nc function arguments"""

    args: Optional[List[Union[StrictStr]]] = None
    plugin: Optional[EnumExecNrNcPlugins] = "ncclient"
    call: Optional[StrictStr] = None
    data: Optional[StrictStr] = None
    method_name: Optional[StrictStr] = None
    source: Optional[StrictStr] = None
    target: Optional[StrictStr] = None
    config: Optional[StrictStr] = None
    ncclient_filter: Optional[Union[List[StrictStr], StrictStr]] = Field(
        None, alias="filter"
    )
    scrapli_filter: Optional[StrictStr] = Field(None, alias="filter_")

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"

    @root_validator(pre=True)
    def check_params_given(cls, values):
        assert values.get("args") or values.get(
            "call"
        ), "No NETCONF method to call provided."
        return values


class EnumExecNrHTTPMethods(str, Enum):
    get = "get"
    post = "post"
    put = "put"
    delete = "delete"
    head = "head"
    patch = "patch"


class model_exec_nr_http(ModelExecCommonArgs):
    """Model for salt_nornir.modules.nornir_proxy_execution_module.http function arguments"""

    args: Optional[List[StrictStr]] = None
    method: Optional[EnumExecNrHTTPMethods] = None
    url: Optional[StrictStr] = None

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"

    @root_validator(pre=True)
    def check_params_given(cls, values):
        assert values.get("args") or values.get(
            "method"
        ), "No NETCONF method to call provided."
        if values.get("args"):
            assert hasattr(
                EnumExecNrHTTPMethods, values["args"][0]
            ), "Unsupported HTTP method"
        return values


class model_exec_nr_do_action_step(BaseModel):
    """Model to validate single nr.do action item"""

    function: StrictStr
    args: Optional[List] = None
    kwargs: Optional[Dict] = None
    description: Optional[StrictStr] = None

    class Config:
        extra = "allow"


class model_exec_nr_do_action(BaseModel):
    """Model to validate list of nr.do action items"""

    action: List[model_exec_nr_do_action_step]

    class Config:
        extra = "forbid"


class model_exec_nr_do(BaseModel):
    """Model for salt_nornir.modules.nornir_proxy_execution_module.do function arguments"""

    args: List[StrictStr]
    stop_on_error: Optional[StrictBool] = None
    filepath: Optional[StrictStr] = None
    default_renderer: Optional[StrictStr] = None
    describe: Optional[StrictBool] = None
    tf: Optional[StrictBool] = None
    diff: Optional[StrictBool] = None

    class Config:
        extra = "allow"


class model_exec_nr_file(ModelExecCommonArgs):
    """Model for salt_nornir.modules.nornir_proxy_execution_module.file function arguments"""

    args: Optional[List[StrictStr]] = None
    call: Optional[FilesCallsEnum] = None
    filegroup: Optional[Union[StrictStr, List[StrictStr], StrictBool]] = None
    last: Optional[Union[StrictInt, List[StrictInt], StrictStr]] = None

    class Config:
        extra = "allow"

    @root_validator(pre=True)
    def check_params_given(cls, values):
        if not (values.get("args") or values.get("call")):
            raise CommandExecutionError("No file call method provided")
        if values.get("args") and not any(
            values["args"][0] == i.value for i in FilesCallsEnum
        ):
            raise CommandExecutionError(
                "Unsupported file method '{}', supported {}".format(
                    values["args"][0], ", ".join([i.value for i in FilesCallsEnum])
                )
            )
        return values


class EnumLearnSupportedFun(str, Enum):
    cli = "cli"
    do = "do"
    nc = "nc"
    http = "http"


class model_exec_nr_learn(ModelExecCommonArgs):
    """Model for salt_nornir.modules.nornir_proxy_execution_module.learn function arguments"""

    args: List[StrictStr]
    fun: Optional[EnumLearnSupportedFun] = None
    tf: Optional[Union[StrictStr, StrictBool]] = None
    tf_skip_failed: Optional[StrictBool] = None

    class Config:
        extra = "allow"

    @root_validator(pre=True)
    def check_params_given(cls, values):
        if values.get("fun", "do") != "do":
            if "tf" not in values:
                raise CommandExecutionError(
                    f"No 'tf' argument provided for '{values['fun']}' function"
                )
        return values


class model_exec_nr_find(model_ffun_fx_filters):
    """Model for salt_nornir.modules.nornir_proxy_execution_module.find function arguments"""

    args: List[StrictStr]
    table: Optional[Union[EnumExecTableTypes, Dict, StrictBool]] = "brief"
    headers: Optional[Union[StrictStr, List[StrictStr]]] = None
    headers_exclude: Optional[Union[StrictStr, List[StrictStr]]] = None
    sortby: Optional[StrictStr] = None
    reverse: Optional[StrictBool] = None
    last: Optional[Union[StrictInt, List[StrictInt], StrictStr]] = None

    class Config:
        extra = "allow"

    @root_validator(pre=True)
    def check_params_given(cls, values):
        if not values.get("args"):
            raise CommandExecutionError("No 'args' provided to source filegroup name")
        return values


class model_exec_nr_diff(model_ffun_fx_filters):
    """Model for salt_nornir.modules.nornir_proxy_execution_module.find function arguments"""

    args: Optional[List[StrictStr]] = None
    diff: Optional[List[StrictStr]] = None
    last: Optional[Union[StrictInt, List[StrictInt], StrictStr]] = None

    class Config:
        extra = "allow"

    @root_validator(pre=True)
    def check_params_given(cls, values):
        if not (values.get("args") or values.get("diff")):
            raise CommandExecutionError(
                "No 'args' or 'diff' argument provided to source filegroup name"
            )
        return values


class EnumNrFun(str, Enum):
    fun_hosts = "hosts"
    fun_stats = "stats"
    fun_dir = "dir"
    fun_test = "test"
    fun_inventory = "inventory"
    fun_version = "version"
    fun_shutdown = "shutdown"
    fun_initialized = "initialized"
    fun_kill = "kill"
    fun_refresh = "refresh"
    fun_connections = "connections"
    fun_disconnect = "disconnect"
    fun_connect = "connect"
    fun_clear_hcache = "clear_hcache"
    fun_clear_dcache = "clear_dcache"
    fun_workers = "workers"
    fun_worker = "worker"
    fun_results_queue_dump = "results_queue_dump"


class model_exec_nr_nornir_fun(model_ffun_fx_filters):
    """Model for salt_nornir.modules.nornir_proxy_execution_module.nornir_fun function arguments"""

    args: Optional[List[StrictStr]] = None
    fun: Optional[EnumNrFun] = None
    worker: Optional[Union[StrictInt, StrictStr]] = None
    workers_only: Optional[StrictBool] = None
    stat: Optional[StrictStr] = None

    class Config:
        extra = "allow"

    @root_validator(pre=True)
    def check_params_given(cls, values):
        fun = values.get("fun")
        if not fun:
            raise CommandExecutionError("No 'fun' argument provided")
        if not any(fun == i.value for i in EnumNrFun):
            raise CommandExecutionError(
                "Unsupported function '{}', supported {}".format(
                    fun, ", ".join([i.value for i in EnumNrFun])
                )
            )
        return values


class EnumGnmiPlugins(str, Enum):
    pygnmi = "pygnmi"


class model_exec_nr_gnmi(ModelExecCommonArgs):
    """Model for salt_nornir.modules.nornir_proxy_execution_module.gnmi function arguments"""

    args: Optional[List[StrictStr]] = None
    call: Optional[StrictStr] = None
    plugin: Optional[EnumGnmiPlugins] = None
    method_name: Optional[StrictStr] = None
    path: Optional[Union[StrictStr, List[StrictStr]]] = None
    filename: Optional[StrictStr] = None

    class Config:
        extra = "allow"

    @root_validator(pre=True)
    def check_params_given(cls, values):
        call = values.get("call")
        if not call:
            raise CommandExecutionError("No 'call' argument provided")
        if call == "help" and "method_name" not in values:
            raise CommandExecutionError("'help' need 'method_name' argument")
        return values


class NrSNMPPlugins(str, Enum):
    puresnmp = "puresnmp"


class model_exec_nr_snmp(ModelExecCommonArgs):
    """Model for salt_nornir.modules.nornir_proxy_execution_module.snmp function arguments"""

    call: StrictStr
    oid: Optional[StrictStr] = None
    oids: Optional[List[StrictStr]] = None
    mappings: Optional[Dict[StrictStr, Any]] = None
    value: Optional[Union[StrictStr]] = None
    plugin: Optional[NrSNMPPlugins] = None
    bulk_size: Optional[StrictInt] = None
    scalar_oids: Optional[List[StrictStr]] = None
    repeating_oids: Optional[List[StrictStr]] = None
    method_name: Optional[StrictStr] = None

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"

    @root_validator(pre=True)
    def check_params_given(cls, values):
        call = values.get("call")
        if not call:
            raise CommandExecutionError("No 'call' argument provided")
        if call == "help" and "method_name" not in values:
            raise CommandExecutionError("'help' requires 'method_name' argument")
        # check plugin specific arguments presence
        if values.get("plugin", "puresnmp") == "puresnmp":
            if call == "multiset":
                assert (
                    "mappings" in values
                ), "Method 'multiset' requires 'mappings' argument"
            elif call in ["get", "getnext", "walk", "table", "bulktable", "set"]:
                assert "oid" in values, f"Method '{call}' requires 'oid' argument"
            elif call in ["multiget", "multiwalk", "bulkwalk"]:
                assert "oids" in values, f"Method '{call}' requires 'oids' argument"
        return values


class EnumNrNetwork(str, Enum):
    resolve_dns = "resolve_dns"
    ping = "ping"


class model_exec_nr_network(ModelExecCommonArgs):
    """Model for salt_nornir.modules.nornir_proxy_execution_module.network function arguments"""

    fun: EnumNrNetwork
    args: Optional[List[StrictStr]] = None

    class Config:
        extra = "allow"

    @root_validator(pre=True)
    def check_params_given(cls, values):
        fun = values.get("fun")
        if not fun:
            raise CommandExecutionError("No 'fun' argument provided")
        if not any(fun == i.value for i in EnumNrNetwork):
            raise CommandExecutionError(
                "Unsupported function '{}', supported {}".format(
                    fun, ", ".join([i.value for i in EnumNrNetwork])
                )
            )
        return values


class EnumNrNetboxTasks(str, Enum):
    dir_ = "dir"
    query = "query"
    get_interfaces = "get_interfaces"
    get_connections = "get_connections"
    get_circuits = "get_circuits"
    update_config_context = "update_config_context"
    update_vrf = "update_vrf"
    parse_config = "parse_config"
    rest = "rest"


class model_exec_nr_netbox(model_ffun_fx_filters):
    """Model for salt_nornir.modules.nornir_proxy_execution_module.netbox function arguments"""

    args: Optional[List[StrictStr]] = None
    task: Optional[EnumNrNetboxTasks] = None
    field: Optional[StrictStr] = None
    filters: Optional[Dict[StrictStr, StrictStr]] = None
    fields: Optional[List[StrictStr]] = None
    add_ip: Optional[StrictBool] = None
    add_inventory_items: Optional[StrictBool] = None
    queries: Optional[Dict] = None
    query_string: Optional[StrictStr] = None
    sync: Optional[StrictBool] = None
    hosts: Optional[List[StrictStr]] = None
    cache: Optional[Union[StrictBool, StrictStr]] = None
    cache_ttl: Optional[StrictInt] = None

    class Config:
        extra = "allow"

    @root_validator(pre=True)
    def check_params_given(cls, values):
        task_name = values["args"][0] if values.get("args") else values.get("task")
        if not task_name:
            raise CommandExecutionError(
                "No arguments or 'task' argument provided to source task name"
            )
        if not any(task_name == i.value for i in EnumNrNetboxTasks):
            raise CommandExecutionError(
                "Unsupported task '{}', supported {}".format(
                    task_name, ", ".join([i.value for i in EnumNrNetboxTasks])
                )
            )
        return values


class StateWorkflowOptions(BaseModel):
    fail_if_any_host_fail_any_step: Optional[List[StrictStr]] = None
    fail_if_any_host_fail_all_step: Optional[List[StrictStr]] = None
    fail_if_all_host_fail_any_step: Optional[List[StrictStr]] = None
    fail_if_all_host_fail_all_step: Optional[List[StrictStr]] = None
    report_all: Optional[StrictBool] = None
    filters: Optional[model_ffun_fx_filters] = None
    hcache: Optional[StrictBool] = None
    dcache: Optional[StrictBool] = None
    sumtable: Optional[Union[StrictBool, StrictStr]] = None
    kwargs: Optional[Dict] = None

    class Config:
        extra = "forbid"


class StateWorkflowStep(BaseModel):
    name: StrictStr
    function: StrictStr
    kwargs: Optional[Dict] = None
    args: Optional[List] = None
    report: Optional[StrictBool] = None
    run_if_fail_any: Optional[List[StrictStr]] = None
    run_if_pass_any: Optional[List[StrictStr]] = None
    run_if_fail_all: Optional[List[StrictStr]] = None
    run_if_pass_all: Optional[List[StrictStr]] = None
    stop_if_fail: Optional[StrictBool] = None

    class Config:
        extra = "forbid"


class model_state_nr_workflow(BaseModel):
    """Model for salt_nornir.states.nornir_proxy_state_module.workflow function arguments"""

    state_name: StrictStr
    options: StateWorkflowOptions
    steps: Dict[StrictStr, List[StateWorkflowStep]]

    class Config:
        extra = "forbid"


class model_runner_nr_inventory(model_ffun_fx_filters):
    """Model for salt_nornir.states.nornir_proxy_runner_module.inventory function arguments"""

    args: Optional[List[StrictStr]] = None
    tgt: Optional[StrictStr] = None
    tgt_type: Optional[StrictStr] = None
    verbose: Optional[StrictBool] = None
    job_retry: Optional[StrictInt] = None
    job_timeout: Optional[StrictInt] = None
    table: Optional[Union[StrictStr, StrictBool, Dict]] = None
    headers: Optional[List[StrictStr]] = None
    reverse: Optional[StrictBool] = None
    sortby: Optional[StrictStr] = None
    tree: Optional[StrictBool] = None
    list_proxy: Optional[StrictBool] = None

    class Config:
        extra = "forbid"

    @root_validator(pre=True)
    def check_params_given(cls, values):
        if not (
            values.get("args")
            or any(F in values for F in FFun_functions)
            or values.get("list_proxy")
        ):
            raise CommandExecutionError("No host filter provided")
        return values


class RunnerProgressTypes(str, Enum):
    bars = "bars"
    raw = "raw"
    log = "log"
    tree = "tree"


class RunnerRetStructTypes(str, Enum):
    struct_dict = "dictionary"
    struct_list = "list"


class model_runner_nr_call(model_ffun_fx_filters):
    """Model for salt_nornir.states.nornir_proxy_runner_module.call function arguments"""

    args: Optional[List[StrictStr]] = None
    fun: Optional[StrictStr] = None
    tgt: Optional[Union[StrictStr, List[StrictStr]]] = None
    tgt_type: Optional[StrictStr] = None
    job_retry: Optional[StrictInt] = None
    job_timeout: Optional[StrictInt] = None
    progress: Optional[Union[RunnerProgressTypes, StrictBool]] = None
    ret_struct: Optional[RunnerRetStructTypes] = None

    class Config:
        extra = "allow"

    @root_validator(pre=True)
    def check_params_given(cls, values):
        if not values.get("args") and "fun" not in values:
            raise CommandExecutionError("No execution function name provided")
        return values


class model_runner_nr_event(BaseModel):
    """Model for salt_nornir.states.nornir_proxy_runner_module.event function arguments"""

    tag: Optional[StrictStr] = None
    jid: Optional[Union[StrictStr, StrictInt]] = None
    stop_signal: Optional[Any] = None
    progress: Optional[Union[RunnerProgressTypes, StrictBool]] = None

    class Config:
        extra = "forbid"


class model_runner_nr_cfg(ModelExecCommonArgs):
    """Model for salt_nornir.states.nornir_proxy_runner_module.call function arguments"""

    host_batch: Optional[StrictInt] = None
    first_batch: Optional[StrictInt] = None
    fromdir: Optional[StrictStr] = None
    fromdict: Optional[Dict[StrictStr, StrictStr]] = None
    tgt: Optional[StrictStr] = None
    tgt_type: Optional[StrictStr] = None
    job_retry: Optional[StrictInt] = None
    job_timeout: Optional[StrictInt] = None
    progress: Optional[Union[RunnerProgressTypes, StrictBool]] = None
    saltenv: Optional[StrictStr] = None
    ret_struct: Optional[RunnerRetStructTypes] = None
    interactive: Optional[StrictBool] = None
    dry_run: Optional[StrictBool] = None
    plugin: Optional[EnumExecNrCfgPlugins] = "netmiko"

    class Config:
        extra = "allow"

    @root_validator(pre=True)
    def check_params_given(cls, values):
        if not any(i in values for i in ["fromdir", "fromdict"]):
            raise CommandExecutionError(
                "nr.cfg runner need 'fromdict' or 'fromdir' argument"
            )
        return values


class SaltNornirProxyType(str, Enum):
    nornir = "nornir"


class SaltNornirProxyMemAction(str, Enum):
    log = "log"
    restart = "restart"


class model_nornir_config_proxy(BaseModel):
    """Model for Salt-Nornir Proxy Minion configuration proxy attributes"""

    proxytype: SaltNornirProxyType
    process_count_max: Optional[StrictInt] = 3
    multiprocessing: Optional[StrictBool] = True
    nornir_filter_required: Optional[StrictBool] = False
    connections_idle_timeout: Optional[StrictInt] = 1
    watchdog_interval: Optional[StrictInt] = 30
    child_process_max_age: Optional[StrictInt] = 660
    job_wait_timeout: Optional[StrictInt] = 600
    memory_threshold_mbyte: Optional[StrictInt] = 300
    memory_threshold_action: Optional[SaltNornirProxyMemAction] = "log"
    files_base_path: Optional[StrictStr] = "/var/salt-nornir/{proxy_id}/files/"
    files_max_count: Optional[StrictInt] = 5
    event_progress_all: Optional[StrictBool] = False
    nr_cli: Optional[Dict] = {}
    nr_cfg: Optional[Dict] = {}
    nr_nc: Optional[Dict] = {}
    runner: Optional[Dict] = {}
    inventory: Optional[Dict] = {}

    class Config:
        extra = "allow"


class EnumN2GDataPlugins(str, Enum):
    L2 = "L2"
    IP = "IP"
    L3 = "L3"
    OSPF = "OSPF"
    ISIS = "ISIS"


class EnumN2GDiagramPlugins(str, Enum):
    yed = "yed"
    drawio = "drawio"
    v3d = "v3d"


class model_runner_nr_diagram(model_ffun_fx_filters):
    """Model for salt_nornir.states.nornir_proxy_runner_module.diagramm function arguments"""

    args: Optional[List[StrictStr]] = None
    data_plugin: Optional[EnumN2GDataPlugins] = None
    diagram_plugin: Optional[EnumN2GDiagramPlugins] = None
    tgt: Optional[StrictStr] = None
    tgt_type: Optional[StrictStr] = None
    job_retry: Optional[StrictInt] = None
    job_timeout: Optional[StrictInt] = None
    progress: Optional[Union[RunnerProgressTypes, StrictBool]] = None
    save_data: Optional[Union[StrictBool, StrictStr]] = None
    outfile: Optional[StrictStr] = None
    cli: Optional[Dict[StrictStr, Any]] = None
    filegroup: Optional[StrictStr] = None
    last: Optional[StrictInt] = None

    class Config:
        extra = "allow"

    @root_validator(pre=True)
    def check_params_given(cls, values):
        data_plugin = (
            values["args"][0]
            if len(values.get("args", [])) >= 1
            else values.get("data_plugin")
        )
        diagram_plugin = (
            values["args"][1]
            if len(values["args"]) == 2
            else values.pop("diagram_plugin", "yed")
        )
        if not data_plugin:
            raise CommandExecutionError("No data plugin name provided")
        if not any(data_plugin == i.value for i in EnumN2GDataPlugins):
            raise CommandExecutionError(
                "Unsupported N2G data plugin '{}', supported {}".format(
                    data_plugin, ", ".join([i.value for i in EnumN2GDataPlugins])
                )
            )
        if not any(diagram_plugin == i.value for i in EnumN2GDiagramPlugins):
            raise CommandExecutionError(
                "Unsupported N2G diagram plugin '{}', supported {}".format(
                    diagram_plugin, ", ".join([i.value for i in EnumN2GDiagramPlugins])
                )
            )
        return values


class model_nornir_config(BaseModel):
    """Model for Salt-Nornir Proxy Minion configuration attributes"""

    proxy: model_nornir_config_proxy
    hosts: Optional[Dict] = None
    groups: Optional[Dict] = None
    defaults: Optional[Dict] = None
    user_defined: Optional[Dict] = None


class SaltNornirExecutionFunctions(BaseModel):
    cli: model_exec_nr_cli = Field(None, description="Send show commands to devices")
    task: model_exec_nr_task = Field(
        None, description="Run arbitrary Nornir task plugin"
    )
    cfg: model_exec_nr_cfg = Field(None, description="Configure devices")
    tping: model_exec_nr_tping = Field(None, description="Test devices TCP connections")
    test: model_exec_nr_test = Field(None, description="Run test suites")
    nc: model_exec_nr_nc = Field(None, description="Manage devices using Netconf")
    http: model_exec_nr_http = Field(None, description="Manage devices using HTTP(S)")
    do: model_exec_nr_do = Field(None, description="Run simple workflows")
    file: model_exec_nr_file = Field(
        None, description="Work with Salt-Nornir Proxy Minion files"
    )
    learn: model_exec_nr_learn = Field(
        None, description="Save jobs output to Salt-Nornir Proxy Minion files"
    )
    find: model_exec_nr_find = Field(
        None, description="Search across Salt-Nornir Proxy Minion files"
    )
    diff: model_exec_nr_diff = Field(
        None, description="Produce difference for Salt-Nornir Proxy Minion files"
    )
    nornir_fun: model_exec_nr_nornir_fun = Field(
        None, description="Salt-Nornir Proxy Minion utilities"
    )
    gnmi: model_exec_nr_gnmi = Field(None, description="Manage devices using gNMI")
    snmp: model_exec_nr_snmp = Field(None, description="Manage devices using SNMP")
    netbox: model_exec_nr_netbox = Field(None, description="Interact with Netbox DCIM")

    class PicleConfig:
        subshell = True
        prompt = "salt[exec]#"


class SaltNornirStateFunctions(BaseModel):
    task: model_exec_nr_task
    cfg: model_exec_nr_cfg
    workflow: model_state_nr_workflow

    class PicleConfig:
        subshell = True
        prompt = "salt[state]#"


class SaltNornirRunnerFunctions(BaseModel):
    inventory: model_runner_nr_inventory
    call: model_runner_nr_call
    event: model_runner_nr_event
    cfg: model_runner_nr_cfg
    diagram: model_runner_nr_diagram

    class PicleConfig:
        subshell = True
        prompt = "salt[run]#"
