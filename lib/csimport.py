import re
from netaddr import *
from netaddr import IPAddress
import sys
import lib.db
import lib.utils
from lib import db
import urlparse
import os
import csv


def import_out_of_scope(out_of_scope_file,workspace):
    with open(out_of_scope_file) as osf:
        for vhost in osf.readlines():
            vhost = vhost.rstrip()
            # print(vhost)
            # from https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
            ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
            vhost = ansi_escape.sub('', vhost)
            # print("escaped:\t" + vhost)
            if re.match(r'\w', vhost):
                #scope, ip = lib.utils.domain_scope_checker(vhost, workspace)
                is_vhost_in_db = lib.db.is_vhost_in_db(vhost,workspace)
                in_scope, ip = lib.utils.domain_scope_checker(vhost, workspace)
                if is_vhost_in_db:
                    lib.db.update_vhosts_explicit_out_of_scope(vhost,workspace,0,1)
                else:
                    print("[+] Adding vhost to list of explicitly out of scope vhosts:\t" + vhost)
                    is_vhost_in_db = lib.db.is_vhost_in_db(vhost, workspace)
                    if is_vhost_in_db:
                        lib.db.update_vhosts_in_scope(ip, vhost, workspace, 0)
                    else:
                        db_vhost = (ip, vhost, 0, 1, 0, workspace)
                        lib.db.create_vhost(db_vhost)


def import_scope(scope_file,workspace):
    with open(scope_file) as sf:
        for network in sf.readlines():
            if "-" in str(network):
                #print("range found")
                iprange = network.split("-")
                # Convert the first part of the range to an IPAddress object
                rangestart = (IPAddress(iprange[0]))
                # rangeend = (IPAddress(iprange[1]))
                # Hold off on converting the second part. We first need to check if
                # it is a real IP or just the last octet (i.e., 192.168.0.100-110)
                rangeend = iprange[1].rstrip()
                # If there is a period in the second part, we can just cast to IPAddress now
                if "." in rangeend:
                    rangeend = IPAddress(rangeend)
                    netRange = IPRange(rangestart, rangeend)
                    # scopeList is a list of all of the IP addresses, networks, and ranges that are in scope
                    #scopeList.append(netRange)
                    for ip in netRange:
                        ip = str(ip)
                        vhost_explicitly_out_of_scope = lib.db.is_vhost_explicitly_out_of_scope(ip, workspace)
                        if not vhost_explicitly_out_of_scope:  # and if the vhost is not explicitly out of scope
                            is_vhost_in_db = lib.db.is_vhost_in_db(ip, workspace)
                            if is_vhost_in_db:
                                lib.db.update_vhosts_in_scope(ip,ip,workspace,1)
                            else:
                                db_vhost = (ip, ip, 1, 0, 0, workspace)  # add it to the vhosts db and mark as in scope
                                lib.db.create_vhost(db_vhost)
                else:
                    try:
                        # If there is no period, that means we just have the last octet for the second half.
                        # So this part copies the first three octects from the first half range and prepends
                        # it to the single octet given for the second part.
                        startpart = str(rangestart).rsplit('.', 1)[0]
                        rangeend = (IPAddress(str(startpart) + "." + str(rangeend)))


                        netRange = list(iter_iprange(rangestart, rangeend))


                        for ip in netRange:
                            ip = str(ip)
                            vhost_explicitly_out_of_scope = lib.db.is_vhost_explicitly_out_of_scope(ip, workspace)
                            if not vhost_explicitly_out_of_scope:  # and if the vhost is not explicitly out of scope
                                is_vhost_in_db = lib.db.is_vhost_in_db(ip, workspace)
                                if is_vhost_in_db:
                                    lib.db.update_vhosts_in_scope(ip, ip, workspace, 1)
                                else:
                                    db_vhost = (ip, ip, 1, 0, 0, workspace)  # add it to the vhosts db and mark as in scope
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
                try:
                    net = IPNetwork(network)
                    for ip in net:
                        ip = str(ip)
                        vhost_explicitly_out_of_scope = lib.db.is_vhost_explicitly_out_of_scope(ip, workspace)
                        if not vhost_explicitly_out_of_scope:  # and if the vhost is not explicitly out of scope
                            is_vhost_in_db = lib.db.is_vhost_in_db(ip, workspace)
                            if is_vhost_in_db:
                                lib.db.update_vhosts_in_scope(ip, ip, workspace, 1)
                            else:
                                db_vhost = (ip, ip, 1, 0, 0, workspace)  # add it to the vhosts db and mark as in scope
                                lib.db.create_vhost(db_vhost)
                    #scopeList.append(net)
                except:
                    print("[!] Could not read the following IP/network: " + str(network))



