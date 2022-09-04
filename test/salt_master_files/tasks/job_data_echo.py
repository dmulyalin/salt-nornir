from nornir.core.task import Result, Task

def task(task):
    "This task echoes back job_data content"
    task.name = "job_data_echo"
    
    job_data = task.host["job_data"]
    
    return Result(host=task.host, result=job_data)