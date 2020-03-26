import subprocess
from subprocess import Popen
from time import sleep
from libnmap.parser import NmapParser
from libnmap.process import NmapProcess
from libnessus.parser import NessusParser
from netaddr import IPAddress, IPRange, IPNetwork
import socket
import db
import os
import re
import lib.db
import lib.config_parser
import redis
from redis import ConnectionError



def task_splitter(id):
    task_list=[]
    for task in id.split(","):
                # Simple check to see if there is a range included.
                if "-" in str(task):
                    #print("range found")
                    taskrange = task.split("-")
                    rangestart = int(taskrange[0])
                    rangeend = int(taskrange[1])
                    #print(rangestart)
                    #print(rangeend)

                    try:
                        task_in_range = range(rangestart, rangeend)
                        #print(task_in_range)
                        for individual_task_id in list(task_in_range):
                            task_list.append(individual_task_id)
                            #print(individual_task_id)
                    except:
                        print("error")
                else:
                    # If there is no "-" in the line, we can deal with it as a simple task
                    task_list.append(task)
                    #print(task)
    return task_list


def create_dir_structure(ip, host_dir):
    #print("\n[+]" + "*" * 30)
    #print("[+] Target: " + ip)
    #print("[+]" + "*" * 30 )

    try:
        os.stat(host_dir)
    except:
        os.mkdir(host_dir)
    #This is the subdirectory that will contain all of the tool output.
    host_data_dir = host_dir + "/celerystalkOutput"
    #print("[+] Creating scans directory at: %s" % host_data_dir)
    try:
        os.stat(host_data_dir)
    except:
        os.mkdir(host_data_dir)


def nmap_parser(nmap_xml):
    """
    If user chooses to start from nmap.xml, read the xml and return an nmap_report object
    :param nmap_xml:
    :return:
    """
    try:
        nmap_report = NmapParser.parse_fromfile(nmap_xml)
        return nmap_report
    except:
        print("\n[!] Error reading {0}. Does it exist?\n".format(nmap_xml))
        exit()


def nessus_parser(nessus_db):
    """
    If user chooses to start from scan.nessus, read the xml and return an nessus_report object
    :param nessus_db:
    :return: nessus_report
    """
    try:
        nessus_report = report = NessusParser.parse_fromfile(nessus_db)
        return nessus_report
    except:
        print("\n[!] Error reading {0}. Does it exist?\n".format(nessus_db))
        exit()



def nmap_scan(hosts, output_dir):
    """
    if user chooses to start from an nmap scan, run the scan and then return an nmap_report object
    :param hosts:
    :param output_dir:
    :return:
    """
    print("[+] Kicking off nmap scan. I don't have  any feedback working, so just be patient")
    nm = NmapProcess(hosts, options="-sC -sV -Pn -p1-65535")
    rc = nm.run()
    nmap_report = NmapParser.parse(nm.stdout)
    nmap_xml = output_dir + "/" + hosts.replace("/","_") + "_nmap.xml"
    f = open(nmap_xml, 'a')
    f.write(nm.stdout)
    f.close()
    print("[+] Nmap scan saved to: {0}".format(nmap_xml))
    return nmap_report




def nmap_follow_up_scan(hosts, port):
    """
    This needs to be reworked.  If nmap service scan can't determine the service, i run an nmap scan without service
    detection to get the default port.  I should just read the IANA ports file instead and grep for the port, or maybe
    even the nmap version of the IANA ports list.
    :param hosts:
    :param port:
    :return:
    """
    nm = NmapProcess(hosts, options="-Pn -p %d" % port)
    rc = nm.run()
    nmap_report = NmapParser.parse(nm.stdout)
    return nmap_report


def start_services(config_file):
    start_celery_worker(config_file)
    start_redis()
    check_redis_running()

def restart_services(config_file):
    shutdown_background_jobs()
    sleep(2)
    start_celery_worker(config_file)
    start_redis()
    check_redis_running()