def import_vhosts(subdomains_file,workspace):
    workspace_mode = lib.db.get_workspace_mode(workspace)[0][0]
    with open(subdomains_file) as vhosts:
        for vhost in vhosts.readlines():
            vhost = vhost.rstrip()
            #print(vhost)
            # from https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
            ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
            vhost = ansi_escape.sub('', vhost)
            #print("escaped:\t" + vhost)
            if re.match(r'\w', vhost):
                vhost_explicitly_out_of_scope = lib.db.is_vhost_explicitly_out_of_scope(vhost,workspace)
                in_scope, ip = lib.utils.domain_scope_checker(vhost, workspace)
                if not vhost_explicitly_out_of_scope:
                    if workspace_mode == "vapt":
                        if in_scope == 1:
                            print("[+] Found subdomain (in scope):\t\t\t" + vhost)
                            is_vhost_in_db = lib.db.is_vhost_in_db(vhost, workspace)
                            if is_vhost_in_db:
                                lib.db.update_vhosts_in_scope(ip, vhost, workspace, 1)
                            else:
                                db_vhost = (ip, vhost, 1, 0, 0, workspace)  # add it to the vhosts db and mark as in scope
                                lib.db.create_vhost(db_vhost)
                        else:
                            print("[+] Found subdomain (out of scope):\t\t" + vhost)
                            is_vhost_in_db = lib.db.is_vhost_in_db(vhost, workspace)
                            if is_vhost_in_db:
                                lib.db.update_vhosts_in_scope(ip, vhost, workspace, 0)
                            else:
                                db_vhost = (ip, vhost, 0, 0, 0, workspace)  # add it to the vhosts db and mark as out of scope
                                lib.db.create_vhost(db_vhost)

                    elif workspace_mode == "bb":
                        print("[+] Found subdomain (in scope):\t\t\t" + vhost)
                        is_vhost_in_db = lib.db.is_vhost_in_db(vhost, workspace)
                        if is_vhost_in_db:
                            lib.db.update_vhosts_in_scope(ip, vhost, workspace, 1)
                        else:
                            db_vhost = (ip, vhost, 1, 0, 0, workspace)  # add it to the vhosts db and mark as in scope
                            lib.db.create_vhost(db_vhost)



