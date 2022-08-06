"""
File to contain pydantic models for Salt-Nornir modules functions
"""
import logging

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
from typing import Union, Optional, List, Any, Dict
from nornir_salt.utils.pydantic_models import FilesCallsEnum, model_ffun_fx_filters
from nornir_salt.plugins.functions import FFun_functions  # list of Fx names

# import salt libs, wrapping it in try/except for docs to generate
try:
    from salt.exceptions import CommandExecutionError
except:
    log.error("Salt-Nornir Pydantic modesl - failed importing SALT libraries")


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
    render: Optional[Union[List[StrictStr], StrictStr]]
    context: Optional[Dict]
    dcache: Optional[Union[StrictStr, StrictBool]]
    defaults: Optional[Dict]
    diff: Optional[StrictStr]
    dp: Optional[Union[StrictStr, List[Union[StrictStr, Dict]]]]
    download: Optional[List[StrictStr]]
    dump: Optional[StrictStr]
    event_failed: Optional[StrictBool]
    event_progress: Optional[StrictBool]
    hcache: Optional[Union[StrictStr, StrictBool]]
    iplkp: Optional[StrictStr]
    jmespath: Optional[StrictStr]
    match: Optional[StrictStr]
    before: Optional[StrictInt]
    ntfsm: Optional[StrictBool]
    run_connect_retry: Optional[StrictInt]
    run_task_retry: Optional[StrictInt]
    run_creds_retry: Optional[List[Union[StrictStr, Dict]]]
    run_num_workers: Optional[StrictInt]
    run_num_connectors: Optional[StrictInt]
    run_reconnect_on_fail: Optional[StrictBool]
    render: Optional[Union[List[StrictStr], StrictStr]]
    run_ttp: Optional[StrictStr]
    ttp_structure: Optional[EnumExecTTPStructTypes] = "flat_list"
    table: Optional[Union[EnumExecTableTypes, Dict, StrictBool]] = "brief"
    headers: Optional[Union[StrictStr, List[StrictStr]]]
    headers_exclude: Optional[Union[StrictStr, List[StrictStr]]]
    sortby: Optional[StrictStr]
    reverse: Optional[StrictBool]
    tests: Optional[Union[List[List[StrictStr]], List[Dict]]]
    failed_only: Optional[StrictBool]
    remove_tasks: Optional[StrictBool]
    tf: Optional[StrictStr]
    tf_skip_failed: Optional[StrictBool]
    to_dict: Optional[StrictBool]
    add_details: Optional[StrictBool]
    xml_flake: Optional[StrictStr]
    xpath: Optional[StrictStr]
    worker: Optional[Union[StrictInt, StrictStr]]


class EnumExecNrCliPlugins(str, Enum):
    plugin_netmiko = "netmiko"
    plugin_scrapli = "scrapli"
    plugin_napalm = "napalm"
    plugin_pyats = "pyats"


class model_exec_nr_cli(ModelExecCommonArgs):
    """Model for salt_nornir.modules.nornir_proxy_execution_module.cli function arguments"""

    args: Optional[Union[List[StrictStr], StrictStr]]
    commands: Optional[Union[List[StrictStr], StrictStr]]
    plugin: Optional[EnumExecNrCliPlugins] = "netmiko"
    filename: Optional[StrictStr]

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"

    @root_validator(pre=True)
    def check_commands_given(cls, values):
        assert (
            values.get("args")
            or values.get("commands")
            or values.get("filename")
            or values.get("run_ttp")
        ), "No CLI commands, filename or run_ttp provided"
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

    args: Optional[List[Union[StrictStr]]]
    commands: Optional[Union[List[StrictStr], StrictStr]]
    plugin: Optional[EnumExecNrCfgPlugins] = "netmiko"
    filename: Optional[StrictStr]
    config: Optional[Union[Dict, StrictStr]]

    class Config:
        extra = "allow"

    @root_validator(pre=True)
    def check_commands_given(cls, values):
        assert (
            values.get("args") or
            values.get("commands") or
            values.get("filename") or
            values.get("config")
        ), "No CLI commands, filename or config provided"
        return values


class model_exec_nr_tping(ModelExecCommonArgs):
    """Model for salt_nornir.modules.nornir_proxy_execution_module.tping function arguments"""

    ports: Optional[Union[List[StrictInt], StrictInt]]
    timeout: Optional[StrictInt]
    host: Optional[StrictStr]

    class Config:
        extra = "allow"


class model_exec_nr_test(BaseModel):
    name: Optional[StrictStr]
    test: Optional[StrictStr]
    pattern: Optional[StrictStr]
    function_file: Optional[StrictStr]
    saltenv: Optional[StrictStr]
    suite: Optional[Union[StrictStr, List[Dict[StrictStr, Any]]]]
    subset: Optional[Union[StrictStr, List[StrictStr]]]
    dump: Optional[StrictStr]
    commands: Optional[Union[StrictStr, List[StrictStr]]]
    plugin: Optional[EnumExecNrCliPlugins]
    use_ps: Optional[StrictBool]
    cli: Optional[
        Dict
    ]  # if reference model_exec_nr_cli here it fails as test's cli might not contain commands and its normal
    failed_only: Optional[StrictBool]
    remove_tasks: Optional[StrictBool]
    table: Optional[Union[EnumExecTableTypes, Dict, StrictBool]] = "brief"
    headers: Optional[Union[StrictStr, List[StrictStr]]]
    sortby: Optional[StrictStr]
    reverse: Optional[StrictBool]

    class Config:
        extra = "allow"