def start_celery_worker(config_file):
    # We can always just try and start the celery worker because it won't restart already running thanks to pidfile.
    try:
        concurrent_tasks = lib.config_parser.get_concurrent_tasks(config_file)
        popen_string = "celery -A tasks worker --concurrency=%s -Ofair -q --pidfile ./%%n.pid --logfile ./log/celeryWorker.log > /dev/null 2>&1" % (str(concurrent_tasks))
        p = Popen(popen_string, shell=True)

    except Exception, e:
        #print(e)
        p = Popen(
            "celery -A tasks worker -Ofair -q --pidfile ./%n.pid --logfile ./log/celeryWorker.log > /dev/null 2>&1",
            shell=True)

    #p = Popen("celery -A tasks worker -Ofair -q --pidfile ./%n.pid --logfile ./log/celeryWorker.log > /dev/null 2>&1", shell=True)
    #print("[+] Started celery worker")

def start_redis():
    # We can always just try and start the redis-server .
    p = Popen("/etc/init.d/redis-server start > /dev/null 2>&1",shell=True)
    c = p.communicate()
    #print("[+] Started redis service\n")


def shutdown_background_jobs():
    print("[-] Stopping celery worker (if running)")
    #p = Popen("celery -A tasks control shutdown > /dev/null 2>&1", shell=True)
    p = Popen('pkill -f "celery -A tasks"> /dev/null 2>&1', shell=True)

    print("[-] Stopping redis service (if running)\n")
    p = Popen("/etc/init.d/redis-server stop > /dev/null 2>&1", shell=True)
    c = p.communicate()



# def initialize_celery_flower():
#     print("[-] Stopping Flower (if running)")
#     p = Popen('pkill -f "tasks flower" > /dev/null 2>&1', shell=True)
#     time.sleep(3)
#     print("[+] Starting Flower")
#     p = Popen("celery -A tasks flower --address=127.0.0.1 --broker='redis://localhost:6379/0' > /dev/null 2>&1", shell=True)
def target_splitter(target_networks):
    scope_list = []
    for network in target_networks.split(","):
                # check to see if a subdomain/vhost was specified (if it has a letter, its not an IP address)
                if re.search('[a-zA-Z]', network):
                    scope_list.append(network)
                    break
                # Simple check to see if there is a range included.
                if "-" in str(network):
                    #print("range found")
                    iprange = network.split("-")
                    # Convert the first part of the range to an IPAddress object
                    rangestart = (IPAddress(iprange[0]))
                    # rangeend = (IPAddress(iprange[1]))
                    # Hold off on converting the second part. We first need to check if
                    # it is a real IP or just the last octet (i.e., 192.168.0.100-110)
                    rangeend = iprange[1]
                    # If there is a period in the second part, we can just cast to IPAddress now
                    if "." in rangeend:
                        rangeend = IPAddress(rangeend)
                        net_range = IPRange(rangestart, rangeend)
                        # scope_list is a list of all of the IP addresses, networks, and ranges that are in scope
                        for individual_ip in list(net_range):
                            scope_list.append(individual_ip)
                            #print(individual_ip)

                    else:
                        try:
                            # If there is no period, that means we just have the last octet for the second half.
                            # So this part copies the first three octects from the first half range and prepends
                            # it to the single octet given for the second part.
                            startpart = str(rangestart).rsplit('.', 1)[0]
                            rangeend = IPAddress(startpart+"." + rangeend)
                            net_range = IPRange(rangestart, rangeend)
                            # scope_list is a list of all of the IP addresses, networks, and ranges that are in scope
                            for individual_ip in list(net_range):
                                scope_list.append(individual_ip)
                                #print(individual_ip)

                        except:
                            # Putting this try/except here because i have a feeling that at some point we will see
                            # something like 192.168.0.0-192.168.200.255 or something like that.  Not handling that
                            # right now.
                            print(error)
                else:
                    # If there is no "-" in the line, we can deal with it as a simple network or IPAddress. Luckily
                    # IPNetwork automatically converts an IP without a CIDR into /32 CIDR, and it works just like
                    # an IP address
                    net = IPNetwork(network)
                    for individual_ip in list(net):
                        scope_list.append(individual_ip)
                        #print(individual_ip)
    return scope_list