def import_url(url,workspace,output_base_dir):
    celery_path = sys.path[0]
    #config, supported_services = config_parser.read_config_ini()
    #task_id_list = []
    urls_to_screenshot = []
    #url = url.split("?")[0].replace("//", "/")
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

    in_scope, ip = lib.utils.domain_scope_checker(vhost, workspace)
    proto = "tcp"
    vhost_explicitly_out_of_scope = lib.db.is_vhost_explicitly_out_of_scope(vhost, workspace)
    if not vhost_explicitly_out_of_scope:  # and if the vhost is not explicitly out of scope
        if in_scope == 0:
            answer = raw_input(
                "[+] {0} is not in scope. Would you like to to add {1}/{0} to the list of in scope hosts?".format(vhost,
                                                                                                                  ip))
            if (answer == "Y") or (answer == "y") or (answer == ""):
                in_scope = 1
        if in_scope == 1:
            is_vhost_in_db = lib.db.is_vhost_in_db(vhost, workspace)
            if is_vhost_in_db:
                lib.db.update_vhosts_in_scope(ip, vhost, workspace, 1)
                lib.db.update_vhosts_submitted(ip,vhost,workspace,1)
            else:
                db_vhost = (ip, vhost, 1, 0, 1, workspace)  # add it to the vhosts db and mark as in scope
                lib.db.create_vhost(db_vhost)


            if ip == vhost:
                scan_output_base_file_dir = output_base_dir + "/" + ip + "/celerystalkOutput/" + ip + "_" + str(
                    port) + "_" + proto
            else:
                scan_output_base_file_dir = output_base_dir + "/" + ip + "/celerystalkOutput/" + vhost + "_" + str(
                    port) + "_" + proto

            host_dir = output_base_dir + "/" + ip
            host_data_dir = host_dir + "/celerystalkOutput/"
            # Creates something like /pentest/10.0.0.1, /pentest/10.0.0.2, etc.
            lib.utils.create_dir_structure(ip, host_dir)
            # Next two lines create the file that will contain each command that was executed. This is not the audit log,
            # but a log of commands that can easily be copy/pasted if you need to run them again.
            summary_file_name = host_data_dir + "ScanSummary.log"
            summary_file = open(summary_file_name, 'a')

            # db_vhost = (ip, vhost, 1,0,1, workspace)  # in this mode all vhosts are in scope
            # # print(db_vhost)
            # db.create_vhost(db_vhost)

            # Insert port/service combo into services table if it doesnt exist
            db_service = db.get_service(ip, port, proto, workspace)
            if not db_service:
                #db_string = (ip, port, proto, scheme,'','','',workspace)
                db_string = (vhost, port, proto, scheme,'','','',workspace)

                db.create_service(db_string)

            # Insert url into paths table and take screenshot
            db_path = db.get_path(path, workspace)
            if not db_path:
                try:
                    url_path = url.split("/",3)[1]
                except:
                    url_path = ''

                url_screenshot_filename = scan_output_base_file_dir + url_path.replace("/", "_") + ".png"
                db_path = (vhost, port, url.rstrip("/"), 0, 0, url_screenshot_filename,workspace)
                db.insert_new_path(db_path)
                # print("Found Url: " + str(url))
                #urls_to_screenshot.append((url, url_screenshot_filename))

                #lib.utils.take_screenshot(urls_to_screenshot)
                # print(result)


            db_path = (vhost, port, url.rstrip("/"), 0, 0, url_screenshot_filename, workspace)
            lib.db.insert_new_path(db_path)
    else:
        print("[!] {0} is explicitly marked as out of scope. Skipping...".format(vhost))


def update_inscope_vhosts(workspace):
    vhosts = lib.db.get_unique_out_of_scope_vhosts(workspace)
    #print(vhosts)
    for vhost in vhosts:
        #TODO: check to see if host is excplictly out of scope and if so don't add it in scope!!
        vhost = vhost[0].rstrip()
        # from https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
        ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
        vhost = ansi_escape.sub('', vhost)

        #this check is to prevent a host from being marked in scope if it iss explicltly marked out of scope.
        vhost_explicitly_out_of_scope = lib.db.is_vhost_explicitly_out_of_scope(vhost, workspace)
        if not vhost_explicitly_out_of_scope:
            if re.match(r'\w', vhost):
                in_scope,ip = lib.utils.domain_scope_checker(vhost,workspace)
                if in_scope == 1:
                    print("[+] Domain is now in scope:\t" + vhost)
                    lib.db.update_vhosts_in_scope(ip,vhost,workspace,1)
        #else:
        #    print("[!] {0} is explicitly marked as out of scope. Skipping...".format(vhost))






def process_nessus_data(nessus_report,workspace,target=None):
    for scanned_host in nessus_report.hosts:
        #print scanned_host.address
        ip = scanned_host.address

        unique_db_ips = lib.db.is_vhost_in_db(ip,workspace) #Returns data if IP is in database
        #print(unique_db_ips)
        if unique_db_ips: #If this IP was in the db...
            vhost_explicitly_out_of_scope = lib.db.is_vhost_explicitly_out_of_scope(ip, workspace)
            if not vhost_explicitly_out_of_scope:  # and if the vhost is not explicitly out of scope
                if not lib.db.get_in_scope_ip(ip,workspace):    # but if it is not in scope...
                    print("[+] IP is in the DB, but not in scope. Adding to scope:\t[{0}]".format(ip))
                    lib.db.update_vhosts_in_scope(ip, ip, workspace, 1)  # update the host to add it to scope, if it was already in scope, do nothing
                # else:
                #     print("[+] [{0}] is already in the DB and considered in scope".format(ip))
            else:
                print("[!] {0} is explicitly marked as out of scope. Skipping...".format(ip))

        else: #if this ip was not already in the db, create a new host and mark it as in scope
            #note to self: i dont need to check to see if it is explicitly out of scope beccause i already know its not in db at all...
            print("[+] IP not in DB. Adding it to DB and to scope:\t [{0}]".format(ip))
            db_vhost = (ip, ip, 1,0,0, workspace)
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
                        db_string = (ip,scanned_service_port,scanned_service_protocol,scanned_service_name,'','','',workspace)
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
                    db_string = (ip, scanned_service_port, scanned_service_protocol, scanned_service_name,'','','', workspace)
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

