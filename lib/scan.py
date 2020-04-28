import os
from netaddr import *
import tasks
import sys
from lib import config_parser, utils, db
from celery.utils import uuid
from celery import chain
import socket
import re
import urlparse
import lib.db
from random import shuffle


def process_db_vhosts(workspace, simulation, target_list=None,dont_scan_ips=None,config_file=None):
    workspace_mode = lib.db.get_workspace_mode(workspace)[0][0]
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
            #TODO: try this: if vhost in unique_unscanned_vhosts_list:
            for unscanned_vhost in unique_unscanned_vhosts_list:
                if str(vhost) == str(unscanned_vhost):
                    vhost_explicitly_out_of_scope = lib.db.is_vhost_explicitly_out_of_scope(str(vhost), workspace)
                    if not vhost_explicitly_out_of_scope:
                        try:
                            IPAddress(vhost)
                            if not dont_scan_ips:
                                command_list = populate_comamnds(vhost, workspace, simulation, output_base_dir,config_file=config_file)
                        except:
                            command_list = populate_commands_vhost_http_https_only(vhost, workspace, simulation,output_base_dir,config_file=config_file)
                        if len(command_list) > 0:
                            print("Submitted [{1}] tasks for {0}".format(unscanned_vhost, len(command_list)))
                        all_commands = all_commands + command_list
    else:
        for vhost in unique_unscanned_vhosts_list:
            command_list = []
            #print(vhost)
            vhost_explicitly_out_of_scope = lib.db.is_vhost_explicitly_out_of_scope(vhost, workspace)
            if not vhost_explicitly_out_of_scope:
                try:
                    IPAddress(vhost)
                    if not dont_scan_ips:
                        command_list = populate_comamnds(vhost, workspace, simulation, output_base_dir,config_file=config_file)
                        if len(command_list) > 0:
                            print("Submitted [{1}] tasks for {0}".format(vhost, len(command_list)))
                except:
                    command_list = populate_commands_vhost_http_https_only(vhost, workspace, simulation, output_base_dir,config_file=config_file)
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
        print("[+]\t\tcelerystalk query [watch]")
        print("[+]\t\tcelerystalk query brief [watch]")
        print("[+]\t\tcelerystalk query summary [watch]\n")

def replace_user_config_options(config_file,populated_command):
    rep = lib.config_parser.get_user_config(config_file)
    rep = dict((k, v) for k, v in rep)
    for k,v in rep.iteritems():
        k = k.upper()
        populated_command = populated_command.replace("[" + k + "]",v)
    return populated_command

def aquatone_host(urls_to_screenshot,vhost,workspace,simulation,scan_output_base_file_dir,celery_path,config_file=None):
    print("in aquatone host")
    celery_path = lib.db.get_current_install_path()[0][0]
    config, supported_services = config_parser.read_config_ini(config_file)
    for (cmd_name, cmd) in config.items("screenshots"):
        #print(cmd_name, cmd)
        try:
            if cmd_name == "aquatone":
                outfile = scan_output_base_file_dir + "_" + cmd_name
                filename = "/tmp/" + workspace + "_paths_" + vhost + ".txt"
                populated_command = cmd.replace("[FILE]", filename).replace("[OUTPUT]", outfile)
                populated_command = replace_user_config_options(config_file,populated_command)

                paths = lib.db.get_all_paths_for_host_path_only(vhost,workspace)
                print(str(paths))


                with open(filename, 'w') as paths_tmp_file:
                    #paths_tmp_file.write(str(paths))
                    for line in paths:
                         #print(str(line))
                         paths_tmp_file.write(str(line[0]) + "\n")

                populated_command = cmd.replace("[FILE]", filename).replace("[OUTPUT]", outfile)
                populated_command = replace_user_config_options(config_file,populated_command)

                #print(populated_command)
        except Exception, e:
            print(e)
            print("[!] Error: In the config file, there needs to be one (and only one) enabled aquatone command.")
            exit()


        task_id = uuid()
        utils.create_task(cmd_name, populated_command, vhost, outfile + "/aquatone_report.html", workspace, task_id)
        result = chain(
            tasks.run_cmd.si(cmd_name, populated_command, celery_path, task_id).set(task_id=task_id),
        )()


