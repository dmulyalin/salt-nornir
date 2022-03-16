import time
from nornir.core.task import Result, Task

def task(task):
    # Task to return timestamp of when its done
    time.sleep(2)
    return Result(host=task.host, result=time.time())