def process_qualys_data(qualys_port_services,workspace,target=None):
    with open(qualys_port_services) as f:
        for i, line in enumerate(csv.reader(f, delimiter=','), 1):
            # Skip the header sections. The first entry is on the 7th line
            if i > 6:
                ip = line[0]
                vhost = line[1]
                service = line[2]
                protocol = line[3]
                port = line[4]
                default_service = line[5]
                date_first_seen = line[6]
                date_last_seen = line[7]
                unique_db_ips = lib.db.is_vhost_in_db(ip, workspace)  # Returns data if IP is in database
                # print(unique_db_ips)
                # print("process_nmap_data: " + str(vhosts))
                vhost_explicitly_out_of_scope = lib.db.is_vhost_explicitly_out_of_scope(vhost, workspace)
                if not vhost_explicitly_out_of_scope:  # if the vhost is not explicitly out of scope, add it to db
                    is_vhost_in_db = lib.db.is_vhost_in_db(vhost, workspace)  # Returns data if IP is in database
                    if not is_vhost_in_db:
                        db_vhost = (ip, vhost, 1, 0, 0, workspace)
                        lib.db.create_vhost(db_vhost)
                    else:
                        if not lib.db.get_in_scope_ip(ip, workspace):  # if it is in the DB but not in scope...
                            print("[+] IP is in the DB, but not in scope. Adding to scope:\t[{0}]".format(ip))
                            lib.db.update_vhosts_in_scope(ip, vhost, workspace,
                                                          1)  # update the host to add it to scope, if it was already in scope, do nothing
                else:
                    print("[!] {0} is explicitly marked as out of scope. Skipping...".format(ip))

                if unique_db_ips:  # If this IP was in the db...
                    vhost_explicitly_out_of_scope = lib.db.is_vhost_explicitly_out_of_scope(ip, workspace)
                    if not vhost_explicitly_out_of_scope:  # and if the vhost is not explicitly out of scope
                        if not lib.db.get_in_scope_ip(ip, workspace):  # and if it is not in scope...
                            print("[+] IP is in the DB, but not in scope. Adding to scope:\t[{0}]".format(ip))
                            lib.db.update_vhosts_in_scope(ip, ip, workspace,
                                                          1)  # update the host to add it to scope, if it was already in scope, do nothing
                        # else:
                        #     print("[+] [{0}] is already in the DB and considered in scope".format(ip))
                    else:
                        print("[!] {0} is explicitly marked as out of scope. Skipping...".format(ip))

                else:  # if this ip was not already in the db, create a new host and mark it as in scope
                    # note to self: i dont need to check to see if it is out of scope beccause i already know its not in db at all...
                    print("[+] IP not in DB. Adding it to DB and to scope:\t [{0}]".format(ip))
                    db_vhost = (ip, ip, 1, 0, 0, workspace)
                    db.create_vhost(db_vhost)

                if not service:
                    service = default_service

                db_service = db.get_service(ip, port, protocol, workspace)
                if not db_service:
                    db_string = (ip, port, protocol, service,"", "", "",workspace)
                    db.create_service(db_string)
                else:
                    db.update_service(ip, port, protocol, service,workspace)

                if vhost:
                    db_service = db.get_service(vhost, port, protocol, workspace)
                    if not db_service:
                        db_string = (vhost, port, protocol, service, "", "", "", workspace)
                        db.create_service(db_string)
                    else:
                        db.update_service(vhost, port, protocol, service, workspace)