def populate_comamnds(vhost,workspace,simulation,output_base_dir,config_file=None):
    workspace_mode = lib.db.get_workspace_mode(workspace)[0][0]
    celery_path = sys.path[0]
    config, supported_services = config_parser.read_config_ini(config_file)
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
            populated_command = replace_user_config_options(config_file, populated_command)

            if simulation:
                populated_command = "#" + populated_command


            task_id = uuid()
            scanned_service_port = ""
            scanned_service_name = ""
            scanned_service_protocol = ""
            #utils.create_task(cmd_name, populated_command, vhost, outfile + ".txt", workspace, task_id)
            populated_command_list.append((cmd_name, populated_command, vhost, outfile + ".txt", workspace, task_id,scanned_service_port, scanned_service_name,scanned_service_protocol))

    if not simulation:
        db.update_vhosts_submitted(vhost_ip[0], vhost, workspace, 1)

    ###################################
    # Time to parse the services from the DB
    ###################################

    if workspace_mode == "vapt":
        db_services = db.get_all_services_for_ip(vhost_ip[0], workspace)
    elif workspace_mode == "bb":
        db_services = db.get_all_services_for_ip(vhost, workspace)

    for db_service in db_services:
        (ip, scanned_service_port, scanned_service_protocol, scanned_service_name,product,version,extra_info) = db_service

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
            populated_command = replace_user_config_options(config_file, populated_command)

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
                                scanned_service_port)).replace("[OUTPUT]", outfile).replace("/[PATH]",
                                                                                            "")
                            populated_command = replace_user_config_options(config_file, populated_command)

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
    )()  # .apply_async()

    #task_id_list.append(result.task_id)
    host_audit_log = host_dir + "/" + "{0}_executed_commands.txt".format(vhost)
    f = open(host_audit_log, 'a')
    f.write(populated_command + "\n\n")
    f.close()



def process_url_param(url, workspace, output_dir, arguments,config_file=None):
    celery_path = sys.path[0]
    config, supported_services = config_parser.read_config_ini(config_file)
    task_id_list = []
    urls_to_screenshot = []
    simulation = arguments["--simulation"]


    if os.path.isfile(url):
        with open(url) as urls_file:
            for line in urls_file:
                line = line.rstrip()
                process_url(line, workspace, output_dir, arguments, config_file)
    else:
        process_url(url, workspace, output_dir, arguments, config_file)


def process_url(url, workspace, output_dir, arguments,config_file=None):
    celery_path = sys.path[0]
    config, supported_services = config_parser.read_config_ini(config_file)
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
        path = parsed_url[2].replace("//", "/")
    except:
        if not scheme:
            exit()

    try:
        ip = socket.gethostbyname(vhost)
    except:
        print("Error getting IP")
        ip=False


    db_ip_tuple = lib.db.get_vhost_ip(vhost,workspace)
    if db_ip_tuple:
        db_ip = db_ip_tuple[0][0]
        if db_ip != ip:
            lib.db.update_vhost_ip(ip, vhost, workspace)


    proto = "tcp"
    vhost_explicitly_out_of_scope = lib.db.is_vhost_explicitly_out_of_scope(vhost, workspace)
    if not vhost_explicitly_out_of_scope:  # and if the vhost is not explicitly out of scope
        if not ip:
            exit()
        elif ip == vhost:
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

        is_vhost_in_db = lib.db.is_vhost_in_db(vhost, workspace)
        if is_vhost_in_db:
            lib.db.update_vhosts_in_scope(ip, vhost, workspace, 1)
        else:
            db_vhost = (ip, vhost, 1, 0, 1, workspace)  # add it to the vhosts db and mark as in scope
            lib.db.create_vhost(db_vhost)


        #only mark it as submitted if it is not in scope.
        if not simulation:
            lib.db.update_vhosts_submitted(ip, vhost, workspace, 1)

        # Insert port/service combo into services table if it doesnt exist
        db_service = db.get_service(ip, port, proto, workspace)
        if not db_service:
            db_string = (ip, port, proto, scheme,'','','',workspace)
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
                        path_for_filename = path.replace("/","_")
                        outfile = scan_output_base_file_dir + path_for_filename  + "_" + cmd_name
                        populated_command = cmd.replace("[TARGET]", vhost).replace("[PORT]",
                                                                                    str(port)).replace("[OUTPUT]",
                                                                                                       outfile).replace(
                            "/[PATH]", path)
                        populated_command = replace_user_config_options(config_file, populated_command)

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
                        )()  # .apply_async()

                        task_id_list.append(result.task_id)
                        host_audit_log = host_dir + "/" + "{0}_executed_commands.txt".format(ip)
                        f = open(host_audit_log, 'a')
                        f.write(populated_command + "\n\n")
                        f.close()
        print("[+] Submitted {0} tasks to queue for {1}.".format(len(task_id_list),url))
    else:
        print("[!] {0} is explicitly marked as out of scope. Skipping...".format(vhost))



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
                    populated_command = cmd.replace("[TARGET]", ip).replace("[PORT]", str(scanned_service_port)).replace("[OUTPUT]", outfile).replace("/[PATH]", "")
                    populated_command = replace_user_config_options(config_file, populated_command)

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
                    )()  # .apply_async()

                    task_id_list.append(result.task_id)
                    host_audit_log = host_dir + "/" + "{0}_executed_commands.txt".format(ip)
                    f = open(host_audit_log, 'a')
                    f.write(populated_command + "\n\n")
                    f.close()


