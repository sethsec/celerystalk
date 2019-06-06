from subprocess import Popen, PIPE
from celery import Celery
import time
from timeit import default_timer as timer
import lib.csimport
from lib import db
import lib.scan
import simplejson
import os.path
from celery.utils import uuid
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
    command_name, populated_command,output_base_dir, workspace, vhost, host_dir, simulation, scanned_service_port,scanned_service,scanned_service_protocol,celery_path = args
    screenshot_name = ""
    urls_to_screenshot = []
    urls_to_screenshot_with_filenames = []
    if "gobuster" in populated_command:
        screenshot_name = "gobuster"

        scan_output_base_file_dir = os.path.join(output_base_dir,"celerystalkReports","screens",vhost + "_" + str(
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
                url = url.split("?")[0]#.replace("//","/")
                if url.startswith("http"):
                    url_screenshot_filename = scan_output_base_file_dir + "/" + url.replace("http", "").replace("https", "") \
                        .replace("/", "_") \
                        .replace("\\", "") \
                        .replace(":", "_") + ".png"
                    url_screenshot_filename = url_screenshot_filename.replace("__", "")
                    db_path = (vhost, scanned_service_port, url, 0, url_screenshot_filename, workspace)
                    db.insert_new_path(db_path)
                    print("Found Url: " + str(url))
                    urls_to_screenshot_with_filenames.append((url,url_screenshot_filename))
                    urls_to_screenshot.append((url,url_screenshot_filename))

                    #result = lib.utils.take_screenshot(url,url_screenshot_filename)
        except Exception, e:
            if not simulation:
                print("[!] Could not open {0}".format(post_gobuster_filename))


    if "photon" in populated_command:
        screenshot_name = "photon"

        scan_output_base_file_dir = os.path.join(output_base_dir, "celerystalkReports", "screens", vhost + "_" + str(
            scanned_service_port) + "_" + scanned_service_protocol)

        try:
            os.stat(scan_output_base_file_dir)
        except:
            os.makedirs(scan_output_base_file_dir)

        #post_photon_filename = populated_command.split(">")[1].lstrip()
        post_photon_filename = lib.db.get_output_file_for_command(workspace,populated_command)[0][0]
        #print(post_photon_filename)


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
            with open(post_photon_filename, 'r') as photon_file:
                photon_file_json = simplejson.load(photon_file)

                good_sections = ["internal", "robots", "fuzzable"]
                for section in good_sections:
                    for url in photon_file_json[section]:
                        if url.startswith("http"):
                            url_screenshot_filename = scan_output_base_file_dir + "/" + url.replace("http", "").replace("https", "") \
                                .replace("/", "_") \
                                .replace("\\", "") \
                                .replace(":", "_") + ".png"
                            url_screenshot_filename = url_screenshot_filename.replace("__", "")
                            db_path = (vhost, scanned_service_port, url, 0, url_screenshot_filename, workspace)
                            db.insert_new_path(db_path)
                            print("Found Url: " + str(url))
                            urls_to_screenshot_with_filenames.append((str(url), url_screenshot_filename))
                            urls_to_screenshot.append((str(url), url_screenshot_filename))


        except Exception, e:
            if not simulation:
                print("[!] Could not open {0}".format(post_photon_filename))



    if not simulation:
        if len(urls_to_screenshot) > 0:
            task_id = uuid()
            populated_command = "firefox-esr {0}-screenshots | {1} | {2}".format(screenshot_name, vhost, scan_output_base_file_dir)
            command_name = "Screenshots"
            #utils.create_task(command_name, populated_command, vhost, scan_output_base_file_dir, workspace, task_id)
            #cel_take_screenshot.delay(urls_to_screenshot_with_filenames,task_id,vhost,scan_output_base_file_dir, workspace,command_name,populated_command)

            #lib.scan.aquatone_host(urls_to_screenshot, vhost, workspace, simulation, scan_output_base_file_dir, celery_path)



@app.task()
def cel_create_task(*args,**kwargs):
    command_name, populated_command, ip, output_dir, workspace, task_id = args
    db_task = (task_id, 1, command_name, populated_command, ip, output_dir, 'SUBMITTED', workspace)
    db.create_task(db_task)
    #return populated_command


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

    print(populated_command)

    print("[+] Kicking off nmap scan for " + host)
    lib.db.update_task_status_started("STARTED", task_id, 0, start_time_int)
    nm = NmapProcess(host, options=config_nmap_options)
    rc = nm.run()
    nmap_report = NmapParser.parse(nm.stdout)
    end = timer()
    end_ctime = time.ctime(end)
    run_time = end - start
    db.update_task_status_completed("COMPLETED", task_id, run_time)

    #f.write("\n" + str(end_ctime) + "," + "CMD COMPLETED" + ","" + str(run_time) + " - " + populated_command + "\n")

    f.write(str(start_ctime)  + "," + str(end_ctime) + "," + str(run_time) + cmd_name + "\n")
    f.close()
    lib.csimport.process_nmap_data(nmap_report, workspace)
    return nmap_report



@app.task()
def cel_process_db_services(output_base_dir, simulation, workspace):
    lib.scan.process_db_services(output_base_dir, simulation, workspace)


