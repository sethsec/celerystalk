import re
from netaddr import *
from netaddr import IPAddress
import sys
import lib.db
import lib.utils
from lib import db
import urlparse
import socket



def import_scope(scope_file,workspace):
    with open(scope_file) as sf:
        for network in sf.readlines():
            if "-" in str(network):
                print("range found")
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
                    netRange = IPRange(rangestart, rangeend)
                    # scopeList is a list of all of the IP addresses, networks, and ranges that are in scope
                    #scopeList.append(netRange)
                    for ip in netRange:
                        ip = str(ip)
                        db_vhost = (ip, ip, 1, 0, workspace) # add it to the vhosts db and mark as in scope
                        lib.db.create_vhost(db_vhost)
                else:
                    try:
                        # If there is no period, that means we just have the last octet for the second half.
                        # So this part copies the first three octects from the first half range and prepends
                        # it to the single octet given for the second part.
                        startpart = str(rangestart).rsplit('.', 1)[0]
                        netRange = IPAddress(startpart + "." + rangeend)
                        for ip in netRange:
                            ip = str(ip)
                            db_vhost = (ip, ip, 1, 0, workspace)  # add it to the vhosts db and mark as in scope
                            lib.db.create_vhost(db_vhost)
                    except Exception, e:
                        # Putting this try/except here because i have a feeling that at some point we will see
                        # something like 192.168.0.0-192.168.200.255 or something like that.  Not handling that
                        # right now.
                        print(e)
            else:
                # If there is no "-" in the line, we can deal with it as a simple network or IPAddress. Luckily
                # IPNetwork automatically converts an IP without a CIDR into /32 CIDR, and it works just like
                # an IP address
                net = IPNetwork(network)
                for ip in net:
                    ip = str(ip)
                    db_vhost = (ip, ip, 1, 0, workspace)  # add it to the vhosts db and mark as in scope
                    lib.db.create_vhost(db_vhost)
                #scopeList.append(net)




def import_vhosts(subdomains_file,workspace):
    with open(subdomains_file) as vhosts:
        for vhost in vhosts.readlines():
            vhost = vhost.rstrip()
            #print(vhost)
            # from https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
            ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
            vhost = ansi_escape.sub('', vhost)
            #print("escaped:\t" + vhost)
            if re.match(r'\w', vhost):
                in_scope,ip = lib.utils.domain_scope_checker(vhost,workspace)
                if in_scope == 1:
                    print("[+] Found subdomain (in scope):\t\t" + vhost)
                    db_vhost = (ip,vhost,1, 0,workspace)
                    lib.db.create_vhost(db_vhost)
                else:
                    print("[+] Found subdomain (out of scope):\t" + vhost)
                    db_vhost = (ip, vhost, 0, 0, workspace)
                    lib.db.create_vhost(db_vhost)

def import_url(url,workspace,output_base_dir):
    celery_path = sys.path[0]
    #config, supported_services = config_parser.read_config_ini()
    #task_id_list = []
    urls_to_screenshot = []

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


    in_scope, ip = lib.utils.domain_scope_checker(vhost, workspace)
    proto = "tcp"

    if in_scope == 0:
        answer = raw_input(
            "[+] {0} is not in scope. Would you like to to add {1}/{0} to the list of in scope hosts?".format(vhost,
                                                                                                              ip))
        if (answer == "Y") or (answer == "y") or (answer == ""):
            in_scope = 1
    if in_scope == 1:
        db_vhost = (ip, vhost, 1, 0, workspace)  # add it to the vhosts db and mark as in scope
        lib.db.create_vhost(db_vhost)
        #lib.db.create_service(db_service)

        if ip == vhost:
            scan_output_base_file_dir = output_base_dir + "/" + ip + "/celerystalkOutput/" + ip + "_" + str(
                port) + "_" + proto + "_"
        else:
            scan_output_base_file_dir = output_base_dir + "/" + ip + "/celerystalkOutput/" + vhost + "_" + str(
                port) + "_" + proto + "_"

        host_dir = output_base_dir + "/" + ip
        host_data_dir = host_dir + "/celerystalkOutput/"
        # Creates something like /pentest/10.0.0.1, /pentest/10.0.0.2, etc.
        lib.utils.create_dir_structure(ip, host_dir)
        # Next two lines create the file that will contain each command that was executed. This is not the audit log,
        # but a log of commands that can easily be copy/pasted if you need to run them again.
        summary_file_name = host_data_dir + "ScanSummary.log"
        summary_file = open(summary_file_name, 'a')

        db_vhost = (ip, vhost, 1, 1, workspace)  # in this mode all vhosts are in scope
        # print(db_vhost)
        db.create_vhost(db_vhost)

        # Insert port/service combo into services table if it doesnt exist
        db_service = db.get_service(ip, port, proto, workspace)
        if not db_service:
            db_string = (ip, port, proto, scheme, workspace)
            db.create_service(db_string)

        # Insert url into paths table and take screenshot
        db_path = db.get_path(path, workspace)
        if not db_path:
            url_screenshot_filename = scan_output_base_file_dir + url.replace("http", "").replace("https", "") \
                .replace("/", "_") \
                .replace("\\", "") \
                .replace(":", "_") + ".png"
            url_screenshot_filename = url_screenshot_filename.replace("__", "")
            db_path = (ip, port, url, 0, url_screenshot_filename, workspace)
            db.insert_new_path(db_path)
            # print("Found Url: " + str(url))
            #urls_to_screenshot.append((url, url_screenshot_filename))

            #lib.utils.take_screenshot(urls_to_screenshot)
            # print(result)


        db_path = (ip, port, url, 0, url_screenshot_filename, workspace)
        lib.db.insert_new_path(db_path)

    #print(in_scope,ip)
