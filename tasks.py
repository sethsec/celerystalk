from subprocess import Popen, PIPE
from celery import Celery
from celery import chain
import time
from timeit import default_timer as timer

import lib.csimport
from lib import db
from lib import utils
from lib import config_parser
import lib.scan
import urlparse
import os.path
from celery.signals import after_task_publish
from celery.utils import uuid
import sys
import re
import socket
import os
from libnmap.parser import NmapParser
from libnmap.process import NmapProcess


#app = Celery('tasks', broker='redis://localhost:6379', backend='redis://localhost:6379')
app = Celery('tasks', broker='redis://localhost:6379', backend='db+sqlite:///results.sqlite')
#app.config_from_object({'task_always_eager': True})


@app.task
def run_cmd(command_name, populated_command,celery_path,task_id,path=None,process_domain_tuple=None):
    """

    :param command_name:
    :param populated_command:
    :param celery_path:
    :param task_id:
    :param path:
    :param process_domain_tuple:
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

    #f.write("[+] CMD EXECUTED: " + str(start_ctime) + " - " + populated_command + "\n")
    #f.write(task_id)
    print(populated_command)

    #The except isnt working yet if I kill the process from linux cli. i guess that is not enough to trigger an exception.
    try:
        p = Popen(populated_command, shell=True, stdout=PIPE, stdin=PIPE)
        pid = p.pid + 1
        db.update_task_status_started("STARTED", task_id, pid, start_time_int)
        out,err = p.communicate()
        end = timer()
        end_ctime = time.ctime(end)
        run_time = end - start
        db.update_task_status_completed("COMPLETED", task_id, run_time)
        #f.write("\n[-] CMD COMPLETED in " + str(run_time) + " - " + populated_command + "\n")
        f.write("\n" + str(start_ctime) + "\t" + str(end_ctime) + "\t" + str("{:.2f}".format(run_time)) + "\t" + command_name + "\t" + populated_command)
    except:
        end = timer()
        run_time = end - start
        db.update_task_status_error("FAILED", task_id, run_time)

    f.close()

    if process_domain_tuple:
        lib.scan.determine_if_domains_are_in_scope(out,process_domain_tuple)

    return out

    #post.post_process(populated_command, output_base_dir, workspace, ip)


@app.task
def post_process(*args):
    command_name, populated_command,output_base_dir, workspace, ip, host_dir, simulation, scanned_service_port,scanned_service,scanned_service_protocol,celery_path = args

    urls_to_screenshot = []
    if "gobuster" in populated_command:

        scan_output_base_file_dir = os.path.join(output_base_dir,"celerystalkReports","screens",ip + "_" + str(
            scanned_service_port) + "_" + scanned_service_protocol)

        try:
            os.stat(scan_output_base_file_dir)
        except:
            os.makedirs(scan_output_base_file_dir)

        post_gobuster_filename = populated_command.split(">")[1].split("&")[0].strip()

        print("Post gobuster filename" + post_gobuster_filename + "\n")
        populated_command_list = populated_command.split(" ")

        index=0
        for arg in populated_command_list:
            if "-u" == populated_command_list[index]:
                if "http" in populated_command_list[index+1]:
                    scanned_url = populated_command_list[index+1]
                    #print("Scanned_url: " + scanned_url)
            index = index + 1

        try:
            with open(post_gobuster_filename,'r') as gobuster_file:
                lines = gobuster_file.read().splitlines()
                print(lines)
                if len(lines) > 300:
                    #TODO: def don't submit 100 direcotires to scan. but need a way to tell the user
                    exit()

            for url in lines:
                #url = url.split("?")[0].replace("//","/")
                if url.startswith("http"):
                    url_screenshot_filename = scan_output_base_file_dir + url.replace("http", "").replace("https", "") \
                        .replace("/", "_") \
                        .replace("\\", "") \
                        .replace(":", "_") + ".png"
                    url_screenshot_filename = url_screenshot_filename.replace("__", "")
                    db_path = (ip, scanned_service_port, url, 0, url_screenshot_filename, workspace)
                    db.insert_new_path(db_path)
                    print("Found Url: " + str(url))
                    urls_to_screenshot.append((url,url_screenshot_filename))
                    #result = lib.utils.take_screenshot(url,url_screenshot_filename)
        except Exception, e:
            if not simulation:
                print("[!] Could not open {0}".format(post_gobuster_filename))

    if "photon" in populated_command:
        scan_output_base_file_dir = os.path.join(output_base_dir, "celerystalkReports", "screens", ip + "_" + str(
            scanned_service_port) + "_" + scanned_service_protocol)

        try:
            os.stat(scan_output_base_file_dir)
        except:
            os.makedirs(scan_output_base_file_dir)

        #post_photon_filename = populated_command.split(">")[1].lstrip()
        post_photon_filename = lib.db.get_output_file_for_command(workspace,populated_command)[0][0]
        print(post_photon_filename)


        print("Post photon filename" + post_photon_filename + "\n")
        populated_command_list = populated_command.split(" ")

        index=0
        for arg in populated_command_list:
            if "-u" == populated_command_list[index]:
                if "http" in populated_command_list[index+1]:
                    scanned_url = populated_command_list[index+1]
                    #print("Scanned_url: " + scanned_url)
            index = index + 1

        try:
            with open(post_photon_filename,'r') as photon_file:
                lines = photon_file.read().splitlines()
                print(lines)
                if len(lines) > 300:
                    #TODO: def don't submit 100 direcotires to scan. but need a way to tell the user
                    lines = lines[:300]

            for url in lines:
                #url = url.split("?")[0].replace("//","/")
                if url.startswith("http"):
                    url_screenshot_filename = scan_output_base_file_dir + url.replace("http", "").replace("https", "") \
                        .replace("/", "_") \
                        .replace("\\", "") \
                        .replace(":", "_") + ".png"
                    url_screenshot_filename = url_screenshot_filename.replace("__", "")
                    db_path = (ip, scanned_service_port, url, 0, url_screenshot_filename, workspace)
                    db.insert_new_path(db_path)
                    print("Found Url: " + str(url))
                    urls_to_screenshot.append((str(url), url_screenshot_filename))

                    #result = lib.utils.take_screenshot(url,url_screenshot_filename)
                    #print(result)
        except Exception, e:
            if not simulation:
                print ("[!] Could not open {0}".format(post_photon_filename))

    if not simulation:
        if len(urls_to_screenshot) > 0:
            task_id = uuid()
            populated_command = "firefox-esr screenshots | {0} | {1}".format(ip, scan_output_base_file_dir)
            command_name = "Screenshots"
            utils.create_task(command_name, populated_command, ip, scan_output_base_file_dir, workspace, task_id)
            cel_take_screenshot.delay(urls_to_screenshot,task_id,ip,scan_output_base_file_dir, workspace,command_name,populated_command)

    #task_id = uuid()
    #cmd_name = "Screenshot"
    #populated_command = "Taking screenshots of all resources found on " + ip
    #utils.create_task(cmd_name, populated_command, ip, "", workspace, task_id)
    #lib.utils.take_screenshot(urls_to_screenshot)



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




    #else:
        #print("Not gobuster: " + populated_command + "\n")
    #f.close()




# @after_task_publish.connect(sender='app.task.run_cmd')
# def task_sent_handler(sender=None, headers=None, body=None, **kwargs):
#     db.create_task(task)


@app.task()
def cel_create_task(*args,**kwargs):
    command_name, populated_command, ip, output_dir, workspace, task_id = args
    db_task = (task_id, 1, command_name, populated_command, ip, output_dir, 'SUBMITTED', workspace)
    db.create_task(db_task)
    #return populated_command

@app.task()
def post_process_domains_bb(vhosts, command_name, populated_command, output_base_dir, workspace, simulation,
                         celery_path,out_of_scope_hosts):
    """

    :param vhosts:
    :param command_name:
    :param populated_command:
    :param output_base_dir:
    :param workspace:
    :param simulation:
    :param celery_path:
    :param out_of_scope_hosts:
    :return:
    """
    config, supported_services = config_parser.read_config_ini()
    vhosts = vhosts.splitlines()
    # from https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    for vhost in vhosts:
        # print("raw:\t" + vhost)
        vhost = ansi_escape.sub('', vhost)
        # print("escaped:\t" + vhost)
        if re.match(r'\w', vhost):
            try:
                ip = socket.gethostbyname(vhost)
                if vhost not in out_of_scope_hosts:
                    print("Found subdomain (in scope):\t" + vhost)
                    db_vhost = (ip, vhost, 1, 0, workspace)
                    db.create_vhost(db_vhost)
                else:
                    print("Found subdomain (out of scope):\t" + vhost)
                    db_vhost = (ip, vhost, 0, 0, workspace)
                    db.create_vhost(db_vhost)
            except:
                print("1There was an issue running the nmap scan against {0}.").format(vhost)
                ip = ""
                db_vhost = (ip, vhost, 0, 0, workspace)  # not in scope if no IP
                print(db_vhost)
                db.create_vhost(db_vhost)

    # pull all in scope vhosts that have not been submitted
    inscope_vhosts = db.get_inscope_unsubmitted_vhosts(workspace)
    for scannable_vhost in inscope_vhosts:
        scannable_vhost = scannable_vhost[0]
        ip = db.get_vhost_ip(scannable_vhost, workspace)
        ip = ip[0][0]
        print("I'm going to scan: " + scannable_vhost + ":" + ip)



        db_scanned_services = db.get_all_services_for_ip(ip, workspace)
        for (
        id, ip, scanned_service_port, scanned_service_protocol, scanned_service_name, workspace) in db_scanned_services:
            # run chain on each one and then update db as submitted
            scan_output_base_file_name = output_base_dir + "/" + ip + "/celerystalkOutput/" + scannable_vhost + "_" + str(
                scanned_service_port) + "_" + scanned_service_protocol + "_"
            host_dir = output_base_dir + "/" + ip

            # TODO: This def might introduce a bug - same code as parse config submit jobs to celery. need to just call that function here
            for section in config.sections():
                if (section == "http") or (section == "https"):
                    if section == scanned_service_name:
                        for (cmd_name, cmd) in config.items(section):
                            outfile = scan_output_base_file_name + cmd_name
                            populated_command = cmd.replace("[TARGET]", scannable_vhost)\
                                                    .replace("[PORT]",str(scanned_service_port))\
                                                    .replace("[OUTPUT]", outfile) \
                                                    .replace("[PATH]", "")
                            if simulation:
                                # debug - sends jobs to celery, but with a # in front of every one.
                                populated_command = "#" + populated_command

                            # Grab a UUID from celery.utils so that i can assign it to my task at init, which is amazing because
                            # that allows me to pass it to all of the tasks in the chain.

                            task_id = uuid()
                            utils.create_task(cmd_name,populated_command, scannable_vhost, outfile + ".txt",workspace, task_id)
                            result = chain(
                                #cel_create_task.subtask(args=(cmd_name,populated_command, scannable_vhost, outfile + ".txt",workspace, task_id)),
                                run_cmd.si(cmd_name, populated_command, celery_path, task_id).set(task_id=task_id),
                                post_process.si(cmd_name, populated_command, output_base_dir, workspace, scannable_vhost,
                                                host_dir,
                                                simulation,
                                                scanned_service_port, scanned_service_name,
                                                scanned_service_protocol, celery_path),
                            )()

                            host_audit_log = host_dir + "/" + "{0}_executed_commands.txt".format(ip)
                            f = open(host_audit_log, 'a')
                            f.write(populated_command + "\n\n")
                            f.close()

        db.update_vhosts_submitted(ip, scannable_vhost, workspace, 1)



@app.task()
def cel_nmap_scan(cmd_name, populated_command, host, config_nmap_options, celery_path, task_id,workspace):
    """
    :param cmd_name:
    :param populated_command:
    :param host:
    :param config_nmap_options:
    :param celery_path:
    :param task_id:
    :param workspace:
    :return:
    """
    # Without the sleep, some jobs were showing as submitted even though
    # they were started. Not sure why.
    #time.sleep(3)
    path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(lib.scan.__file__)),".."))
    audit_log = path + "/log/cmdExecutionAudit.log"
    f = open(audit_log, 'a')
    start_time = time.time()
    start_time_int = int(start_time)
    start_ctime = time.ctime(start_time)
    start = timer()

    #f.write(str(start_ctime)+ "," + "CMD EXECUTED" + "," + populated_command + "\n")
    #f.write(task_id)
    print(populated_command)

    #The except isnt working yet if I kill the process from linux cli. i guess that is not enough to trigger an exception.
    # try:
    print("[+] Kicking off nmap scan for " + host)
    db.update_task_status_started("STARTED", task_id, 0, start_time_int)
    nm = NmapProcess(host, options=config_nmap_options)
    rc = nm.run()
    nmap_report = NmapParser.parse(nm.stdout)
    end = timer()
    end_ctime = time.ctime(end)
    run_time = end - start
    db.update_task_status_completed("COMPLETED", task_id, run_time)

    #f.write("\n" + str(end_ctime) + "," + "CMD COMPLETED" + ","" + str(run_time) + " - " + populated_command + "\n")

    f.write(str(start_ctime)  + "," + str(end_ctime) + "," + str(run_time) + cmd_name + "\n")

    # except:
    #     end = timer()
    #     run_time = end - start
    #     db.update_task_status_error("FAILED", task_id, run_time)

    f.close()
    lib.csimport.process_nmap_data2(nmap_report, workspace)
    return nmap_report

@app.task()
def cel_scan_process_nmap_data(nmap_report,workspace):
    lib.csimport.process_nmap_data2(nmap_report, workspace)

@app.task()
def cel_process_db_services(output_base_dir, simulation, workspace):
    lib.scan.process_db_services(output_base_dir, simulation, workspace)


@app.task()
def cel_take_screenshot(urls_to_screenshot,task_id,ip,scan_output_base_file_dir, workspace,command_name,populated_command):
    #print("cel_take_screenshot")
    lib.utils.take_screenshot(urls_to_screenshot,task_id,ip,scan_output_base_file_dir, workspace,command_name,populated_command)