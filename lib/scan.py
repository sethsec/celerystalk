import os
from netaddr import *
import tasks
import sys
from lib import config_parser, utils, db
from celery.utils import uuid
from celery import chain
from ConfigParser import ConfigParser
import socket
import re
import urlparse
import lib.db
from random import shuffle

def process_db_vhosts(workspace, simulation, target_list=None):
    all_commands = []
    output_base_dir = lib.db.get_output_dir_for_workspace(workspace)[0][0]
    try:
        os.stat(output_base_dir)
    except:
        print("[+] Output directory does not exist. Creating " + output_base_dir)
        os.makedirs(output_base_dir)
    unique_unscanned_vhosts = db.get_inscope_unsubmitted_vhosts(workspace)
    unique_unscanned_vhosts_list = []
    [unique_unscanned_vhosts_list.append(i[0]) for i in unique_unscanned_vhosts] #converts list of tuples that contains the IPs, to a list of IPs

    if target_list:
        for vhost in target_list:
            for unscanned_vhost in unique_unscanned_vhosts_list:
                if str(vhost) == str(unscanned_vhost):
                    try:
                        IPAddress(vhost)
                        command_list = populate_comamnds(vhost, workspace, simulation, output_base_dir)
                    except:
                        command_list = populate_commands_vhost_http_https_only(vhost, workspace, simulation,output_base_dir)
                    if len(command_list) > 0:
                        print("Submitted [{1}] tasks for {0}".format(unscanned_vhost, len(command_list)))
                    all_commands = all_commands + command_list
    else:
        for vhost in unique_unscanned_vhosts_list:
            #print(vhost)
            try:
                IPAddress(vhost)
                command_list = populate_comamnds(vhost, workspace, simulation, output_base_dir)
            except:
                command_list = populate_commands_vhost_http_https_only(vhost, workspace, simulation, output_base_dir)
            if len(command_list) > 0:
                print("Submitted [{1}] tasks for {0}".format(vhost, len(command_list)))
            all_commands = all_commands + command_list

    shuffle(all_commands)
    for populated_command_tuple in all_commands:
        #print populated_command_tuple
        send_commands_to_celery(populated_command_tuple,output_base_dir,simulation)

    total_tasks_num = len(all_commands)
    if total_tasks_num > 0:
        print("\n\n[+] Summary:\tSubmitted {0} tasks to the [{1}] workspace.".format(total_tasks_num,workspace))
        print("[+]\t\tThere might be additional tasks added to the queue during post processing\n[+]")
        print("[+]\t\tTo keep an eye on things, run one of these commands: \n[+]")
        if workspace == "Default":
            print("[+]\t\tcelerystalk query [watch]")
            print("[+]\t\tcelerystalk query brief [watch]")
            print("[+]\t\tcelerystalk query summary [watch]\n")
        else:
            print("[+]\t\tcelerystalk query -w {0} [watch]".format(workspace))
            print("[+]\t\tcelerystalk query -w {0} brief [watch]".format(workspace))
            print("[+]\t\tcelerystalk query -w {0} summary [watch]\n".format(workspace))


