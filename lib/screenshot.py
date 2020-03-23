from celery import chain
import lib.db
import lib.utils
import tasks
from celery.utils import uuid
import os
from lib import config_parser, utils
from subprocess import Popen

def does_aquatone_folder_exixst():
    workspace = lib.db.get_current_workspace()[0][0]
    outdir = lib.db.get_output_dir_for_workspace(workspace)[0][0]
    aquatone_dir = os.path.join(outdir, 'celerystalkReports/aquatone/')

    try:
        os.stat(aquatone_dir)
        return True
    except:
        return False

def screenshot_command(arguments):
    if arguments["-w"]:
        output_dir, workspace = lib.workspace.create_workspace(arguments["-w"], arguments)
    else:
        try:
            workspace = lib.db.get_current_workspace()[0][0]
            output_dir = lib.db.get_output_dir_for_workspace(workspace)[0][0]
        except:
            print("[!] There are no workspaces yet. Create one and run your command again:\n\n")
            print("./celerystalk workspace create -o output_dir -w workspace_name -m vapt")
            print("./celerystalk workspace create -o output_dir -w workspace_name -m bb\n")
            exit()
    if arguments["-c"]:
        if os.path.exists(arguments["-c"]):
            config_file = arguments["-c"]
        else:
            print("[!] The specified config file does not exist. Try again?")
            exit()
    else:
        config_file = 'config.ini'

    # lib.screenshot.screenshot_all_paths(workspace)
    #TODO: change this to reflect number of screenshots taken based on config.ini max
    paths_len = len(lib.db.get_all_paths_exclude_404(workspace))
    max_paths_len = len(get_max_screenshots(workspace,config_file))
    max = lib.config_parser.get_screenshot_max(config_file)
    print("[+]\n[+] There are [{0}] paths in the DB").format(str(paths_len))
    #print("[+] max_screenshots_per_vhost set to: [{0}]").format(str(max))
    print("[+] Tasking aquatone to take [{0}] screenshots per host for a total of [{1}] screenshots\n[+]\n[+]").format(str(max),str(max_paths_len))
    lib.screenshot.aquatone_all_paths(workspace)

def get_max_screenshots(workspace,config_file):
    screenshot_list = []
    max = lib.config_parser.get_screenshot_max(config_file)
    vhosts = lib.db.get_unique_hosts_with_paths(workspace)
    for vhost in vhosts:
        vhost = vhost[0]
        paths = lib.db.get_x_paths_for_host_path_only(vhost, workspace,max)
        for path in paths:
            screenshot_list.append(path[0])
    return screenshot_list


def aquatone_all_paths(workspace,simulation=None,config_file=None):
    #print("in aquatone all_paths")
    urls_to_screenshot = []
    #TODO: Instead of just grabbing all paths here, maybe add some logic to see if only new paths should be scanned or something. at a minimum, as they are grabbed, we need to update the "screenshot taken" column and put the auatone directory or something like that.
    paths = lib.db.get_all_paths_exclude_404(workspace)
    celery_path = lib.db.get_current_install_path()[0][0]
    outdir = lib.db.get_output_dir_for_workspace(workspace)[0][0]
    outdir = os.path.join(outdir,'celerystalkReports/aquatone/')

    try:
        os.stat(outdir)
    except:
        os.makedirs(outdir)

    if config_file == None:
        config_file = "config.ini"

    config, supported_services = config_parser.read_config_ini(config_file)


    if len(paths) > 0:
        screenshot_name = "db"
        for (cmd_name, cmd) in config.items("screenshots"):
            #print(cmd_name, cmd)
            try:
                if cmd_name == "aquatone":
                    populated_command = celery_path + "/celerystalk db paths_only limit | " + cmd.replace("[OUTPUT]", outdir)
                    #print(populated_command)
            except Exception, e:
                print(e)
                print("[!] Error: In the config file, there needs to be one (and only one) enabled aquatone command.")
                exit()



        p = Popen(populated_command, shell=True)
        p.communicate()

        # task_id = uuid()
        # utils.create_task(cmd_name, populated_command, workspace, outdir + "aquatone_report.html", workspace, task_id)
        # result = chain(
        #     tasks.run_cmd.si(cmd_name, populated_command, celery_path, task_id).set(task_id=task_id),
        # )()
        # print("[+]\t\tTo keep an eye on things, run one of these commands: \n[+]")
        # print("[+]\t\t./celerystalk query [watch]")
        # print("[+]\t\t./celerystalk query brief [watch]")
        # print("[+]\t\t./celerystalk query summary [watch]")
        # print("[+]\t\tor\n[+]\t\ttail -f " + outdir + "aquatone_stdout.txt")
        # print("[+]")
        # print("[+] To peak behind the curtain, view log/celeryWorker.log")
        # print("[+] For a csv compatible record of every command execued, view log/cmdExecutionAudit.log\n")