from subprocess import Popen, PIPE
from celery import Celery
import time
from timeit import default_timer as timer
import lib.csimport
from lib import db
import lib.scan
import parsers.generic_urlextract
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
def run_cmd(command_name, populated_command,celery_path,task_id,path=None,process_domain_tuple=None,process_nmap=None,output_file=None):
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
    else:
        #putting this here because i want to parse scan tool output for urls, not subdomain tools output
        parsers.generic_urlextract.extract_in_scope_urls_from_task_output(out)

    if process_nmap:
        nmap_xml = output_file + ".xml"
        nmap_report = NmapParser.parse_fromfile(nmap_xml)
        workspace = lib.db.get_current_workspace()[0][0]
        lib.csimport.process_nmap_data(nmap_report, workspace)
    return out










