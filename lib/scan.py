import os

from netaddr import IPAddress

import tasks
import sys
from lib import config_parser, utils, db
from celery.utils import uuid
from celery import chain
from ConfigParser import ConfigParser
import socket
import re
import urlparse


def process_nessus_data2(nessus_report,workspace,target=None):
    for scanned_host in nessus_report.hosts:
        #print scanned_host.address
        ip = scanned_host.address
        # this if takes care of only acting on the targets specififed at hte command line, if the target
        # this if takes care of only acting on the targets specififed at hte command line, if the target
        # param is used.  This is a very simple comparison now. In the future, i'd like to be able to use
        # the target splitter function and be able to handle ranges and cidr's in the target option
        if (IPAddress(ip) == target) or (target is None):
            has_vhost_been_scanned = db.get_inscope_submitted_vhosts_for_ip(ip, workspace)
            if has_vhost_been_scanned:
                answer = raw_input("[!] {0} has already been scanned. Scan it, and all vhosts associated with it, again? [Y\\n] ".format(ip))
                if (answer == "Y") or (answer == "y") or (answer == ""):
                    db.update_vhosts_submitted(ip, ip, workspace, 0)
            else:
                db_vhost = (ip, ip, 1, 0, workspace)  # in this mode all vhosts are in scope
                #print(db_vhost)
                db.create_vhost(db_vhost)
            # Step 1: pull all report items in the port scanner family to get every port. The services names are IANA
            #         default as this point, which is why we need the next two loops.
            for report_item in scanned_host.get_report_items:
                if report_item.plugin_family == "Port scanners":
                    scanned_service_port = report_item.port
                    scanned_service_protocol = report_item.protocol
                    scanned_service_name = report_item.service
                    db_service = db.get_service(ip,scanned_service_port,scanned_service_protocol,workspace)

                    if not db_service:
                        db_string = (ip,scanned_service_port,scanned_service_protocol,scanned_service_name,workspace)
                        db.create_service(db_string)

            # Step 2: Cycle through the service detection items and update the services where we have a better idea of
            #         the real running service on the port. These are a subset of open ports which is why we need loop 1
            for report_item in scanned_host.get_report_items:
                if report_item.plugin_family == "Service detection":
                    scanned_service_port = report_item.port
                    scanned_service_protocol = report_item.protocol
                    scanned_service_name = report_item.service
                    db_service = db.get_service(ip,scanned_service_port,scanned_service_protocol,workspace)
                    if not db_service:
                        db_string = (ip, scanned_service_port, scanned_service_protocol, scanned_service_name, workspace)
                        db.create_service(db_string)
                        #print("new service2: " + ip,scanned_service_port,scanned_service_name)
                    else:
                        db.update_service(ip,scanned_service_port,scanned_service_protocol,scanned_service_name,workspace)
                        #print("updating service servicename2: " + ip, scanned_service_port, scanned_service_name)
                        #print("old service servicename2     : " + ip, scanned_service_port,str(db_service[0][4]))

            # Step 3: This is needed to split up HTTPS from HTTP
            for report_item in scanned_host.get_report_items:
                if (report_item.plugin_name == "TLS Version 1.0 Protocol Detection" or
                report_item.plugin_name == "OpenSSL Detection" or
                report_item.plugin_name == "SSL Version 2 and 3 Protocol Detection"):
                    scanned_service_port = report_item.port
                    scanned_service_protocol = report_item.protocol
                    scanned_service_name = 'https'
                    try:
                        db.update_service(ip, scanned_service_port, scanned_service_protocol, scanned_service_name,
                                          workspace)
                    except:
                        print("if this errors that means there was no service to update as https which is a bigger problem")

