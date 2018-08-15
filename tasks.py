from subprocess import Popen, PIPE
from celery import Celery
from celery import chain
import time
from timeit import default_timer as timer
from lib import db
from lib import utils
from lib import config_parser
import urlparse
import os.path
from celery.signals import after_task_publish
from celery.utils import uuid
import sys


#app = Celery('tasks', broker='redis://localhost:6379', backend='redis://localhost:6379')
app = Celery('tasks', broker='redis://localhost:6379', backend='db+sqlite:///results.sqlite')
#app.config_from_object({'task_always_eager': True})

# @app.on_after_configure.connect
# def setup_periodic_tasks(sender, **kwargs):
#     sender.add_periodic_task(60.0, send_new_dirs_to_celery.s())



@app.task
def run_cmd(populated_command,celery_path,task_id,path=None):
    """
    :param populated_command: the command celery worker will run
    :param output_base_dir: passed so we can record the job in the cmdExecutionAudit.log
    :param workspace: the user specified workspace name. Default: default
    :param ip: The IP is passed so that we can write it to the database
    :return:
    """

    #task_id = run_cmd.request.id

    #task_id = run_cmd.request.id


    # Without the sleep, some jobs were showing as submitted even though
    # they were started. Not sure why.
    #time.sleep(3)
    audit_log = celery_path + "/log/cmdExecutionAudit.log"
    f = open(audit_log, 'a')
    start_time = time.time()
    start_time_int = int(start_time)
    start_ctime = time.ctime(start_time)
    start = timer()

    f.write("[+] CMD EXECUTED: " + str(start_ctime) + " - " + populated_command + "\n")
    f.write(task_id)
    print(populated_command)

    #The except isnt working yet if I kill the process from linux cli. i guess that is not enough to trigger an exception.
    try:
        p = Popen(populated_command, shell=True, stdout=PIPE, stdin=PIPE)
        pid = p.pid + 1
        db.update_task_status_started("STARTED", task_id, pid, start_time_int)
        out,err = p.communicate()
        end = timer()
        run_time = end - start
        db.update_task_status_completed("COMPLETED", task_id, run_time)
        f.write("\n[-] CMD COMPLETED in " + str(run_time) + " - " + populated_command + "\n")
    except:
        end = timer()
        run_time = end - start
        db.update_task_status_error("FAILED", task_id, run_time)

    f.close()
    return out

    #post.post_process(populated_command, output_base_dir, workspace, ip)


@app.task
def post_process(*args):
    populated_command,output_base_dir, workspace, ip, host_dir, simulation, scanned_service_port,scanned_service,scanned_service_protocol,celery_path = args


    #json_config = read_config_post(path)
    #test_log = "/opt/celerystalk/test.txt"
    #f = open(test_log, 'a')
    ##f.write(populated_command + "\n\n")
    #print("post")


    if "amass" in populated_command:
        json_config = config_parser.read_config()
        post_amass_filename = populated_command.split(">")[1].rstrip()
        with open(post_amass_filename,'r') as amass_file:
            lines = amass_file.read().splitlines()
            for vhost in lines:
                in_scope,ip = utils.domain_scope_checker(vhost,workspace)
                db_vhost = (ip,vhost,in_scope,0,workspace)
                db.create_vhost(db_vhost)

            #pull all in scope vhosts that have not been submitted
            for scannable_vhost in db.get_inscope_vhosts(workspace):
                scan_output_base_file_name = output_base_dir + "/" + ip + "/celerystalkOutput/" + scannable_vhost + str(scanned_service_port) + "_" + scanned_service_protocol + "_"
                for db_scanned_service in db.get_all_services_for_ip(ip,workspace):
                #run chain on each one and then update db as submitted

                    for entry in json_config["services"][db_scanned_service]["output"]:
                        if (db_scanned_service == "http") or (db_scanned_service == "https"):
                            for cmd in entry["commands"]:
                                if simulation:
                                    # debug - sends jobs to celery, but with a # in front of every one.
                                    populated_command = (("#" + cmd) % {"IP": scannable_vhost, "PORT": scanned_service_port,
                                                                        "OUTPUTDIR": scan_output_base_file_name})
                                else:
                                    populated_command = (cmd % {"IP": scannable_vhost, "PORT": scanned_service_port,
                                                                "OUTPUTDIR": scan_output_base_file_name})



                                task_id = uuid()
                                result = chain(
                                    # insert a row into the database to mark the task as submitted. a subtask does not get tracked
                                    # in celery the same way a task does, for instance, you can't find it in flower
                                    #cel_create_task.subtask(args=(populated_command, ip, workspace, task_id), task_id=task_id),
                                    cel_create_task.subtask(args=(populated_command, ip, workspace, task_id)),
                                    # run the command. run_task takes care of marking the task as started and then completed.
                                    # The si tells run_cmd to ignore the data returned from a previous task
                                    run_cmd.si(populated_command,celery_path,task_id).set(task_id=task_id),

                                    # right now, every executed command gets sent to a generic post_process task that can do
                                    # additinoal stuff based on the command that just ran.
                                    post_process.si(populated_command, output_base_dir, workspace, ip, host_dir, simulation,
                                                    scanned_service_port,db_scanned_service,scanned_service_protocol,celery_path),
                                )()  # .apply_async()

                                host_audit_log = host_dir + "/" + "{0}_executed_commands.txt".format(ip)
                                f = open(host_audit_log, 'a')
                                f.write(populated_command + "\n\n")
                                f.close()


    if "gobuster" in populated_command:
        #f.write("\nPost_gobuster!\n\n")
        #print("gobuster")
        #print(args)
        #print(populated_command,output_base_dir, workspace, ip, host_dir, simulation, scanned_service_port)
        #f.write(populated_command + "\n")
        # print(populated_command + " - populatd command\n")
        post_gobuster_filename = populated_command.split(">")[1].split("&")[0].strip()
        print(post_gobuster_filename + " - post gobuster filename \n")
        populated_command_list = populated_command.split(" ")
        # print("\npopulated_command_list\n")
        # print(populated_command_list)

        index=0
        for arg in populated_command_list:
            if "-u" == populated_command_list[index]:
                if "http" in populated_command_list[index+1]:
                    scanned_url = populated_command_list[index+1]

                print("\nscanned_url\n")
                print(scanned_url)
            index = index + 1

        with open(post_gobuster_filename,'r') as gobuster_file:
            lines = gobuster_file.read().splitlines()
            print(lines)
            if len(lines) > 100:
                #TODO: def don't submit 100 direcotires to scan. but need a way to tell the user
                exit()

        for url in lines:
            url = url.split("?")[0].replace("//","/")
            if url.startswith("http"):
                db_path = (ip, scanned_service_port, url, 0, workspace)
                db.insert_new_path(db_path)
                print("\nurl: " + str(url))



