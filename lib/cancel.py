import time
from subprocess import Popen
from lib import db
from lib.utils import task_splitter

def cancel_tasks(id, workspace,ip=None):

    from celery import Celery
    from celery.task.control import revoke
    #app = Celery('tasks', broker='redis://localhost:6379', backend='redis://localhost:6379')
    app = Celery('tasks', broker='redis://localhost:6379', backend='db+sqlite:///results.sqlite')

    #TODO: add logic to revoke all takss for an IP
    #TODO: add logic to pause all taks (maybe just stopping celery workers?)
    num_cancelled = 0
    task_list = []
    if (id.lower()) == "all":
        running_tasks = db.get_running_tasks(workspace)
        pending_tasks = db.get_pending_tasks(workspace)
        paused_tasks = db.get_paused_tasks(workspace)
        running_pending_paused_task_list = running_tasks + pending_tasks + paused_tasks
        for task in running_pending_paused_task_list:
            task_list.append(task[0])
    elif ip:
        running_tasks = db.get_running_tasks(workspace,ip)
        pending_tasks = db.get_pending_tasks(workspace,ip)
        running_pending_paused_task_list = running_tasks + pending_tasks + paused_tasks
        for task in running_pending_paused_task_list:
            task_list.append(task[0])
    else:
        task_list = task_splitter(id)


    for task in task_list:
        try:
            task=db.get_task_id_status_pid(task)[0]
            db_id= task[0]
            task_id = task[1]
            task_status = task[2]
            task_pid = task[3]
            if task_status == "CANCELLED":
                print("[+] Task [{0}] has already been CANCELLED.".format(db_id))
        except:
            print("Could not find task {0}".format(task))


    for task in task_list:
        try:
            task=db.get_task_id_status_pid(task)[0]
            db_id= task[0]
            task_id = task[1]
            task_status = task[2]
            task_pid = task[3]

            if task_status == "SUBMITTED":
                result = revoke(task_id, terminate=True)
                db.update_task_status_cancelled(task_id)
                print("[-] Task [{0}] moved from PENDING to CANCELLED.".format(db_id))
                num_cancelled = num_cancelled + 1
        except:
            print("Could not find task {0}".format(task))

    for task in task_list:
        try:
            task=db.get_task_id_status_pid(task)[0]
            db_id= task[0]
            task_id = task[1]
            task_status = task[2]
            task_pid = task[3]
            if task_status == "STARTED":
                command = "kill " + str(task_pid) + " > /dev/null 2>&1"
                p = Popen(command, shell=True)
                c = p.communicate()
                time.sleep(.5)
                db.update_task_status_cancelled(task_id)
                print("[-] Task [{0}] moved from RUNNING to CANCELLED.".format(db_id))
                num_cancelled = num_cancelled + 1
        except:
            print("Could not find task {0}".format(task))

    for task in task_list:
        try:
            task=db.get_task_id_status_pid(task)[0]
            db_id= task[0]
            task_id = task[1]
            task_status = task[2]
            task_pid = task[3]
            if task_status == "PAUSED":
                time.sleep(.25)
                command = "kill -CONT " + str(task_pid) + " > /dev/null 2>&1 & sleep 1 & kill " + str(task_pid) + " > /dev/null 2>&1"
                p = Popen(command, shell=True)
                c = p.communicate()
                time.sleep(.5)
                db.update_task_status_cancelled(task_id)
                print("[-] Task [{0}] moved from PAUSED to CANCELLED.".format(db_id))
                num_cancelled = num_cancelled + 1
        except:
            print("Could not find task {0}".format(task))


    return num_cancelled