def process_nmap_data2(nmap_report,workspace, target=None):
    for scanned_host in nmap_report.hosts:

        #print(scanned_host)
        ip=scanned_host.id
        #print(ip)
        if (IPAddress(ip) == target) or (target is None):
            #has_vhost_been_scanned = db.get_unique_inscope_vhosts_for_ip(ip,workspace)
            has_vhost_been_scanned = db.get_inscope_submitted_vhosts_for_ip(ip,workspace)
            if has_vhost_been_scanned:
                answer = raw_input("[!] {0} has already been scanned. Scan it, and all vhosts associated with it, again? [Y\\n] ".format(ip))
                if (answer == "Y") or (answer == "y") or (answer == ""):
                    db.update_vhosts_submitted(ip,ip,workspace,0)
            else:
                db_vhost = (ip, ip, 1, 0, workspace)  # in this mode all vhosts are in scope
                #print(db_vhost)
                db.create_vhost(db_vhost)

            for scanned_service_item in scanned_host.services:
                if scanned_service_item.state == "open":
                    scanned_service_port = scanned_service_item.port
                    scanned_service_name = scanned_service_item.service
                    scanned_service_protocol = scanned_service_item.protocol

                    if scanned_service_item.tunnel == 'ssl':
                        scanned_service_name = 'https'
                    db_service = db.get_service(ip, scanned_service_port, scanned_service_protocol, workspace)
                    if not db_service:
                        db_string = (ip, scanned_service_port, scanned_service_protocol, scanned_service_name, workspace)
                        db.create_service(db_string)
                    else:
                        db.update_service(ip, scanned_service_port, scanned_service_protocol, scanned_service_name,
                                          workspace)

                    #Not using this yet, but I'd like to do send this to searchsploit
                    try:
                        scanned_service_product = scanned_service_item.service_dict['product']
                    except:
                        scanned_service_product = ''
                    try:
                        scanned_service_version = scanned_service_item.service_dict['version']
                    except:
                        scanned_service_version = ''
                    try:
                        scanned_service_extrainfo = scanned_service_item.service_dict['extrainfo']
                    except:
                        scanned_service_extrainfo = ''
                    #print "Port: {0}\tService: {1}\tProduct & Version: {3} {4} {5}".format(scanned_service_port,scanned_service_name,scanned_service_product,scanned_service_version,scanned_service_extrainfo)


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
                    udp_nmap_command = cmd
                outfile = scan_output_base_host_filename + "_" + cmd_name
                populated_command = cmd.replace("[TARGET]", vhost).replace("[OUTPUT]", outfile)

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
            if not simulation:
                db.update_vhosts_submitted(vhost, vhost, workspace, 1)


            task_id_list.append(result.task_id)
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


def find_subdomains(domains,simulation,workspace,output_base_dir,scan_mode,out_of_scope_hosts=None):
    config, supported_services = config_parser.read_config_ini()
    celery_path = sys.path[0]
    for domain in domains.split(","):
        for section in config.sections():
            if section == "domain-recon":
                for (cmd_name, cmd) in config.items(section):
                    populated_command = cmd.replace("[DOMAIN]", domain)
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