#    try:
#        ip = socket.gethostbyname(vhost)
#    except:
#        print("Error getting IP")




def update_inscope_vhosts(workspace):
    vhosts = lib.db.get_unique_out_of_scope_vhosts(workspace)
    #print(vhosts)
    for vhost in vhosts:
        vhost = vhost[0].rstrip()
        #print(vhost)
        # from https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
        ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
        vhost = ansi_escape.sub('', vhost)
        #print("escaped:\t" + vhost)
        if re.match(r'\w', vhost):
            in_scope,ip = lib.utils.domain_scope_checker(vhost,workspace)
            if in_scope == 1:
                print("[+] Domain is now in scope:\t" + vhost)
                lib.db.update_vhosts_in_scope(ip,vhost,workspace,1)


def process_nessus_data(nessus_report,workspace,target=None):
    for scanned_host in nessus_report.hosts:
        #print scanned_host.address
        ip = scanned_host.address

        unique_db_ips = lib.db.get_host_by_ip(ip,workspace) #Returns data if IP is in database
        #print(unique_db_ips)
        if unique_db_ips: #If this IP was in the db...
            if not lib.db.get_in_scope_ip(ip,workspace):    # but if it is not in scope...
                print("[+] [{0}] is already in the DB, but not in scope. Adding to scope".format(ip))
                lib.db.update_vhosts_in_scope(ip, ip, workspace, 1)  # update the host to add it to scope, if it was already in scope, do nothing
            # else:
            #     print("[+] [{0}] is already in the DB and considered in scope".format(ip))
        else: #if this ip was not already in the db, create a new host and mark it as in scope
            print("[+] [{0}] is not in the DB. Adding it to DB and to scope".format(ip))
            db_vhost = (ip, ip, 1, 0, workspace)
            db.create_vhost(db_vhost)



        # Step 1: pull all report items in the port scanner family to get every port. The services names are IANA
        #         default as this point, which is why we need the next two loops.
        for report_item in scanned_host.get_report_items:
            if report_item.plugin_family == "Port scanners":
                if report_item.port != "0":
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

# def process_nessus_data2(nessus_report,workspace,target=None):
#     for scanned_host in nessus_report.hosts:
#         #print scanned_host.address
#         ip = scanned_host.address
#         # this if takes care of only acting on the targets specififed at hte command line, if the target
#         # this if takes care of only acting on the targets specififed at hte command line, if the target
#         # param is used.  This is a very simple comparison now. In the future, i'd like to be able to use
#         # the target splitter function and be able to handle ranges and cidr's in the target option
#         if (IPAddress(ip) == target) or (target is None):
#             has_vhost_been_scanned = db.get_inscope_submitted_vhosts_for_ip(ip, workspace)
#             if has_vhost_been_scanned:
#                 answer = raw_input("[!] {0} has already been scanned. Scan it, and all vhosts associated with it, again? [Y\\n] ".format(ip))
#                 if (answer == "Y") or (answer == "y") or (answer == ""):
#                     db.update_vhosts_submitted(ip, ip, workspace, 0)
#             else:
#                 db_vhost = (ip, ip, 1, 0, workspace)  # in this mode all vhosts are in scope
#                 #print(db_vhost)
#                 db.create_vhost(db_vhost)
#             # Step 1: pull all report items in the port scanner family to get every port. The services names are IANA
#             #         default as this point, which is why we need the next two loops.
#             for report_item in scanned_host.get_report_items:
#                 if report_item.plugin_family == "Port scanners":
#                     if report_item.port != "0":
#                         scanned_service_port = report_item.port
#                         scanned_service_protocol = report_item.protocol
#                         scanned_service_name = report_item.service
#                         db_service = db.get_service(ip,scanned_service_port,scanned_service_protocol,workspace)
#
#                         if not db_service:
#                             db_string = (ip,scanned_service_port,scanned_service_protocol,scanned_service_name,workspace)
#                             db.create_service(db_string)
#
#             # Step 2: Cycle through the service detection items and update the services where we have a better idea of
#             #         the real running service on the port. These are a subset of open ports which is why we need loop 1
#             for report_item in scanned_host.get_report_items:
#                 if report_item.plugin_family == "Service detection":
#                     scanned_service_port = report_item.port
#                     scanned_service_protocol = report_item.protocol
#                     scanned_service_name = report_item.service
#                     db_service = db.get_service(ip,scanned_service_port,scanned_service_protocol,workspace)
#                     if not db_service:
#                         db_string = (ip, scanned_service_port, scanned_service_protocol, scanned_service_name, workspace)
#                         db.create_service(db_string)
#                         #print("new service2: " + ip,scanned_service_port,scanned_service_name)
#                     else:
#                         db.update_service(ip,scanned_service_port,scanned_service_protocol,scanned_service_name,workspace)
#                         #print("updating service servicename2: " + ip, scanned_service_port, scanned_service_name)
#                         #print("old service servicename2     : " + ip, scanned_service_port,str(db_service[0][4]))
#
#             # Step 3: This is needed to split up HTTPS from HTTP
#             for report_item in scanned_host.get_report_items:
#                 if (report_item.plugin_name == "TLS Version 1.0 Protocol Detection" or
#                 report_item.plugin_name == "OpenSSL Detection" or
#                 report_item.plugin_name == "SSL Version 2 and 3 Protocol Detection"):
#                     scanned_service_port = report_item.port
#                     scanned_service_protocol = report_item.protocol
#                     scanned_service_name = 'https'
#                     try:
#                         db.update_service(ip, scanned_service_port, scanned_service_protocol, scanned_service_name,
#                                           workspace)
#                     except:
#                         print("if this errors that means there was no service to update as https which is a bigger problem")