class EnumExecNrNcPlugins(str, Enum):
    plugin_netmiko = "ncclient"
    plugin_scrapli = "scrapli"


class model_exec_nr_nc(ModelExecCommonArgs):
    """Model for salt_nornir.modules.nornir_proxy_execution_module.nc function arguments"""

    args: Optional[List[Union[StrictStr]]]
    plugin: Optional[EnumExecNrNcPlugins] = "ncclient"
    call: Optional[StrictStr]
    data: Optional[StrictStr]
    method_name: Optional[StrictStr]
    source: Optional[StrictStr]
    target: Optional[StrictStr]
    config: Optional[StrictStr]
    ncclient_filter: Optional[Union[List[StrictStr], StrictStr]] = Field(alias="filter")
    scrapli_filter: Optional[StrictStr] = Field(alias="filter_")

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

    args: Optional[List[StrictStr]]
    method: Optional[EnumExecNrHTTPMethods]
    url: Optional[StrictStr]

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
    args: Optional[List]
    kwargs: Optional[Dict]
    description: Optional[StrictStr]

    class Config:
        extra = "allow"


class model_exec_nr_do_action(BaseModel):
    """Model to validate list of nr.do action items"""

    action: List[model_exec_nr_do_action_step]

    class Config:
        extra = "forbid"


class model_exec_nr_do(BaseModel):
    """Model for salt_nornir.modules.nornir_proxy_execution_module.do function arguments"""

    args: conlist(StrictStr, min_items=1)
    stop_on_error: Optional[StrictBool]
    filepath: Optional[StrictStr]
    default_renderer: Optional[StrictStr]
    describe: Optional[StrictBool]
    tf: Optional[StrictBool]
    diff: Optional[StrictBool]

    class Config:
        extra = "allow"


class model_exec_nr_file(ModelExecCommonArgs):
    """Model for salt_nornir.modules.nornir_proxy_execution_module.file function arguments"""

    args: Optional[List[StrictStr]]
    call: Optional[FilesCallsEnum]
    filegroup: Optional[Union[StrictStr, List[StrictStr], StrictBool]]
    last: Optional[Union[StrictInt, List[StrictInt], StrictStr]]

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

    args: conlist(StrictStr, min_items=1)
    fun: Optional[EnumLearnSupportedFun]
    tf: Optional[Union[StrictStr, StrictBool]]
    tf_skip_failed: Optional[StrictBool]

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

    args: conlist(StrictStr, min_items=1)
    table: Optional[Union[EnumExecTableTypes, Dict, StrictBool]] = "brief"
    headers: Optional[Union[StrictStr, List[StrictStr]]]
    headers_exclude: Optional[Union[StrictStr, List[StrictStr]]]
    sortby: Optional[StrictStr]
    reverse: Optional[StrictBool]
    last: Optional[Union[StrictInt, List[StrictInt], StrictStr]]

    class Config:
        extra = "allow"

    @root_validator(pre=True)
    def check_params_given(cls, values):
        if not values.get("args"):
            raise CommandExecutionError("No 'args' provided to source filegroup name")
        return values


class model_exec_nr_diff(model_ffun_fx_filters):
    """Model for salt_nornir.modules.nornir_proxy_execution_module.find function arguments"""

    args: Optional[List[StrictStr]]
    diff: Optional[List[StrictStr]]
    last: Optional[Union[StrictInt, List[StrictInt], StrictStr]]

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

    args: Optional[List[StrictStr]]
    fun: Optional[EnumNrFun]
    worker: Optional[Union[StrictInt, StrictStr]]
    workers_only: Optional[StrictBool]
    stat: Optional[StrictStr]

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

    args: Optional[List[StrictStr]]
    call: Optional[StrictStr]
    plugin: Optional[EnumGnmiPlugins]
    method_name: Optional[StrictStr]
    path: Optional[Union[StrictStr, List[StrictStr]]]
    filename: Optional[StrictStr]

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


class StateWorkflowOptions(BaseModel):
    fail_if_any_host_fail_any_step: Optional[List[StrictStr]]
    fail_if_any_host_fail_all_step: Optional[List[StrictStr]]
    fail_if_all_host_fail_any_step: Optional[List[StrictStr]]
    fail_if_all_host_fail_all_step: Optional[List[StrictStr]]
    report_all: Optional[StrictBool]
    filters: Optional[model_ffun_fx_filters]
    hcache: Optional[StrictBool]
    dcache: Optional[StrictBool]
    sumtable: Optional[Union[StrictBool, StrictStr]]
    kwargs: Optional[Dict]

    class Config:
        extra = "forbid"