def post_process_domains(vhosts,process_domain_tuple):

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

        # elif scan_mode == "BB":
        #
        #     cmd_name, cmd = config['nmap-bug-bounty_mode']
        #
        #     utils.
        #
        #     db_vhost = ("", vhost, 1, 0, workspace)
        #     db.create_vhost(db_vhost)


    #pull all in scope vhosts that have not been submitted
    inscope_vhosts = db.get_inscope_unsubmitted_vhosts(workspace)
    for scannable_vhost in inscope_vhosts:
        scannable_vhost = scannable_vhost[0]
        ip = db.get_vhost_ip(scannable_vhost,workspace)
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
                            utils.create_task(cmd_name, populated_command, scannable_vhost, outfile + ".txt", workspace, task_id)


                            result = chain(
                                # insert a row into the database to mark the task as submitted. a subtask does not get tracked
                                # in celery the same way a task does, for instance, you can't find it in flower
                                #tasks.cel_create_task.subtask(args=(cmd_name,populated_command, scannable_vhost, outfile + ".txt", workspace, task_id)),

                                # run the command. run_task takes care of marking the task as started and then completed.
                                # The si tells run_cmd to ignore the data returned from a previous task
                                tasks.run_cmd.si(cmd_name, populated_command, celery_path, task_id).set(task_id=task_id),

                                # right now, every executed command gets sent to a generic post_process task that can do
                                # additinoal stuff based on the command that just ran.
                                tasks.post_process.si(cmd_name, populated_command, output_base_dir, workspace, scannable_vhost, host_dir,
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



def process_url(url,output_base_dir,workspace,simulation):
    celery_path = sys.path[0]
    config,supported_services = config_parser.read_config_ini()
    task_id_list = []
    urls_to_screenshot = []

    try:
        parsed_url = urlparse.urlparse(url)
        scheme = parsed_url[0]
        if not scheme:
            print("\n[!] URL parameter (-u) requires that you specify the scheme (http:// or https://)\n")
            exit()
        if ":" in parsed_url[1]:
            target,port = parsed_url[1].split(':')
        else:
            target = parsed_url[1]
            if scheme == "http":
                port = 80
            elif scheme == "https":
                port = 443
        path = parsed_url[2]
    except:
        if not scheme:
            exit()
    try:
        ip = socket.gethostbyname(target)
    except:
        print("Error getting IP")
    proto = "tcp"

    if ip == target:
        scan_output_base_file_dir = output_base_dir + "/" + ip + "/celerystalkOutput/" + ip + "_" + str(port) + "_" + proto + "_"
    else:
        scan_output_base_file_dir = output_base_dir + "/" + ip + "/celerystalkOutput/" + target + "_" + str(port) + "_" + proto + "_"

    host_dir = output_base_dir + "/" + ip
    host_data_dir = host_dir + "/celerystalkOutput/"
    # Creates something like /pentest/10.0.0.1, /pentest/10.0.0.2, etc.
    utils.create_dir_structure(ip, host_dir)
    # Next two lines create the file that will contain each command that was executed. This is not the audit log,
    # but a log of commands that can easily be copy/pasted if you need to run them again.
    summary_file_name = host_data_dir + "ScanSummary.log"
    summary_file = open(summary_file_name, 'a')

    db_vhost = (ip, target, 1, 1, workspace)  # in this mode all vhosts are in scope
    #print(db_vhost)
    db.create_vhost(db_vhost)

    #Insert port/service combo into services table
    db_service = db.get_service(ip, port, proto, workspace)
    if not db_service:
        db_string = (ip, port, proto, scheme, workspace)
        db.create_service(db_string)

    # Insert url into paths table and take screenshot
    db_path = db.get_path(path,workspace)
    if not db_path:
        url_screenshot_filename = scan_output_base_file_dir + url.replace("http", "").replace("https", "") \
            .replace("/", "_") \
            .replace("\\", "") \
            .replace(":", "_") + ".png"
        url_screenshot_filename = url_screenshot_filename.replace("__", "")
        db_path = (ip, port, url, 0, url_screenshot_filename, workspace)
        db.insert_new_path(db_path)
        #print("Found Url: " + str(url))
        urls_to_screenshot.append((url, url_screenshot_filename))
        result = utils.take_screenshot(urls_to_screenshot)
        #print(result)


    #TODO: This def might introduce a bug - same code as parse config submit jobs to celery. need to just call that function here
    for section in config.sections():
        if (section == "http") or (section == "https"):
            if section == scheme:
                for (cmd_name, cmd) in config.items(section):
                    outfile = scan_output_base_file_dir + cmd_name
                    populated_command = cmd.replace("[TARGET]", target).replace("[PORT]",
                                            str(port)).replace("[OUTPUT]", outfile).replace("[PATH]", path)
                    if simulation:
                        # debug - sends jobs to celery, but with a # in front of every one.
                        populated_command = "#" + populated_command

                    # Grab a UUID from celery.utils so that i can assign it to my task at init, which is amazing because
                    # that allows me to pass it to all of the tasks in the chain.

                    task_id = uuid()
                    utils.create_task(cmd_name,populated_command, target, outfile + ".txt", workspace, task_id)
                    result = chain(
                        # insert a row into the database to mark the task as submitted. a subtask does not get tracked
                        # in celery the same way a task does, for instance, you can't find it in flower
                        #tasks.cel_create_task.subtask(args=(cmd_name,populated_command, target, outfile + ".txt", workspace, task_id)),

                        # run the command. run_task takes care of marking the task as started and then completed.
                        # The si tells run_cmd to ignore the data returned from a previous task
                        tasks.run_cmd.si(cmd_name, populated_command, celery_path,task_id).set(task_id=task_id),

                        # right now, every executed command gets sent to a generic post_process task that can do
                        # additinoal stuff based on the command that just ran.
                        tasks.post_process.si(cmd_name, populated_command, output_base_dir, workspace, target, host_dir,
                                              simulation,port, scheme,proto,celery_path),
                    )()  # .apply_async()

                    task_id_list.append(result.task_id)
                    host_audit_log = host_dir + "/" + "{0}_executed_commands.txt".format(ip)
                    f = open(host_audit_log, 'a')
                    f.write(populated_command + "\n\n")
                    f.close()
    print("[+] Submitted {0} tasks to queue.\n".format(len(task_id_list)))