def populate_comamnds(vhost,workspace,simulation,output_base_dir):
    celery_path = sys.path[0]
    config, supported_services = config_parser.read_config_ini()
    task_id_list = []
    populated_command_list = []
    total_tasks_num = 0
    vhost = str(vhost)
    vhost_ip = db.get_vhost_ip(vhost, workspace)[0]
    host_dir = output_base_dir + vhost
    host_data_dir = host_dir + "/celerystalkOutput/"
    # Creates something like /pentest/10.0.0.1, /pentest/10.0.0.2, etc.
    utils.create_dir_structure(vhost, host_dir)
    # Next two lines create the file that will contain each command that was executed. This is not the audit log,
    # but a log of commands that can easily be copy/pasted if you need to run them again.
    summary_file_name = host_data_dir + "ScanSummary.log"
    summary_file = open(summary_file_name, 'a')

    # THIS is just a work around until i have a real solution.  Really, UDP scans should be done
    # For every host in the scanned host list, launch a quick UDP scan (top 100 ports)
    scan_output_base_host_filename = host_data_dir + vhost

    ###################################
    # If enabled in config, run a udp scan against the host.
    ###################################


    for (cmd_name, cmd) in config.items("nmap-commands"):
        if cmd_name == "udp_scan":
            outfile = scan_output_base_host_filename + "_" + cmd_name
            populated_command = cmd.replace("[TARGET]", vhost).replace("[OUTPUT]", outfile)

            if simulation:
                populated_command = "#" + populated_command

            task_id = uuid()
            scanned_service_port = ""
            scanned_service_name = ""
            scanned_service_protocol = ""
            #utils.create_task(cmd_name, populated_command, vhost, outfile + ".txt", workspace, task_id)
            populated_command_list.append((cmd_name, populated_command, vhost, outfile + ".txt", workspace, task_id,scanned_service_port, scanned_service_name,scanned_service_protocol))

    if not simulation:
        db.update_vhosts_submitted(vhost_ip, vhost, workspace, 1)

    ###################################
    # Time to parse the services from the DB
    ###################################
    db_services = db.get_all_services_for_ip(vhost_ip[0], workspace)

    for db_service in db_services:
        (id, ip, scanned_service_port, scanned_service_protocol, scanned_service_name,
         workspace) = db_service

        scan_output_base_file_name = host_data_dir + vhost + "_" + str(
            scanned_service_port) + "_" + scanned_service_protocol + "_"

        # If the service name is not in the supported service list, give the user notice so they can add the service
        # and add some commands to the service. This is a major GAP right now. If the service is not in the config,
        # the script completely ignores it, which is not good!
        if scanned_service_name not in supported_services:
            print(
                "[!] Nmap reports {0}:{1} is running: [{2}]. There are no commands to run against {2} in config.ini.".format(
                    vhost, scanned_service_port, scanned_service_name))
            summary_file.write(
                "[!] Nmap reports {0}:{1} is running: [{2}]. There are no commands to run against {2} in config.ini\n".format(
                    vhost, scanned_service_port, scanned_service_name))
            # updated_port_scan = utils.nmap_follow_up_scan(vhost, scanned_service_port)
            # scanned_service_name = updated_port_scan.hosts[0]._services[0].service
            cmd_name = "nmap_service_scan"
            populated_command = 'nmap -sV -sC -Pn -p {0} -oN {1}_nmap_service_scan.txt {2}'.format(
                scanned_service_port, scan_output_base_file_name, vhost)
            if simulation:
                populated_command = "#" + populated_command

            outfile = scan_output_base_file_name + "_nmap_service_scan.txt"

            task_id = uuid()
            populated_command_list.append((cmd_name, populated_command, vhost, outfile, workspace, task_id,scanned_service_port, scanned_service_name,scanned_service_protocol))
        else:
            for (key, val) in config.items("nmap-service-names"):
                services = val.split(",")
                for service in services:
                    if service == scanned_service_name:
                        mapped_service_name = key
                        # print(config.items(mapped_service_name))
                        for (cmd_name, cmd) in config.items(mapped_service_name):
                            outfile = scan_output_base_file_name + cmd_name
                            populated_command = cmd.replace("[TARGET]", vhost).replace("[PORT]", str(
                                scanned_service_port)).replace("[OUTPUT]", outfile).replace("[PATH]",
                                                                                            "")
                            if simulation:
                                # debug - sends jobs to celery, but with a # in front of every one.
                                populated_command = "#" + populated_command

                            # Grab a UUID from celery.utils so that i can assign it to my task at init, which is amazing because
                            # that allows me to pass it to all of the tasks in the chain.

                            task_id = uuid()
                            populated_command_list.append((cmd_name, populated_command, vhost, outfile + ".txt",
                                              workspace, task_id,scanned_service_port, scanned_service_name,scanned_service_protocol))
    #print(populated_command_list.__len__())
    #print(populated_command_list)

    return populated_command_list

def send_commands_to_celery(populated_command_tuple,output_base_dir,simulation):

    celery_path = sys.path[0]
    cmd_name, populated_command, vhost, outfile, workspace, task_id,scanned_service_port, scanned_service_name,scanned_service_protocol = populated_command_tuple
    host_dir = output_base_dir + vhost
    host_data_dir = host_dir + "/celerystalkOutput/"

    utils.create_task(cmd_name, populated_command, vhost, outfile, workspace, task_id)
    result = chain(
        # insert a row into the database to mark the task as submitted. a subtask does not get tracked
        # in celery the same way a task does, for instance, you can't find it in flower
        # tasks.cel_create_task.subtask(args=(cmd_name, populated_command, ip, outfile + ".txt", workspace, task_id)),

        # run the command. run_task takes care of marking the task as started and then completed.
        # The si tells run_cmd to ignore the data returned from a previous task
        tasks.run_cmd.si(cmd_name, populated_command, celery_path, task_id).set(task_id=task_id),

        # right now, every executed command gets sent to a generic post_process task that can do
        # additinoal stuff based on the command that just ran.
        tasks.post_process.si(cmd_name, populated_command, output_base_dir, workspace, vhost, host_dir,
                              simulation,
                              scanned_service_port, scanned_service_name, scanned_service_protocol,
                              celery_path),
    )()  # .apply_async()

    #task_id_list.append(result.task_id)
    host_audit_log = host_dir + "/" + "{0}_executed_commands.txt".format(vhost)
    f = open(host_audit_log, 'a')
    f.write(populated_command + "\n\n")
    f.close()