def process_nmap_data(nmap_report,workspace, target=None):
    print("in proc nmap data")
    workspace_mode = lib.db.get_workspace_mode(workspace)[0][0]
    services_file = open('/etc/services', mode='r')
    services_file_data = services_file.readlines()
    services_file.close()


    #This top part of the for loop determines whether or not to add the host
    for scanned_host in nmap_report.hosts:
        ip=scanned_host.id
        unique_db_ips = lib.db.is_vhost_in_db(ip,workspace) #Returns data if IP is in database
        #print(unique_db_ips)
        vhosts = scanned_host.hostnames
        #print("process_nmap_data: " + str(vhosts))
        for vhost in vhosts:
            #print("process_nmap_data: " + vhost)
            vhost_explicitly_out_of_scope = lib.db.is_vhost_explicitly_out_of_scope(vhost, workspace)
            if not vhost_explicitly_out_of_scope:  # if the vhost is not explicitly out of scope, add it to db
                is_vhost_in_db = lib.db.is_vhost_in_db(vhost, workspace)  # Returns data if IP is in database
                if not is_vhost_in_db:
                    db_vhost = (ip, vhost, 1,0,0, workspace)
                    lib.db.create_vhost(db_vhost)
                else:
                    if not lib.db.get_in_scope_ip(ip, workspace):  # if it is in the DB but not in scope...
                        print("[+] IP is in the DB, but not in scope. Adding to scope:\t[{0}]".format(ip))
                        lib.db.update_vhosts_in_scope(ip, vhost, workspace,1)  # update the host to add it to scope, if it was already in scope, do nothing
            else:
                print("[!] {0} is explicitly marked as out of scope. Skipping...".format(ip))

        if unique_db_ips: #If this IP was in the db...
            vhost_explicitly_out_of_scope = lib.db.is_vhost_explicitly_out_of_scope(ip, workspace)
            if not vhost_explicitly_out_of_scope: #and if the vhost is not explicitly out of scope
                if not lib.db.get_in_scope_ip(ip,workspace):  # and if it is not in scope...
                    print("[+] IP is in the DB, but not in scope. Adding to scope:\t[{0}]".format(ip))
                    lib.db.update_vhosts_in_scope(ip, ip, workspace, 1)  # update the host to add it to scope, if it was already in scope, do nothing
                # else:
                #     print("[+] [{0}] is already in the DB and considered in scope".format(ip))
            else:
                print("[!] {0} is explicitly marked as out of scope. Skipping...".format(ip))

        else: #if this ip was not already in the db, create a new host and mark it as in scope
            #note to self: i dont need to check to see if it is out of scope beccause i already know its not in db at all...
            print("[+] IP not in DB. Adding it to DB and to scope:\t [{0}]".format(ip))
            db_vhost = (ip, ip, 1,0,0, workspace)
            db.create_vhost(db_vhost)


        #Now after the host is added, let's add the ports for that host.
        for scanned_service_item in scanned_host.services:
            if scanned_service_item.state == "open":
                scanned_service_port = scanned_service_item.port
                scanned_service_name = scanned_service_item.service
                scanned_service_protocol = scanned_service_item.protocol
                #print(str(scanned_service_port))
                if scanned_service_item.tunnel == 'ssl':
                    scanned_service_name = 'https'

                if scanned_service_name == "tcpwrapped":
                    try:
                        port_proto = "\t" + str(scanned_service_port) + "/" + str(scanned_service_protocol) + "\t"
                        for line in services_file_data:
                            if port_proto in line:
                                scanned_service_name = line.split("\t")[0]
                    except:
                        pass




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


                db_service = db.get_service(ip, scanned_service_port, scanned_service_protocol, workspace)
                if not db_service:
                    db_string = (ip, scanned_service_port, scanned_service_protocol, scanned_service_name, scanned_service_product, scanned_service_version, scanned_service_extrainfo, workspace)
                    db.create_service(db_string)


                else:
                    db.update_service(ip, scanned_service_port, scanned_service_protocol, scanned_service_name,
                                      workspace)



                output_base_dir = lib.db.get_output_dir_for_workspace(workspace)[0][0]

                file_end_part = "/" + ip + "/celerystalkOutput/" + ip + "_" + str(
                    scanned_service_port) + "_" + scanned_service_protocol + "_"

                scan_output_base_file_dir = os.path.abspath(output_base_dir + file_end_part)

                if (scanned_service_name == 'https') or (scanned_service_name == 'http'):
                    path = scanned_service_name + "://" + ip + ":" + str(scanned_service_port)
                    path = path.rstrip("/")
                    db_path = db.get_path(path, workspace)
                    if not db_path:
                        url_screenshot_filename = scan_output_base_file_dir + ".png"
                        db_path = (ip, scanned_service_port, path, 0, 0, url_screenshot_filename, workspace)
                        db.insert_new_path(db_path)


                for vhost in vhosts:
                    #print("process_nmap_data - add service: " + vhost)
                    db_service = db.get_service(vhost, scanned_service_port, scanned_service_protocol, workspace)
                    if not db_service:
                        print("service didnt exist, adding: " + vhost + str(scanned_service_port))
                        db_string = (vhost, scanned_service_port, scanned_service_protocol, scanned_service_name,
                                     scanned_service_product, scanned_service_version, scanned_service_extrainfo,
                                     workspace)
                        db.create_service(db_string)
                    else:
                        print("service does exist, updating: " + vhost + str(scanned_service_port))

                        db.update_service(vhost, scanned_service_port, scanned_service_protocol, scanned_service_name,
                                          workspace)
                    if ip == vhost:
                        scan_output_base_file_dir = os.path.abspath(output_base_dir + "/" + ip + "/celerystalkOutput/" + ip + "_" + str(
                            scanned_service_port) + "_" + scanned_service_protocol)
                    else:
                        scan_output_base_file_dir = os.path.abspath(output_base_dir + "/" + ip + "/celerystalkOutput/" + vhost + "_" + str(
                            scanned_service_port) + "_" + scanned_service_protocol)

                    if (scanned_service_name == 'https') or (scanned_service_name == 'http'):
                        path = scanned_service_name + "://" + vhost + ":" + str(scanned_service_port)
                        path = path.rstrip("/")
                        db_path = db.get_path(path, workspace)
                        if not db_path:
                            url_screenshot_filename = scan_output_base_file_dir + ".png"
                            db_path = (vhost, scanned_service_port, path, 0, 0, url_screenshot_filename, workspace)
                            db.insert_new_path(db_path)



