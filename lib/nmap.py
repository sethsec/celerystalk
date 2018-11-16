import sys
from ConfigParser import ConfigParser
from celery import chain
from kombu import uuid

import lib.utils
import tasks
from lib import config_parser, utils
import lib.db


def nmap_scan_subdomain_host(vhost,workspace,simulation,output_base_dir):
    celery_path = sys.path[0]
    config_nmap_options = config_parser.extract_bb_nmap_options()
    config = ConfigParser(allow_no_value=True)
    config.read(['config.ini'])

    vhost_explicitly_out_of_scope = lib.db.is_vhost_explicitly_out_of_scope(vhost, workspace)
    in_scope, ip = lib.utils.domain_scope_checker(vhost, workspace)
    if not vhost_explicitly_out_of_scope:
        #print(config_nmap_options)
        cmd_name = "nmap_bug_bounty_mode"
        try:
            populated_command = "nmap " + vhost + config_nmap_options
        except TypeError:
            print("[!] Error: In the config file, there needs to be one, and only one, enabled bug_bounty_mode command.")
            print("[!]        This determines what ports to scan.")
        task_id = uuid()
        utils.create_task(cmd_name, populated_command, vhost, output_base_dir + ".txt", workspace, task_id)
        result = chain(
            tasks.cel_nmap_scan.si(cmd_name, populated_command, vhost, config_nmap_options, celery_path, task_id,workspace).set(task_id=task_id),
        )()


def nmapcommand(simulation,targets):
    lib.utils.start_services()
    celery_path = sys.path[0]


    try:
        workspace = lib.db.get_current_workspace()[0][0]
        output_dir = lib.db.get_output_dir_for_workspace(workspace)[0][0]
    except:
        print("[!] There are no workspaces yet. Create one and run your command again:\n\n")
        print("./celerystalk workspace create -o output_dir                     #Default workspace")
        print("./celerystalk workspace create -o output_dir -w workspace_name   #Named workspace\n")
        exit()

    workspace_mode = lib.db.get_workspace_mode(workspace)

    in_scope_vhosts = lib.db.get_unique_inscope_vhosts(workspace)
    for in_scope_vhost in in_scope_vhosts:
        vhost = in_scope_vhost[0]
        if targets:
            target_list = lib.utils.target_splitter(targets)
            if vhost in target_list:
                lib.nmap.nmap_scan_subdomain_host(vhost, workspace, simulation, output_dir)
        else:
            lib.nmap.nmap_scan_subdomain_host(vhost, workspace, simulation, output_dir)

    print("[+]\t\tTo keep an eye on things, run one of these commands: \n[+]")
    print("[+]\t\tcelerystalk query [watch]")
    print("[+]\t\tcelerystalk query brief [watch]")
    print("[+]\t\tcelerystalk query summary [watch]")
    print("[+]")
    print("[+] To peak behind the curtain, view log/celeryWorker.log")
    print("[+] For a csv compatible record of every command execued, view log/cmdExecutionAudit.log\n")


        # ####################################
        # # Scan - Bug Bounty mode - take domains, find subdomains, run nmap, run celerystalk (for ALL hosts in target file)
        # ####################################
        #
        # if arguments["<bb_scope_file>"]:
        #     scan_mode = "BB"
        #     in_scope_domains, in_scope_hosts, out_of_scope_hosts = lib.config_parser.read_bb_scope_ini(
        #         arguments["<bb_scope_file>"])
        #
        #
        #     #submit the in scope hosts to celery
        #     for in_scope_host in in_scope_hosts:
        #         in_scope_host = in_scope_host[0]
        #         #try:
        #         ip = socket.gethostbyname(in_scope_host)
        #
        #         #nmap_report = lib.scan.nmap_scan_subdomain_host(in_scope_host, workspace,arguments["--simulation"],output_dir)  # run nmap scan
        #         lib.scan.nmap_scan_subdomain_host(in_scope_host, workspace,arguments["--simulation"],output_dir)  # run nmap scan
        #         db_vhost = (ip, in_scope_host, 1, 0, workspace)  # in this mode all vhosts are in scope
        #         print(db_vhost)
        #         db.create_vhost(db_vhost)
        #         #lib.scan.process_nmap_data2(nmap_report, workspace)
        #         #lib.scan.process_db_services(output_dir, arguments["--simulation"], workspace)
        #         # except:
        #         #     print("2There was an issue running the nmap scan against {0}.").format(in_scope_host)
        #         #     ip = ""
        #         #     db_vhost = (ip, in_scope_host, 0, 0, workspace)  # not in scope if no IP
        #         #     print(db_vhost)
        #         #     db.create_vhost(db_vhost)
        #
        #     for domain in in_scope_domains:
        #         print("domain pulled from in scope domains")
        #         print(domain)
        #         lib.scan.subdomains(domain, arguments["--simulation"], workspace, output_dir,
        #                                  scan_mode,out_of_scope_hosts)
        #     #lib.scan.process_db_services(output_dir, arguments["--simulation"], workspace)