#Commenting this next part out because i don't think i want to auto run against newly discovered paths. I think I am
#going to give the list of paths back to the user and let them pick which ones to submit to celery

            # post_output_base_file_name = post_gobuster_filename.split("__")[0] + "_" + path.replace("/", "_")
            #
            # json_config = read_config_post(path)
                # for entry in json_config["services"][scanned_service]["output"]:
                #     for cmd in entry["commands"]:
                #         if simulation == "True":
                #             #debug - sends jobs to celery, but with a # in front of every one.
                #             populated_command = (("##" + cmd) % {"OUTPUTDIR": post_output_base_file_name})
                #         else:
                #             populated_command = (cmd % {"IP": ip, "PORT": scanned_service_port,
                #                                         "OUTPUTDIR": post_output_base_file_name})
                #
                #         task_id = uuid()
                #         result = chain(
                #             # insert a row into the database to mark the task as submitted. a subtask does not get tracked
                #             # in celery the same way a task does, for instance, you can't find it in flower
                #             cel_create_task.subtask(args=(populated_command, ip, workspace, task_id), task_id=task_id),
                #
                #             # run the command. run_task takes care of marking the task as started and then completed.
                #             # The si tells run_cmd to ignore the data returned from a previous task
                #             run_cmd.si(populated_command, output_base_dir, workspace, ip, task_id),
                #
                #             # right now, every executed command gets sent to a generic post_process task that can do
                #             # additinoal stuff based on the command that just ran.
                #             post_process.si(populated_command, output_base_dir, workspace, ip, host_dir, simulation,
                #                             scanned_service_port),
                #         )()  # .apply_async()
                #
                #         host_audit_log = host_dir + "/" + "{0}_executed_commands.txt".format(ip)
                #         f = open(host_audit_log, 'a')
                #         f.write(populated_command + "\n\n")
                #         f.close()




    else:
        print("Not gobuster: " + populated_command + "\n")
    #f.close()



@app.task
def run2(populated_command, output_base_dir, workspace, ip,host_dir, simulation, scanned_service_port):
    p = Popen(populated_command, shell=True, stdout=PIPE, stdin=PIPE)
    c = p.communicate()
    return "run2done"


# @after_task_publish.connect(sender='app.task.run_cmd')
# def task_sent_handler(sender=None, headers=None, body=None, **kwargs):
#     db.create_task(task)


@app.task()
def cel_create_task(*args,**kwargs):
    populated_command, ip, workspace, task_id = args
    db_task = (task_id, 1, populated_command, ip, 'SUBMITTED', workspace)
    db.create_task(db_task)
    #return populated_command


