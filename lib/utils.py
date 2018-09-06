import os
from subprocess import Popen

from libnmap.parser import NmapParser
from libnmap.process import NmapProcess
from libnessus.parser import NessusParser
from netaddr import IPAddress, IPRange, IPNetwork
import socket
import db
from selenium import webdriver
#from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options
from pyvirtualdisplay import Display
import os
import time


def take_screenshot(url,output):
    #Source: https://medium.com/@ronnyml/website-screenshot-generator-with-python-593d6ddb56cb
    #Source: https://medium.com/@pyzzled/running-headless-chrome-with-selenium-in-python-3f42d1f5ff1d
    #Source: https://stackoverflow.com/questions/50642308/org-openqa-selenium-webdriverexception-unknown-error-devtoolsactiveport-file-d

    # instantiate a chrome options object so you can set the size and headless preference
    # chrome_options = Options()
    # chrome_options.add_argument("--headless")
    # chrome_options.add_argument("--window-size=1920x1080")
    # chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument("--allow-http-screen-capture")
    # chrome_options.add_argument("--ignore-certificate-errors")
    # chrome_options.add_argument("--disable-gpu")
    #
    # driver = '/usr/bin/chromedriver'
    # driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=driver)
    display = Display(visible=0, size=(800, 600))
    display.start()
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Firefox(firefox_options=options)

    try:
        # capture the screen
        driver.get(url)
        #time.sleep(3)
        #driver.get_screenshot_as_file(output)
        print("output in takescreenshot: " + output)
        print(url)
        screenshot = driver.save_screenshot(output)
        driver.quit()
        return screenshot
    except:
        return False
    display.stop()




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
    print("\n[+]" + "*" * 30)
    print("[+] IP address: " + ip)
    print("[+]" + "*" * 30 )

    try:
        os.stat(host_dir)
    except:
        os.mkdir(host_dir)
    #This is the subdirectory that will contain all of the tool output.
    host_data_dir = host_dir + "/celerystalkOutput"
    print("[+] Creating scans directory at: %s" % host_data_dir)
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


def start_services():
    # maybe this first part should be somwhere else.   But for now, in order to run, celery worker and celery flower need to be started.
    print("[+] Starting celery Worker")
    start_celery_worker()
    start_redis()
    print("[+] Reading config file")


def start_celery_worker():
    # We can always just try and start the celery worker because it won't restart already running thanks to pidfile.
    p = Popen("celery -A tasks worker --concurrency=5 -Ofair -q --pidfile ./%n.pid --logfile ./log/celeryWorker.log > /dev/null 2>&1", shell=True)


def start_redis():
    # We can always just try and start the redis-server .
    p = Popen("/etc/init.d/redis-server start > /dev/null 2>&1",shell=True)
    c = p.communicate()


def shutdown_background_jobs():
    print("[-] Stopping celery worker and flower (if running)")
    #p = Popen("celery -A tasks control shutdown > /dev/null 2>&1", shell=True)
    p = Popen('pkill -f "celery"> /dev/null 2>&1', shell=True)

    #print("[-] Stopping celery flower (if running)")
    #p = Popen('pkill -f "tasks flower"> /dev/null 2>&1', shell=True)



# def initialize_celery_flower():
#     print("[-] Stopping Flower (if running)")
#     p = Popen('pkill -f "tasks flower" > /dev/null 2>&1', shell=True)
#     time.sleep(3)
#     print("[+] Starting Flower")
#     p = Popen("celery -A tasks flower --address=127.0.0.1 --broker='redis://localhost:6379/0' > /dev/null 2>&1", shell=True)
def target_splitter(target_networks):
    scope_list = []
    for network in target_networks.split(","):
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
    unique_db_hosts = db.get_unique_hosts(workspace)
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