from celery import chain
from kombu import uuid

import lib.db
import lib.utils
import tasks
from celery.utils import uuid

from lib import config_parser, utils


def screenshot_all_paths(workspace):
    urls_to_screenshot_with_filenames = []

    paths = lib.db.get_all_paths(workspace)

    if len(paths) > 0:
        screenshot_name = "db"
        for (id,vhost,port,path,submitted,scan_output_base_file_dir,workspace) in paths:
            urls_to_screenshot_with_filenames.append((path, scan_output_base_file_dir))


        task_id = uuid()
        populated_command = "firefox-esr {0}-screenshots | {1} | {2}".format(screenshot_name, vhost,
                                                                             scan_output_base_file_dir)
        command_name = "Screenshots"
        lib.utils.create_task(command_name, populated_command, vhost, scan_output_base_file_dir, workspace, task_id)
        tasks.cel_take_screenshot.delay(urls_to_screenshot_with_filenames, task_id, vhost, scan_output_base_file_dir,
                                  workspace, command_name, populated_command)


def aquatone_all_paths(workspace,simulation=None,config_file=None):
    print("in aquatone all_paths")
    urls_to_screenshot_with_filenames = []
    paths = lib.db.get_all_paths(workspace)
    celery_path = lib.db.get_current_install_path()[0][0]
    #config, supported_services = config_parser.read_config_ini(config_file)


    if len(paths) > 0:
        screenshot_name = "db"
        for (id, vhost, port, path, submitted, scan_output_base_file_dir, workspace) in paths:
            urls_to_screenshot_with_filenames.append((path, scan_output_base_file_dir))



        for (cmd_name, cmd) in config.items("screenshots"):
            #print(cmd_name, cmd)
            try:
                if cmd_name == "aquatone":
                    outfile = scan_output_base_file_dir + "_" + cmd_name
                    filename = "/tmp/" + workspace + "_paths_" + vhost + ".txt"
                    populated_command = cmd.replace("[FILE]", filename).replace("[OUTPUT]", outfile)

                    paths = lib.db.get_all_paths_for_host_path_only(vhost,workspace)
                    print(str(paths))


                    with open(filename, 'w') as paths_tmp_file:
                        #paths_tmp_file.write(str(paths))
                        for line in paths:
                             #print(str(line))
                             paths_tmp_file.write(str(line[0]) + "\n")

                    populated_command = cmd.replace("[FILE]", filename).replace("[OUTPUT]", outfile)
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