import sys
from ConfigParser import ConfigParser
from celery import chain
from kombu import uuid

import lib.utils
import tasks
from lib import config_parser, utils
import lib.db


def nmap_scan_subdomain_host(vhost,workspace,simulation,output_base_dir,config_file=None):
    celery_path = sys.path[0]
    config_nmap_options = config_parser.extract_bb_nmap_options(config_file=config_file)
    config = ConfigParser(allow_no_value=True)
    config.read(['config.ini'])

    vhost_explicitly_out_of_scope = lib.db.is_vhost_explicitly_out_of_scope(vhost, workspace)
    if not vhost_explicitly_out_of_scope:
        #print(config_nmap_options)
        cmd_name = "nmap_tcp_scan"
        try:
            if not simulation:
                populated_command = "nmap " + vhost + config_nmap_options
            else:
                populated_command = "#nmap " + vhost + config_nmap_options
        except TypeError:
            print("[!] Error: In the config file, there needs to be one, and only one, enabled tcp_scan command in the nmap_commands section.")
            print("[!]        This determines what ports to scan.")
            exit()
        task_id = uuid()
        utils.create_task(cmd_name, populated_command, vhost, output_base_dir + ".txt", workspace, task_id)
        result = chain(
            tasks.cel_nmap_scan.si(cmd_name, populated_command, vhost, config_nmap_options, celery_path, task_id,workspace).set(task_id=task_id),
        )()

def nmapcommand(simulation,targets,config_file=None):
    lib.utils.start_services()
    task_count = 0

    try:
        workspace = lib.db.get_current_workspace()[0][0]
        output_dir = lib.db.get_output_dir_for_workspace(workspace)[0][0]
    except:
        print("[!] There are no workspaces yet. Create one and run your command again:\n\n")
        print("./celerystalk workspace create -o output_dir                     #Default workspace")
        print("./celerystalk workspace create -o output_dir -w workspace_name   #Named workspace\n")
        exit()

    in_scope_vhosts = lib.db.get_unique_inscope_vhosts(workspace)
    for in_scope_vhost in in_scope_vhosts:
        vhost = in_scope_vhost[0]
        if targets:
            target_list = lib.utils.target_splitter(targets)
            if vhost in target_list:
                lib.nmap.nmap_scan_subdomain_host(vhost, workspace, simulation, output_dir,config_file=config_file)
                task_count = task_count + 1
        else:
            lib.nmap.nmap_scan_subdomain_host(vhost, workspace, simulation, output_dir,config_file=config_file)
            task_count = task_count + 1

    print("[+] Submitted {0} nmap tasks to queue.\n".format(str(len(task_count))))

    print("[+]\t\tTo keep an eye on things, run one of these commands: \n[+]")
    print("[+]\t\t./celerystalk query [watch]")
    print("[+]\t\t./celerystalk query brief [watch]")
    print("[+]\t\t./celerystalk query summary [watch]")
    print("[+]")
    print("[+] To peak behind the curtain, view log/celeryWorker.log")
    print("[+] For a csv compatible record of every command execued, view log/cmdExecutionAudit.log\n")
    print("[+]")
    print("[+] To view services as they make it into the DB, run: ")
    print("[+]\t\t./celerystalk db services")