def domain_scope_checker(domain,workspace):
    domain_tuples = []
    try:
        ips = socket.gethostbyname(domain)
        for ip in ips.split():
            domain_tuples.append((domain, ip))
    except:
        #If the domain does not resolve, skip it!
        return 0,""
    unique_db_hosts = db.get_unique_inscope_ips(workspace)
    in_scope = "False"
    for domain_tuple in domain_tuples:
        ip = str(domain_tuple[1])
        for item in unique_db_hosts:
            if ip in item:
                # print("Domain: {domain} - Resolved IP: {ip} is in scope.").format(domain=domain,ip=ip)
                in_scope = "True"
                return 1,ip
    if in_scope == "False":
        for domain_tuple in domain_tuples:
            ip = str(domain_tuple[1])
            return 0,ip


def create_task(command_name, populated_command, ip, output_dir, workspace, task_id):
    db_task = (task_id, 1, command_name, populated_command, ip, output_dir, 'SUBMITTED', workspace)
    db.create_task(db_task)



def check_for_new_default_config():

    user_config_file = check_if_config_ini_exists()
    default_config_file = 'setup/config_default.ini'
    user_config_age=os.path.getmtime(user_config_file)
    #print(user_config_age)
    default_config_age = os.path.getmtime(default_config_file)
    #print(default_config_age)
    if user_config_age < default_config_age:

        print("[!] [config_default.ini] pulled from git is newer than the the current [config.ini] file.")

        print("[!] This is most likely because a new tool or possibly a new feature has been added.\n")
        answer = raw_input("[+] Would you like backup your current config and replace [config.ini] with the new version? (y\N)")
        print("")
        if (answer == "Y") or (answer == "y"):
            from shutil import copyfile
            backup_config_filename = 'config.ini.' + str(user_config_age)
            copyfile(user_config_file, backup_config_filename)
            copyfile(default_config_file, user_config_file)
            print("[+] config.ini has been copied to " +  backup_config_filename)
            print("[+] setup/config_default.ini has been copied to config.ini")
        else:
            from subprocess import Popen
            path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(lib.scan.__file__)), "../config.ini", ))
            populated_command = "touch " + path
            p = Popen(populated_command, shell=True)
            p.communicate()



def check_if_config_ini_exists():
    if os.path.exists(os.path.join(os.getcwd(), 'config.ini')):
        config_file = 'config.ini'
    else:
        print("[!] The default config file does not exist. Run ./setup/install.sh and try again.")
        exit()
    return config_file


def check_for_dependencies():
    try:
        os.stat('/opt/aquatone/aquatone')
    except:
        print("[!] Aquatone is not installed.")
        print("[!]   cd setup")
        print("[!]   ./install.sh")
        exit()


def get_terminal_width():
    """
    From: https://gist.githubusercontent.com/Steelsouls/9626112/raw/e99b6a741fa22c20c3699140d352de5a46db4ad2/terminal_width.py
    :return: the current width of the terminal
    """
    command = ['tput', 'cols']
    try:
        width = int(subprocess.check_output(command))
    except OSError as e:
        print("Invalid Command '{0}': exit status ({1})".format(
              command[0], e.errno))
    except subprocess.CalledProcessError as e:
        print("Command '{0}' returned non-zero exit status: ({1})".format(
              command, e.returncode))
    else:
        return width


def check_redis_running():
        r = redis.Redis(host='localhost', port=6379, db=0)
        try:
            r.ping()
        except ConnectionError:
            print("[!] Redis is not running, try starting it: ")
            print("/etc/init.d/redis-server restart")
            exit(0)

def check_celery_status():
    from celery import Celery
    app = Celery('tasks', broker='redis://localhost:6379', backend='db+sqlite:///results.sqlite')
    status = app.control.inspect().active()
    if not status:
        print("[!] Celery is not running, try starting it: ")
        print("./celerystalk admin start")
        exit(0)