def process_url(url, workspace, output_dir, arguments):
    celery_path = sys.path[0]
    config, supported_services = config_parser.read_config_ini()
    task_id_list = []
    urls_to_screenshot = []
    simulation = arguments["--simulation"]




    try:
        parsed_url = urlparse.urlparse(url)
        scheme = parsed_url[0]
        if not scheme:
            print("\n[!] URL parameter (-u) requires that you specify the scheme (http:// or https://)\n")
            exit()
        if ":" in parsed_url[1]:
            vhost, port = parsed_url[1].split(':')
        else:
            vhost = parsed_url[1]
            if scheme == "http":
                port = 80
            elif scheme == "https":
                port = 443
        path = parsed_url[2]
    except:
        if not scheme:
            exit()

    #get ip from db, or if not in db, get it through dns
    db_ip = lib.db.get_vhost_ip(vhost,workspace)
    if db_ip:
        ip = db_ip[0][0]
    else:
        try:
            ip = socket.gethostbyname(vhost)
        except:
            print("Error getting IP")
    proto = "tcp"

    if ip == vhost:
        scan_output_base_file_dir = output_dir + "/" + ip + "/celerystalkOutput/" + ip + "_" + str(
            port) + "_" + proto + "_"
    else:
        scan_output_base_file_dir = output_dir + "/" + ip + "/celerystalkOutput/" + vhost + "_" + str(
            port) + "_" + proto + "_"

    host_dir = output_dir + "/" + ip
    host_data_dir = host_dir + "/celerystalkOutput/"
    # Creates something like /pentest/10.0.0.1, /pentest/10.0.0.2, etc.
    utils.create_dir_structure(ip, host_dir)
    # Next two lines create the file that will contain each command that was executed. This is not the audit log,
    # but a log of commands that can easily be copy/pasted if you need to run them again.
    summary_file_name = host_data_dir + "ScanSummary.log"
    summary_file = open(summary_file_name, 'a')

    db_vhost = (ip, vhost, 1, 1, workspace)  # in this mode all vhosts are in scope
    # print(db_vhost)
    #create it if it doesnt exist (if it does, doing this doesnt change anything)
    db.create_vhost(db_vhost)
    # mark this host as in scope now
    lib.db.update_vhosts_in_scope(ip, vhost, workspace, 1)

    #only mark it as submitted if it is not in scope.
    if not simulation:
        lib.db.update_vhosts_submitted(ip, vhost, workspace, 1)

    # Insert port/service combo into services table if it doesnt exist
    db_service = db.get_service(ip, port, proto, workspace)
    if not db_service:
        db_string = (ip, port, proto, scheme, workspace)
        db.create_service(db_string)

    #mark this host as in scope now
    if not simulation:
        db.update_vhosts_submitted(vhost, vhost, workspace, 1)