def process_nmap_data(nmap_report,workspace, target=None):
    for scanned_host in nmap_report.hosts:
        ip=scanned_host.id


        unique_db_ips = lib.db.get_host_by_ip(ip,workspace) #Returns data if IP is in database
        #print(unique_db_ips)
        if unique_db_ips: #If this IP was in the db...
            if not lib.db.get_in_scope_ip(ip,workspace):    # but if it is not in scope...
                print("[+] [{0}] is already in the DB, but not in scope. Adding to scope".format(ip))
                lib.db.update_vhosts_in_scope(ip, ip, workspace, 1)  # update the host to add it to scope, if it was already in scope, do nothing
            # else:
            #     print("[+] [{0}] is already in the DB and considered in scope".format(ip))
        else: #if this ip was not already in the db, create a new host and mark it as in scope
            print("[+] [{0}] is not in the DB. Adding it to DB and to scope".format(ip))
            db_vhost = (ip, ip, 1, 0, workspace)
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




# def process_nmap_data2(nmap_report,workspace, target=None):
#     for scanned_host in nmap_report.hosts:
#
#         #print(scanned_host)
#         ip=scanned_host.id
#         #print(ip)
#         if (IPAddress(ip) == target) or (target is None):
#             #has_vhost_been_scanned = db.get_unique_inscope_vhosts_for_ip(ip,workspace)
#             has_vhost_been_scanned = db.get_inscope_submitted_vhosts_for_ip(ip,workspace)
#             if has_vhost_been_scanned:
#                 answer = raw_input("[!] {0} has already been scanned. Scan it, and all vhosts associated with it, again? [Y\\n] ".format(ip))
#                 if (answer == "Y") or (answer == "y") or (answer == ""):
#                     db.update_vhosts_submitted(ip,ip,workspace,0)
#             else:
#                 db_vhost = (ip, ip, 1, 0, workspace)  # in this mode all vhosts are in scope
#                 #print(db_vhost)
#                 db.create_vhost(db_vhost)
#
#             for scanned_service_item in scanned_host.services:
#                 if scanned_service_item.state == "open":
#                     scanned_service_port = scanned_service_item.port
#                     scanned_service_name = scanned_service_item.service
#                     scanned_service_protocol = scanned_service_item.protocol
#
#                     if scanned_service_item.tunnel == 'ssl':
#                         scanned_service_name = 'https'
#                     db_service = db.get_service(ip, scanned_service_port, scanned_service_protocol, workspace)
#                     if not db_service:
#                         db_string = (ip, scanned_service_port, scanned_service_protocol, scanned_service_name, workspace)
#                         db.create_service(db_string)
#                     else:
#                         db.update_service(ip, scanned_service_port, scanned_service_protocol, scanned_service_name,
#                                           workspace)
#
#                     #Not using this yet, but I'd like to do send this to searchsploit
#                     try:
#                         scanned_service_product = scanned_service_item.service_dict['product']
#                     except:
#                         scanned_service_product = ''
#                     try:
#                         scanned_service_version = scanned_service_item.service_dict['version']
#                     except:
#                         scanned_service_version = ''
#                     try:
#                         scanned_service_extrainfo = scanned_service_item.service_dict['extrainfo']
#                     except:
#                         scanned_service_extrainfo = ''
#                     #print "Port: {0}\tService: {1}\tProduct & Version: {3} {4} {5}".format(scanned_service_port,scanned_service_name,scanned_service_product,scanned_service_version,scanned_service_extrainfo)