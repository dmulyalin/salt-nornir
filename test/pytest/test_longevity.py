import logging
import pprint
import pytest
import random
from rich.progress import Progress, TimeElapsedColumn, BarColumn

log = logging.getLogger(__name__)

try:
    import salt.client
    import salt.config
    import salt.utils.event
    import salt.exceptions

    HAS_SALT = True
except:
    HAS_SALT = False
    raise SystemExit("SALT Nonrir Tests - failed importing SALT libraries")

if HAS_SALT:
    # initiate execution modules client to run 'salt xyz command' commands
    client = salt.client.LocalClient()
    opts = salt.config.client_config("/etc/salt/master")
    event = salt.utils.event.get_event(
        "master", sock_dir=opts["sock_dir"], transport=opts["transport"], opts=opts
    )
    
tasks_list = [
    {
        "fun": "nr.cli",
        "arg": ["show clock", "show hostname", "show version"],
        "kwarg": {"to_dict": False},
        "tgt": "nrp1",
        "tgt_type": "glob",
        "timeout": 60,
    },
    {
        "fun": "nr.cfg",
        "arg": ["logging host 1.2.3.4"],
        "kwarg": {"plugin": "netmiko", "to_dict": False},
        "tgt": "nrp1",
        "tgt_type": "glob",
        "timeout": 60,
    },    
    {
        "tgt": "nrp1",
        "fun": "nr.task",
        "arg": [],
        "kwarg": {"plugin": "nornir_salt.plugins.tasks.sleep", "sleep_for": 1},
        "tgt_type": "glob",
        "timeout": 60,
    },
    {
        "tgt": "nrp1",
        "fun": "nr.task",
        "arg": [],
        "kwarg": {
            "plugin": "nornir_salt.plugins.tasks.nr_test", 
            "result": "Nothing to see here",
        },
        "tgt_type": "glob",
        "timeout": 60,
    }
]

def run_for_tasks_count():
    tasks_count = 10000
    job_results_report = open("run_for_tasks_count_report.txt", "w", encoding="utf-8")
    worker_stats_before = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["worker", "stats"],
    )
    stats_before = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["stats"],
    )
    workers_count = len(worker_stats_before["nrp1"])
    job_results_report.write("Stats before:\n{}\n".format(pprint.pformat(stats_before)))
    job_results_report.write("Workers Stats before:\n{}\n".format(pprint.pformat(worker_stats_before)))
    progress = Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        "{task.completed}/{task.total}",
        TimeElapsedColumn(),
        refresh_per_second=5,
    )
        
    # run tasks
    with progress:
        tasks_progress = progress.add_task("Running {} tasks".format(tasks_count), total=tasks_count)
        
        while tasks_count:
            job_results_report.write("Tasks count: {}\n".format(tasks_count))
            jobs = []
            for _ in range(workers_count):
                if tasks_count <= 0:
                    continue
                task = tasks_list[random.randint(0, len(tasks_list) - 1)]
                job = client.run_job(**task)
                jobs.append(job)
                job_results_report.write("\nTask {}, started job:\n{}\n{}\n".format(tasks_count, job, task))
                tasks_count -= 1
                progress.update(tasks_progress, advance=1)
            
            # get jobs
            for j in jobs:
                results_iterator = client.get_cli_returns(timeout=60, **j)
                for i in results_iterator:
                    job_results_report.write("\nFinished job: {}\n".format(j))
                    job_results_report.write(pprint.pformat(i) + "\n")

    # collect after stats
    worker_stats_after = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["worker", "stats"],
    )
    stats_after = client.cmd(
        tgt="nrp1",
        fun="nr.nornir",
        arg=["stats"],
    )
    job_results_report.write("\nStats after:\n{}\n".format(pprint.pformat(stats_after)))
    job_results_report.write("\nWorkers Stats after:\n{}\n".format(pprint.pformat(worker_stats_after)))
    job_results_report.close()

# run_for_tasks_count()