# I might want to keep this, but i think it is redundant if we have gobuster and photon screenshots...
    # Insert url into paths table and take screenshot
    # db_path = db.get_path(path, workspace)
    # if not db_path:
    #     url_screenshot_filename = scan_output_base_file_dir + url.replace("http", "").replace("https", "") \
    #         .replace("/", "_") \
    #         .replace("\\", "") \
    #         .replace(":", "_") + ".png"
    #     url_screenshot_filename = url_screenshot_filename.replace("__", "")
    #     db_path = (ip, port, url, 0, url_screenshot_filename, workspace)
    #     db.insert_new_path(db_path)
    #     # print("Found Url: " + str(url))
    #     urls_to_screenshot.append((url, url_screenshot_filename))
    #     if not simulation:
    #         task_id = uuid()
    #         command_name = "Screenshots"
    #         populated_command = "firefox-esr URL mode screenshot | {0} | {1}".format(vhost,scan_output_base_file_dir)
    #         utils.create_task(command_name, populated_command, vhost, scan_output_base_file_dir, workspace, task_id)
    #         result = tasks.cel_take_screenshot.delay(urls_to_screenshot,task_id,vhost,scan_output_base_file_dir, workspace,command_name,populated_command)
    #     # print(result)

    # TODO: This def might introduce a bug - same code as parse config submit jobs to celery. need to just call that function here
    for section in config.sections():
        if (section == "http") or (section == "https"):
            if section == scheme:
                for (cmd_name, cmd) in config.items(section):
                    outfile = scan_output_base_file_dir + cmd_name
                    populated_command = cmd.replace("[TARGET]", vhost).replace("[PORT]",
                                                                                str(port)).replace("[OUTPUT]",
                                                                                                   outfile).replace(
                        "[PATH]", path)
                    if simulation:
                        # debug - sends jobs to celery, but with a # in front of every one.
                        populated_command = "#" + populated_command

                    # Grab a UUID from celery.utils so that i can assign it to my task at init, which is amazing because
                    # that allows me to pass it to all of the tasks in the chain.

                    task_id = uuid()
                    utils.create_task(cmd_name, populated_command, vhost, outfile + ".txt", workspace, task_id)
                    result = chain(
                        # insert a row into the database to mark the task as submitted. a subtask does not get tracked
                        # in celery the same way a task does, for instance, you can't find it in flower
                        # tasks.cel_create_task.subtask(args=(cmd_name,populated_command, vhost, outfile + ".txt", workspace, task_id)),

                        # run the command. run_task takes care of marking the task as started and then completed.
                        # The si tells run_cmd to ignore the data returned from a previous task
                        tasks.run_cmd.si(cmd_name, populated_command, celery_path, task_id).set(task_id=task_id),

                        # right now, every executed command gets sent to a generic post_process task that can do
                        # additinoal stuff based on the command that just ran.
                        tasks.post_process.si(cmd_name, populated_command, output_dir, workspace, vhost,
                                              host_dir,
                                              simulation, port, scheme, proto, celery_path),
                    )()  # .apply_async()

                    task_id_list.append(result.task_id)
                    host_audit_log = host_dir + "/" + "{0}_executed_commands.txt".format(ip)
                    f = open(host_audit_log, 'a')
                    f.write(populated_command + "\n\n")
                    f.close()
    print("[+] Submitted {0} tasks to queue.\n".format(len(task_id_list)))