def importcommand(workspace, output_dir, arguments):
    celery_path = sys.path[0]
    in_scope_hosts_before = lib.db.get_unique_inscope_vhosts(workspace)

    if arguments["-O"]:
        lib.csimport.import_out_of_scope(arguments["-O"],workspace)

    if arguments["-S"]:
        lib.csimport.import_scope(arguments["-S"],workspace)

    if arguments["-f"]:
        if ".csv" in arguments["-f"]:
            lib.csimport.process_qualys_data(arguments["-f"], workspace)
        else:
            if "nessus" in arguments["-f"]:
                nessus_report = lib.utils.nessus_parser(arguments["-f"])
                lib.csimport.process_nessus_data(nessus_report, workspace)
            else:
                nmap_report = lib.utils.nmap_parser(arguments["-f"])
                lib.csimport.process_nmap_data(nmap_report, workspace)
    if arguments["-D"]:
        lib.csimport.import_vhosts(arguments["-D"],workspace)

    if arguments["-u"]:
        lib.csimport.import_url(arguments["-u"],workspace,output_dir)

    # After all files have been proccessed, run this to see if any new hosts are now in scope!
    lib.csimport.update_inscope_vhosts(workspace)

    #This part is really just to tell the user what we have done.
    in_scope_hosts = lib.db.get_unique_inscope_vhosts(workspace)
    new_in_scope_hosts = in_scope_hosts.__len__() - in_scope_hosts_before.__len__()

    if new_in_scope_hosts > 0:
        print("[+] [{0}] hosts were just marked as in scope".format(new_in_scope_hosts))

    if in_scope_hosts.__len__() == 0:
        print("\n[!] There are no in scope hosts in the DB\n")
    else:
        print("[+] [{0}] hosts are currently marked as in scope\n".format(in_scope_hosts.__len__()))