class StateWorkflowStep(BaseModel):
    name: StrictStr
    function: StrictStr
    kwargs: Optional[Dict]
    args: Optional[List]
    report: Optional[StrictBool]
    run_if_fail_any: Optional[List[StrictStr]]
    run_if_pass_any: Optional[List[StrictStr]]
    run_if_fail_all: Optional[List[StrictStr]]
    run_if_pass_all: Optional[List[StrictStr]]

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

    args: Optional[List[StrictStr]]
    tgt: Optional[StrictStr]
    tgt_type: Optional[StrictStr]
    verbose: Optional[StrictBool]
    job_retry: Optional[StrictInt]
    job_timeout: Optional[StrictInt]
    table: Optional[Union[StrictStr, StrictBool, Dict]]
    headers: Optional[List[StrictStr]]
    reverse: Optional[StrictBool]
    sortby: Optional[StrictStr]
    tree: Optional[StrictBool]

    class Config:
        extra = "forbid"

    @root_validator(pre=True)
    def check_params_given(cls, values):
        if not (values.get("args") or any(F in values for F in FFun_functions)):
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

    args: Optional[List[StrictStr]]
    fun: Optional[StrictStr]
    tgt: Optional[StrictStr]
    tgt_type: Optional[StrictStr]
    job_retry: Optional[StrictInt]
    job_timeout: Optional[StrictInt]
    progress: Optional[Union[RunnerProgressTypes, StrictBool]]
    ret_struct: Optional[RunnerRetStructTypes]

    class Config:
        extra = "allow"

    @root_validator(pre=True)
    def check_params_given(cls, values):
        if not values.get("args") and "fun" not in values:
            raise CommandExecutionError("No execution function name provided")
        return values


class model_runner_nr_event(BaseModel):
    """Model for salt_nornir.states.nornir_proxy_runner_module.event function arguments"""

    tag: Optional[StrictStr]
    jid: Optional[Union[StrictStr, StrictInt]]
    stop_signal: Optional[Any]
    progress: Optional[Union[RunnerProgressTypes, StrictBool]]

    class Config:
        extra = "forbid"


class model_runner_nr_cfg(ModelExecCommonArgs):
    """Model for salt_nornir.states.nornir_proxy_runner_module.call function arguments"""

    host_batch: Optional[StrictInt]
    first_batch: Optional[StrictInt]
    fromdir: Optional[StrictStr]
    fromdict: Optional[Dict[StrictStr, StrictStr]]
    tgt: Optional[StrictStr]
    tgt_type: Optional[StrictStr]
    job_retry: Optional[StrictInt]
    job_timeout: Optional[StrictInt]
    progress: Optional[Union[RunnerProgressTypes, StrictBool]]
    saltenv: Optional[StrictStr]
    ret_struct: Optional[RunnerRetStructTypes]
    interactive: Optional[StrictBool]
    dry_run: Optional[StrictBool]
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

    args: Optional[List[StrictStr]]
    data_plugin: Optional[EnumN2GDataPlugins]
    diagram_plugin: Optional[EnumN2GDiagramPlugins]
    tgt: Optional[StrictStr]
    tgt_type: Optional[StrictStr]
    job_retry: Optional[StrictInt]
    job_timeout: Optional[StrictInt]
    progress: Optional[Union[RunnerProgressTypes, StrictBool]]
    save_data: Optional[Union[StrictBool, StrictStr]]
    outfile: Optional[StrictStr]
    cli: Optional[Dict[StrictStr, Any]]
    filegroup: Optional[StrictStr]
    last: Optional[StrictInt]

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
    hosts: Optional[Dict]
    groups: Optional[Dict]
    defaults: Optional[Dict]


class SaltNornirExecutionFunctions(BaseModel):
    cli: model_exec_nr_cli
    tas: model_exec_nr_task
    cfg: model_exec_nr_cfg
    tping: model_exec_nr_tping
    test: model_exec_nr_test
    nc: model_exec_nr_nc
    http: model_exec_nr_http
    do: model_exec_nr_do
    file: model_exec_nr_file
    learn: model_exec_nr_learn
    find: model_exec_nr_find
    diff: model_exec_nr_diff
    nornir_fun: model_exec_nr_nornir_fun
    gnmi: model_exec_nr_gnmi


class SaltNornirStateFunctions(BaseModel):
    task: model_exec_nr_task
    cfg: model_exec_nr_cfg
    workflow: model_state_nr_workflow


class SaltNornirRunnerFunctions(BaseModel):
    inventory: model_runner_nr_inventory
    call: model_runner_nr_call
    event: model_runner_nr_event
    cfg: model_runner_nr_cfg
    diagram: model_runner_nr_diagram


class SaltNornirMasterModel(BaseModel):
    execution: SaltNornirExecutionFunctions
    state: SaltNornirStateFunctions
    runner: SaltNornirRunnerFunctions
    config: model_nornir_config