def process_db_services(output_base_dir, simulation, workspace, target=None,host=None):
    celery_path = sys.path[0]
    config, supported_services = config_parser.read_config_ini()
    task_id_list = []
    total_tasks_num = 0
    if host:
        target = db.get_vhost_ip(host)
    try:
        os.stat(output_base_dir)
    except:
        print("[+] Output directory does not exist. Creating " + output_base_dir)
        os.makedirs(output_base_dir)
    #unique_hosts = db.get_unique_hosts(workspace)
    unique_unscanned_vhosts = db.get_inscope_unsubmitted_vhosts(workspace)
    for row in unique_unscanned_vhosts:

        vhost = row[0]
        #print("in proccess_db_services - vhost:" + vhost)
        vhost_ip = db.get_vhost_ip(vhost,workspace)[0]
        #print(target)
        #print(vhost_ip)
        #print(str(vhost_ip))

        if (IPAddress(vhost_ip[0]) == target) or (target is None):
            host_dir = output_base_dir + vhost
            host_data_dir = host_dir + "/celerystalkOutput/"
            # Creates something like /pentest/10.0.0.1, /pentest/10.0.0.2, etc.
            utils.create_dir_structure(vhost, host_dir)
            #Next two lines create the file that will contain each command that was executed. This is not the audit log,
            #but a log of commands that can easily be copy/pasted if you need to run them again.
            summary_file_name = host_data_dir + "ScanSummary.log"
            summary_file = open(summary_file_name, 'a')

            #THIS is just a work around until i have a real solution.  Really, UDP scans should be done
            #For every host in the scanned host list, launch a quick UDP scan (top 100 ports)
            scan_output_base_host_filename = host_data_dir + vhost

            for (cmd_name, cmd) in config.items("nmap-commands"):
                if cmd_name == "udp_scan":
                    #print(cmd_name,cmd)
                    outfile = scan_output_base_host_filename + "_" + cmd_name
                    populated_command = cmd.replace("[TARGET]", vhost).replace("[OUTPUT]", outfile)
                    #print(cmd)

                    #cmd_name = "udp-top100"
                    #populated_command = 'nmap -sV -sC -Pn -sU --top-ports 100 -oN {0}_nmap_UDP_service_scan.txt -oX {0}_nmap_UDP_service_scan.xml {1}'.format(
                    #    scan_output_base_host_filename, vhost)
                    if simulation:
                        populated_command = "#" + populated_command
                    #outfile = scan_output_base_host_filename + "_nmap_UDP_service_scan.txt"
                    task_id = uuid()
                    utils.create_task(cmd_name, populated_command, vhost, outfile + ".txt", workspace, task_id)
                    result = chain(
                        # insert a row into the database to mark the task as submitted. a subtask does not get tracked
                        # in celery the same way a task does, for instance, you can't find it in flower
                        #tasks.cel_create_task.subtask(args=(cmd_name, populated_command, vhost, outfile + ".txt", workspace, task_id)),

                        # run the command. run_task takes care of marking the task as started and then completed.
                        # The si tells run_cmd to ignore the data returned from a previous task
                        tasks.run_cmd.si(cmd_name, populated_command,celery_path,task_id).set(task_id=task_id),

                    )()  # .apply_async()
                    task_id_list.append(result.task_id)


            if not simulation:
                db.update_vhosts_submitted(vhost, vhost, workspace, 1)



            #print "IP Address: {0}".format(vhost)
            db_services = db.get_all_services_for_ip(vhost_ip[0], workspace)

            for db_service in db_services:
                (id,ip, scanned_service_port, scanned_service_protocol, scanned_service_name, workspace) = db_service

                scan_output_base_file_name = host_data_dir + vhost + "_" + str(scanned_service_port) + "_" + scanned_service_protocol + "_"

                #If the service name is not in the supported service list, give the user notice so they can add the service
                # and add some commands to the service. This is a major GAP right now. If the service is not in the config,
                # the script completely ignores it, which is not good!
                if scanned_service_name not in supported_services:
                    print("[!] Nmap reports {0}:{1} is running: [{2}]. There are no commands to run against {2} in config.ini.".format(vhost, scanned_service_port, scanned_service_name))
                    summary_file.write("[!] Nmap reports {0}:{1} is running: [{2}]. There are no commands to run against {2} in config.ini\n".format(vhost, scanned_service_port, scanned_service_name))
                    #updated_port_scan = utils.nmap_follow_up_scan(vhost, scanned_service_port)
                    #scanned_service_name = updated_port_scan.hosts[0]._services[0].service
                    cmd_name = "nmap_service_scan"
                    populated_command = 'nmap -sV -sC -Pn -p {0} -oN {1}_nmap_service_scan.txt {2}'.format(
                        scanned_service_port, scan_output_base_file_name, vhost)
                    if simulation:
                        populated_command = "#" + populated_command

                    outfile = scan_output_base_file_name + "_nmap_service_scan.txt"

                    task_id = uuid()
                    utils.create_task(cmd_name, populated_command, vhost, outfile , workspace, task_id)
                    result = chain(
                        # insert a row into the database to mark the task as submitted. a subtask does not get tracked
                        # in celery the same way a task does, for instance, you can't find it in flower
                        #tasks.cel_create_task.subtask(args=(cmd_name, populated_command, vhost, outfile , workspace, task_id)),

                        # run the command. run_task takes care of marking the task as started and then completed.
                        # The si tells run_cmd to ignore the data returned from a previous task
                        tasks.run_cmd.si(cmd_name, populated_command,celery_path,task_id).set(task_id=task_id),

                    )()  # .apply_async()

                    task_id_list.append(result.task_id)
                else:
                    parse_config_and_send_commands_to_celery(scanned_service_name, scanned_service_port, scan_output_base_file_name, config, simulation, output_base_dir, host_dir, workspace, task_id_list,vhost,scanned_service_protocol)
                #task_id_list = task_id_list + new_tasks_list
            summary_file.close()

            print("[+] Submitted {0} tasks to the queue.".format(len(task_id_list)))
            total_tasks_num = total_tasks_num + len(task_id_list)
            task_id_list = []
    print("\n\n[+] Summary:\tSubmitted {0} tasks to the [{1}] workspace.".format(total_tasks_num,workspace))
    print("[+]\t\tThere might be additional tasks added to the queue during post processing\n[+]")
    print("[+]\t\tTo keep an eye on things, run one of these commands: \n[+]")
    if workspace == "Default":
        print("[+]\t\tcelerystalk query [watch]")
        print("[+]\t\tcelerystalk query brief [watch]")
        print("[+]\t\tcelerystalk query summary [watch]\n")
    else:
        print("[+]\t\tcelerystalk query -w {0} [watch]".format(workspace))
        print("[+]\t\tcelerystalk query -w {0} brief [watch]".format(workspace))
        print("[+]\t\tcelerystalk query -w {0} summary [watch]\n".format(workspace))