@app.task()
def post_process_domains(vhosts,populated_command,output_base_dir,workspace,domain,simulation,celery_path):
    config,supported_services = config_parser.read_config_ini()
    #(populated_command,output_base_dir,workspace,domain,simulation) = args
    vhosts = vhosts.splitlines()
    for vhost in vhosts:
        in_scope,ip = utils.domain_scope_checker(vhost,workspace)
        if in_scope == 1:
            db_vhost = (ip,vhost,in_scope,0,workspace)
            db.create_vhost(db_vhost)
        else:
            db_vhost = ("", vhost, 0, 0, workspace)
            db.create_vhost(db_vhost)

    #pull all in scope vhosts that have not been submitted
    inscope_vhosts = db.get_inscope_unsubmitted_vhosts(workspace)
    for scannable_vhost in inscope_vhosts:
        scannable_vhost = scannable_vhost[0]
        ip = db.get_vhost_ip(scannable_vhost,workspace)
        ip = ip[0][0]
        db_scanned_services = db.get_all_services_for_ip(ip, workspace)
        print("hello")
        for (id,ip,scanned_service_port,scanned_service_protocol,scanned_service_name,workspace) in db_scanned_services:
        #run chain on each one and then update db as submitted
            scan_output_base_file_name = output_base_dir + "/" + ip + "/celerystalkOutput/" + scannable_vhost + "_" +  str(scanned_service_port) + "_" + scanned_service_protocol + "_"
            host_dir = output_base_dir + "/" + ip

            #TODO: This def might introduce a bug - same code as parse config submit jobs to celery. need to just call that function here
            for section in config.sections():
                if (section == "http") or (section == "https"):
                    if section == scanned_service_name:
                        for (key, val) in config.items(section):
                            val = val.split("\n")
                            for cmd in val:
                                outfile = scan_output_base_file_name + key
                                populated_command = cmd.replace("[TARGET]", scannable_vhost).replace("[PORT]",
                                    str(scanned_service_port)).replace("[OUTPUT]", outfile)
                                if simulation:
                                    # debug - sends jobs to celery, but with a # in front of every one.
                                    populated_command = "#" + populated_command

                                # Grab a UUID from celery.utils so that i can assign it to my task at init, which is amazing because
                                # that allows me to pass it to all of the tasks in the chain.

                                task_id = uuid()
                                result = chain(
                                    # insert a row into the database to mark the task as submitted. a subtask does not get tracked
                                    # in celery the same way a task does, for instance, you can't find it in flower
                                    cel_create_task.subtask(args=(populated_command, scannable_vhost, workspace, task_id)),

                                    # run the command. run_task takes care of marking the task as started and then completed.
                                    # The si tells run_cmd to ignore the data returned from a previous task
                                    run_cmd.si(populated_command,celery_path,task_id).set(task_id=task_id),

                                    # right now, every executed command gets sent to a generic post_process task that can do
                                    # additinoal stuff based on the command that just ran.
                                    post_process.si(populated_command, output_base_dir, workspace, scannable_vhost, host_dir,
                                                          simulation,
                                                          scanned_service_port, scanned_service_name,
                                                          scanned_service_protocol,celery_path),
                                )()  # .apply_async()

                                #task_id_list.append(result.task_id)
                                host_audit_log = host_dir + "/" + "{0}_executed_commands.txt".format(ip)
                                f = open(host_audit_log, 'a')
                                f.write(populated_command + "\n\n")
                                f.close()

        db.update_vhosts_submitted(ip,scannable_vhost,workspace,1)

            # for entry in config["services"][service]["output"]:
            #     if (service == "http") or (service == "https"):
            #         for cmd in entry["commands"]:
            #             if simulation:
            #                 # debug - sends jobs to celery, but with a # in front of every one.
            #                 populated_command = (("#" + cmd) % {"IP": scannable_vhost, "PORT": port,
            #                                                     "OUTPUTDIR": scan_output_base_file_name})
            #             else:
            #                 populated_command = (cmd % {"IP": scannable_vhost, "PORT": port,
            #                                             "OUTPUTDIR": scan_output_base_file_name})
            #
            #
            #
            #             task_id = uuid()
            #             result = chain(
            #                 # insert a row into the database to mark the task as submitted. a subtask does not get tracked
            #                 # in celery the same way a task does, for instance, you can't find it in flower
            #                 cel_create_task.subtask(args=(populated_command, ip, workspace, task_id), task_id=task_id),
            #
            #                 # run the command. run_task takes care of marking the task as started and then completed.
            #                 # The si tells run_cmd to ignore the data returned from a previous task
            #                 run_cmd.si(populated_command, output_base_dir, workspace, ip, task_id),
            #
            #                 # right now, every executed command gets sent to a generic post_process task that can do
            #                 # additinoal stuff based on the command that just ran.
            #                 post_process.si(populated_command, output_base_dir, workspace, ip, host_dir, simulation,
            #                                 port,service,proto),
            #             )()  # .apply_async()
            #
            #             host_audit_log = host_dir + "/" + "{0}_executed_commands.txt".format(ip)
            #             f = open(host_audit_log, 'a')
            #             f.write(populated_command + "\n\n")
            #             f.close()
