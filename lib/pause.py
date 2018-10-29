from subprocess import Popen
from lib import db
from lib.utils import task_splitter

def pause_running_tasks(id,workspace=None,repeat=None):
    task_list = []
    num_paused = 0

    if (id.lower()) == "all":
        running_tasks = db.get_running_tasks(workspace)
        for task in running_tasks:
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

            elif task_status == "STARTED":
                command = "kill -STOP " + str(task_pid) + " > /dev/null 2>&1"
                p = Popen(command, shell=True)
                c = p.communicate()
                db.update_task_status_paused(task_id)
                num_paused = num_paused + 1
                print("[+] Task [{0}] moved from RUNNING to PAUSED.".format(db_id))
            elif task_status == "PAUSED":
                if repeat != "True":
                    print("[+] Task [{0}] has already been PAUSED.".format(db_id))
        except:
            print("Could not find task {0}".format(db_id))
    return num_paused