def parse_config_and_send_commands_to_celery(scanned_service_name, scanned_service_port, scan_output_base_file_name, config, simulation, output_base_dir, host_dir, workspace, task_id_list,ip,scanned_service_protocol):
    """

    :param scanned_service_name:
    :param scanned_service_port:
    :param scan_output_base_file_name:
    :param json_config:
    :param summary_file:
    :param simulation:
    :param output_base_dir:
    :param host_dir:
    :param workspace:
    :param task_id_list:
    :param ip:
    :return:
    """
    celery_path = sys.path[0]

    for (key, val) in config.items("nmap-service-names"):
        services = val.split(",")
        for service in services:
            if service == scanned_service_name:
                mapped_service_name = key
                #print(config.items(mapped_service_name))
                for (cmd_name, cmd) in config.items(mapped_service_name):
                    outfile = scan_output_base_file_name + cmd_name
                    populated_command = cmd.replace("[TARGET]", ip).replace("[PORT]", str(scanned_service_port)).replace("[OUTPUT]", outfile).replace("[PATH]", "")
                    if simulation:
                        #debug - sends jobs to celery, but with a # in front of every one.
                        populated_command = "#" + populated_command

                    # Grab a UUID from celery.utils so that i can assign it to my task at init, which is amazing because
                    # that allows me to pass it to all of the tasks in the chain.

                    task_id = uuid()
                    utils.create_task(cmd_name, populated_command, ip, outfile + ".txt", workspace, task_id)
                    result = chain(
                        # insert a row into the database to mark the task as submitted. a subtask does not get tracked
                        # in celery the same way a task does, for instance, you can't find it in flower
                        #tasks.cel_create_task.subtask(args=(cmd_name, populated_command, ip, outfile + ".txt", workspace, task_id)),

                        # run the command. run_task takes care of marking the task as started and then completed.
                        # The si tells run_cmd to ignore the data returned from a previous task
                        tasks.run_cmd.si(cmd_name, populated_command,celery_path,task_id).set(task_id=task_id),

                        # right now, every executed command gets sent to a generic post_process task that can do
                        # additinoal stuff based on the command that just ran.
                        tasks.post_process.si(cmd_name, populated_command, output_base_dir, workspace, ip, host_dir, simulation,
                                        scanned_service_port, scanned_service_name, scanned_service_protocol,celery_path),
                    )()  # .apply_async()

                    task_id_list.append(result.task_id)
                    host_audit_log = host_dir + "/" + "{0}_executed_commands.txt".format(ip)
                    f = open(host_audit_log, 'a')
                    f.write(populated_command + "\n\n")
                    f.close()


def create_dns_recon_tasks(domains,simulation,workspace,output_base_dir,scan_mode=None,out_of_scope_hosts=None):
    config, supported_services = config_parser.read_config_ini()
    celery_path = sys.path[0]
    for domain in domains.split(","):
        for section in config.sections():
            if section == "domain-recon":
                for (cmd_name, cmd) in config.items(section):
                    outfile = output_base_dir + domain + "_" + cmd_name
                    populated_command = cmd.replace("[DOMAIN]", domain).replace("[OUTPUT]", outfile)
                    if simulation:
                        populated_command = "#" + populated_command
                    print(populated_command)

                    # Grab a UUID from celery.utils so that i can assign it to my task at init, which is amazing because
                    # that allows me to pass it to all of the tasks in the chain.
                    task_id = uuid()
                    utils.create_task(cmd_name, populated_command, domain, "", workspace, task_id)
                    process_domain_tuple = (cmd_name, populated_command, output_base_dir, workspace, domain, simulation, celery_path, scan_mode)
                    if scan_mode == "VAPT":
                        result = chain(
                            # insert a row into the database to mark the task as submitted. a subtask does not get tracked
                            # in celery the same way a task does, for instance, you can't find it in flower
                            #tasks.cel_create_task.subtask(args=(cmd_name, populated_command, domain, "", workspace, task_id)),

                            # run the command. run_task takes care of marking the task as started and then completed.
                            # The si tells run_cmd to ignore the data returned from a previous task
                            tasks.run_cmd.si(cmd_name, populated_command,celery_path,task_id,process_domain_tuple=process_domain_tuple).set(task_id=task_id),

                            # right now, every executed command gets sent to a generic post_process task that can do
                            # additinoal stuff based on the command that just ran.
                            #tasks.post_process_domains.s(cmd_name, populated_command, output_base_dir, workspace, domain, simulation,celery_path,scan_mode),
                        )()  # .apply_async()
                    else:
                        result = chain(
                            #tasks.cel_create_task.subtask(args=(cmd_name, populated_command, domain, "", workspace, task_id)),
                            tasks.run_cmd.si(cmd_name, populated_command, celery_path, task_id).set(task_id=task_id),
                            tasks.post_process_domains_bb.s(cmd_name, populated_command, output_base_dir, workspace,
                                                         domain, simulation, celery_path,out_of_scope_hosts),
                        )()