def create_dns_recon_tasks(domains,simulation,workspace,output_base_dir,out_of_scope_hosts=None,config_file=None):
    workspace_mode = lib.db.get_workspace_mode(workspace)[0][0]
    task_id_list = []
    total_tasks_num = 0
    config, supported_services = config_parser.read_config_ini(config_file)
    celery_path = sys.path[0]
    for domain in domains.split(","):
        for section in config.sections():
            if section == "domain-recon":
                for (cmd_name, cmd) in config.items(section):
                    outfile = output_base_dir + domain + "_" + cmd_name
                    populated_command = cmd.replace("[DOMAIN]", domain).replace("[OUTPUT]", outfile)
                    populated_command = replace_user_config_options(config_file, populated_command)

                    if simulation:
                        populated_command = "#" + populated_command
                    #print(populated_command)

                    # Grab a UUID from celery.utils so that i can assign it to my task at init, which is amazing because
                    # that allows me to pass it to all of the tasks in the chain.
                    task_id = uuid()
                    utils.create_task(cmd_name, populated_command, domain, outfile + ".txt", workspace, task_id)
                    process_domain_tuple = (cmd_name, populated_command, output_base_dir, workspace, domain, simulation, celery_path, workspace_mode)
                    result = chain(
                        # insert a row into the database to mark the task as submitted. a subtask does not get tracked
                        # in celery the same way a task does, for instance, you can't find it in flower
                        #tasks.cel_create_task.subtask(args=(cmd_name, populated_command, domain, "", workspace, task_id)),

                        # run the command. run_task takes care of marking the task as started and then completed.
                        # The si tells run_cmd to ignore the data returned from a previous task
                        tasks.run_cmd.si(cmd_name, populated_command,celery_path,task_id,process_domain_tuple=process_domain_tuple).set(task_id=task_id),
                    )()  # .apply_async()

    total_tasks_num = total_tasks_num + len(task_id_list)
    print("\n\n[+] Summary:\tSubmitted {0} tasks to the [{1}] workspace.".format(total_tasks_num, workspace))
    print("[+]\t\tThere might be additional tasks added to the queue during post processing\n[+]")
    print("[+]\t\tTo keep an eye on things, run one of these commands: \n[+]")
    print("[+]\t\tcelerystalk query [watch]")
    print("[+]\t\tcelerystalk query brief [watch]")
    print("[+]\t\tcelerystalk query summary [watch]\n")


def determine_if_domains_are_in_scope(vhosts,process_domain_tuple):
    command_name, populated_command, output_base_dir, workspace, domain, simulation, celery_path, scan_mode = process_domain_tuple
    workspace_mode = lib.db.get_workspace_mode(workspace)[0][0]
    vhosts = vhosts.splitlines()

    # from https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    for vhost in vhosts:
        #This checks for spaces in vhosts and is a dirty way to filter out error messages and other stuff.
        if ' ' not in vhost:
            #print("raw:\t" + vhost)
            vhost = ansi_escape.sub('', vhost)
            #print("escaped:\t" + vhost)
            if re.match(r'\w', vhost):
                in_scope, ip = utils.domain_scope_checker(vhost, workspace)
                if workspace_mode == "vapt":
                    if in_scope == 1:
                        print("Found subdomain (in scope):\t" + vhost)
                        is_vhost_in_db = lib.db.is_vhost_in_db(vhost, workspace)
                        if is_vhost_in_db:
                            lib.db.update_vhosts_in_scope(ip, vhost, workspace, 1)
                        else:
                            db_vhost = (ip, vhost, 1, 0, 0, workspace)  # add it to the vhosts db and mark as in scope
                            lib.db.create_vhost(db_vhost)
                    else:
                        print("Found subdomain (out of scope):\t" + vhost)
                        is_vhost_in_db = lib.db.is_vhost_in_db(vhost, workspace)
                        if is_vhost_in_db:
                            lib.db.update_vhosts_in_scope(ip, vhost, workspace, 0)
                        else:
                            db_vhost = (ip, vhost, 0, 0, 0, workspace)  # add it to the vhosts db and mark as out of scope
                            lib.db.create_vhost(db_vhost)
                elif workspace_mode == "bb":
                    print("Found subdomain (in scope):\t" + vhost)
                    is_vhost_in_db = lib.db.is_vhost_in_db(vhost, workspace)
                    if is_vhost_in_db:
                        lib.db.update_vhosts_in_scope(ip, vhost, workspace, 1)
                    else:
                        db_vhost = (ip, vhost, 1, 0, 0, workspace)  # add it to the vhosts db and mark as in scope
                        lib.db.create_vhost(db_vhost)


def populate_commands_vhost_http_https_only(vhost, workspace, simulation, output_base_dir,config_file=None):
    workspace_mode = lib.db.get_workspace_mode(workspace)[0][0]
    #pull all in scope vhosts that have not been submitted
    celery_path = sys.path[0]
    config, supported_services = config_parser.read_config_ini(config_file)
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


    if workspace_mode == "vapt":
        db_scanned_services = db.get_all_services_for_ip(ip, workspace)
    elif workspace_mode == "bb":
        db_scanned_services = db.get_all_services_for_ip(vhost, workspace)


    #db_scanned_services = db.get_all_services_for_ip(ip, workspace)
    for (ip, scanned_service_port, scanned_service_protocol, scanned_service_name,product,version,extra_info) in db_scanned_services:
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
                            str(scanned_service_port)).replace("[OUTPUT]", outfile).replace("/[PATH]", "")
                        populated_command = replace_user_config_options(config_file, populated_command)

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



