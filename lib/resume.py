from subprocess import Popen

from lib import db
from lib.utils import task_splitter


def resume_paused_tasks(id,workspace=None):
    task_list = []
    num_resumed = 0
    if (id.lower()) == "all":
        paused_tasks = db.get_paused_tasks(workspace)
        for task in paused_tasks:
            task_list.append(task[0])
    else:
        task_list = task_splitter(id)

    for task in task_list:
        try:
            task = db.get_task_id_status_pid(task)[0]
            db_id = task[0]
            task_id = task[1]
            task_status = task[2]
            task_pid = task[3]

            if task_status == "SUBMITTED":
                print("[-] Task [{0}] is still PENDING, it can't be PAUSED.".format(db_id))

            elif task_status == "PAUSED":
                command = "kill -CONT " + str(task_pid) + " > /dev/null 2>&1"
                p = Popen(command, shell=True)
                c = p.communicate()
                db.update_task_status_resumed(task_id)
                print("[+] Task [{0}] moved from PAUSED to RUNNING.".format(db_id))
                num_resumed = num_resumed + 1
        except:
            print("Could not find task {0}".format(db_id))
    return num_resumed