def determine_if_domains_are_in_scope(vhosts,process_domain_tuple):
    command_name, populated_command, output_base_dir, workspace, domain, simulation, celery_path, scan_mode = process_domain_tuple
    config,supported_services = config_parser.read_config_ini()
    vhosts = vhosts.splitlines()
    # from https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    for vhost in vhosts:
        #print("raw:\t" + vhost)
        vhost = ansi_escape.sub('', vhost)
        #print("escaped:\t" + vhost)
        if re.match(r'\w', vhost):
            in_scope,ip = utils.domain_scope_checker(vhost,workspace)
            if in_scope == 1:
                print("Found subdomain (in scope):\t" + vhost)
                db_vhost = (ip,vhost,1, 0,workspace)
                db.create_vhost(db_vhost)
            else:
                print("Found subdomain (out of scope):\t" + vhost)
                db_vhost = (ip, vhost, 0, 0, workspace)
                db.create_vhost(db_vhost)

def populate_commands_vhost_http_https_only(vhost, workspace, simulation, output_base_dir):
    #pull all in scope vhosts that have not been submitted
    celery_path = sys.path[0]
    config, supported_services = config_parser.read_config_ini()
    task_id_list = []
    populated_command_list = []
    total_tasks_num = 0
    vhost = str(vhost)
    vhost_ip = db.get_vhost_ip(vhost, workspace)[0][0]
    host_dir = output_base_dir + vhost
    host_data_dir = host_dir + "/celerystalkOutput/"
    # Creates something like /pentest/10.0.0.1, /pentest/10.0.0.2, etc.
    utils.create_dir_structure(vhost, host_dir)
    # Next two lines create the file that will contain each command that was executed. This is not the audit log,
    # but a log of commands that can easily be copy/pasted if you need to run them again.
    summary_file_name = host_data_dir + "ScanSummary.log"
    summary_file = open(summary_file_name, 'a')


    scannable_vhost = vhost
    ip = db.get_vhost_ip(scannable_vhost, workspace)
    ip = ip[0][0]
    db_scanned_services = db.get_all_services_for_ip(ip, workspace)
    for (id,ip,scanned_service_port,scanned_service_protocol,scanned_service_name,workspace) in db_scanned_services:
    #run chain on each one and then update db as submitted
        scan_output_base_file_name = output_base_dir + "/" + ip + "/celerystalkOutput/" + scannable_vhost + "_" +  str(scanned_service_port) + "_" + scanned_service_protocol + "_"
        host_dir = output_base_dir + "/" + ip

        #TODO: This def might introduce a bug - same code as parse config submit jobs to celery. need to just call that function here
        for section in config.sections():
            if (section == "http") or (section == "https"):
                if section == scanned_service_name:
                    for (cmd_name, cmd) in config.items(section):
                        outfile = scan_output_base_file_name + cmd_name
                        populated_command = cmd.replace("[TARGET]", scannable_vhost).replace("[PORT]",
                            str(scanned_service_port)).replace("[OUTPUT]", outfile).replace("[PATH]", "")
                        if simulation:
                            # debug - sends jobs to celery, but with a # in front of every one.
                            populated_command = "#" + populated_command

                        # Grab a UUID from celery.utils so that i can assign it to my task at init, which is amazing because
                        # that allows me to pass it to all of the tasks in the chain.

                        task_id = uuid()
                        populated_command_list.append((cmd_name, populated_command, vhost, outfile + ".txt",
                                          workspace, task_id,scanned_service_port, scanned_service_name,scanned_service_protocol))

    if not simulation:
        db.update_vhosts_submitted(vhost_ip, vhost, workspace, 1)
    return populated_command_list


    # inscope_vhosts = db.get_inscope_unsubmitted_vhosts(workspace)
    # for scannable_vhost in inscope_vhosts:
    #     scannable_vhost = scannable_vhost[0]
    #     ip = db.get_vhost_ip(scannable_vhost,workspace)
    #     ip = ip[0][0]
    #     db_scanned_services = db.get_all_services_for_ip(ip, workspace)
    #
    #
    #     for (id,ip,scanned_service_port,scanned_service_protocol,scanned_service_name,workspace) in db_scanned_services:
    #     #run chain on each one and then update db as submitted
    #         scan_output_base_file_name = output_base_dir + "/" + ip + "/celerystalkOutput/" + scannable_vhost + "_" +  str(scanned_service_port) + "_" + scanned_service_protocol + "_"
    #         host_dir = output_base_dir + "/" + ip
    #
    #         #TODO: This def might introduce a bug - same code as parse config submit jobs to celery. need to just call that function here
    #         for section in config.sections():
    #             if (section == "http") or (section == "https"):
    #                 if section == scanned_service_name:
    #                     for (cmd_name, cmd) in config.items(section):
    #                         outfile = scan_output_base_file_name + cmd_name
    #                         populated_command = cmd.replace("[TARGET]", scannable_vhost).replace("[PORT]",
    #                             str(scanned_service_port)).replace("[OUTPUT]", outfile).replace("[PATH]", "")
    #                         if simulation:
    #                             # debug - sends jobs to celery, but with a # in front of every one.
    #                             populated_command = "#" + populated_command
    #
    #                         # Grab a UUID from celery.utils so that i can assign it to my task at init, which is amazing because
    #                         # that allows me to pass it to all of the tasks in the chain.
    #
    #                         task_id = uuid()
    #                         populated_command_list.append((cmd_name, populated_command, vhost, outfile + ".txt",
    #                                           workspace, task_id,scanned_service_port, scanned_service_name,scanned_service_protocol))
    # return populated_command_list
        #                     utils.create_task(cmd_name, populated_command, scannable_vhost, outfile + ".txt", workspace, task_id)
        #
        #
        #                     result = chain(
        #                         # insert a row into the database to mark the task as submitted. a subtask does not get tracked
        #                         # in celery the same way a task does, for instance, you can't find it in flower
        #                         #tasks.cel_create_task.subtask(args=(cmd_name,populated_command, scannable_vhost, outfile + ".txt", workspace, task_id)),
        #
        #                         # run the command. run_task takes care of marking the task as started and then completed.
        #                         # The si tells run_cmd to ignore the data returned from a previous task
        #                         tasks.run_cmd.si(cmd_name, populated_command, celery_path, task_id).set(task_id=task_id),
        #
        #                         # right now, every executed command gets sent to a generic post_process task that can do
        #                         # additinoal stuff based on the command that just ran.
        #                         tasks.post_process.si(cmd_name, populated_command, output_base_dir, workspace, scannable_vhost, host_dir,
        #                                               simulation,
        #                                               scanned_service_port, scanned_service_name,
        #                                               scanned_service_protocol,celery_path),
        #                     )()  # .apply_async()
        #
        #                     #task_id_list.append(result.task_id)
        #                     host_audit_log = host_dir + "/" + "{0}_executed_commands.txt".format(ip)
        #                     f = open(host_audit_log, 'a')
        #                     f.write(populated_command + "\n\n")
        #                     f.close()
        #
        # db.update_vhosts_submitted(ip,scannable_vhost,workspace,1)


def nmap_scan_subdomain_host(host,workspace,simulation,output_base_dir):
    celery_path = sys.path[0]
    config_nmap_options = config_parser.extract_bb_nmap_options()
    config = ConfigParser(allow_no_value=True)
    config.read(['config.ini'])


    #print(config_nmap_options)
    cmd_name = "nmap_bug_bounty_mode"
    populated_command = "nmap " + host + config_nmap_options
    task_id = uuid()
    utils.create_task(cmd_name, populated_command, host, output_base_dir, workspace, task_id)
    result = chain(
        #tasks.cel_create_task.subtask(args=(cmd_name, populated_command, host, output_base_dir, workspace, task_id)),
        tasks.cel_nmap_scan.si(cmd_name, populated_command, host, config_nmap_options, celery_path, task_id,workspace).set(task_id=task_id),
        tasks.cel_scan_process_nmap_data.s(workspace),
        tasks.cel_process_db_services.si(output_base_dir, simulation, workspace,host=host),
        tasks.post_process_domains_bb.si(host,cmd_name, populated_command, output_base_dir, workspace,simulation, celery_path),
    )()



