import os
import glob
import bleach
from bleach.sanitizer import Cleaner
import lib.db
import urllib

def paths_report(host):
    all_paths = lib.db.get_all_paths_for_host(host)
    html_code = ""
    for row in all_paths:
        ip,port,path,url_screenshot_filename,workspace = row
        try:
            os.stat(url_screenshot_filename)
            url_screenshot_filename = urllib.quote(url_screenshot_filename)
            html_code = html_code + """\n<div id="linkwrap">\n"""
            html_code = html_code + """<a class="link" href="#">[Screenshot]<span><img src="{1}" alt="image"/></span></a>  <a href="{0}">{0}</a><br>\n""".format(path,url_screenshot_filename)
            html_code = html_code + "</div>\n"
        except:
            print("Could not find screenshot for " + path)
            html_code = html_code + """\n<div id="linkwrap">\n"""
            html_code = html_code + "[Screenshot]  " + """<a href="{0}">{0}</a><br>\n""".format(path)
            html_code = html_code + "</div>\n"
    return html_code




def report(workspace,target_list=None):

    cleaner = Cleaner()
    report_count = 0
    host_report_file_names = []
    if target_list:
        #for loop around targets in scope or somethign...
        a=""
    else:
        #unique_hosts = lib.db.get_unique_hosts_in_workspace(workspace)
        unique_ips = lib.db.get_unique_hosts(workspace)
        unique_vhosts = lib.db.get_unique_inscope_vhosts(workspace)
        if len(unique_ips) == 0:
            print("[!] - There are no hosts in the [{0}] workspace. Try another?\n".format(workspace))
            exit()

    print("\n[+] Generating a report for the [" + workspace + "] workspace (" + str(len(unique_ips)) +") unique IP(s) and (" + str(len(unique_vhosts)) + ") unique vhosts(s)\n")



    # HTML Report
    for ip in unique_ips:
        ip = ip[0]
        unique_vhosts_for_ip = lib.db.get_unique_inscope_vhosts_for_ip(ip, workspace)
        #unique_vhosts_for_ip.append(ip) # This line makes sure the report includes the tools run against the IP itself.
        for vhost in unique_vhosts_for_ip:
            vhost = vhost[0]
            #ip = lib.db.get_vhost_ip(host,workspace)
            #vhost_src_directory = os.path.join(output_dir,str(ip),"celerystalkOutput")
            #print(host_src_directory)
            output_dir = lib.db.get_output_dir_for_workspace(workspace)[0][0]
            workspace_report_directory = os.path.join(output_dir, "celerystalkReports")
            #report_count = report_count +  1
            #These lines create a host specific report file

            try:
                os.stat(workspace_report_directory)
            except:
                os.mkdir(workspace_report_directory)
            host_report_file_name = os.path.join(workspace_report_directory,vhost + '_hostReport.txt')
            host_report_file_names.append([vhost,host_report_file_name])
            host_report_file = open(host_report_file_name, 'w')
            populate_report_data(host_report_file,vhost,workspace)
            host_report_file.close()
            print("[+] Report file (single host): {0}".format(host_report_file_name))

    combined_report_file_name = os.path.join(workspace_report_directory,'Workspace-Report[' + workspace + '].html')
    combined_report_file = open(combined_report_file_name, 'w')
    combined_report_file.write(populate_report_head())



    # Create sidebar navigation
    for host,report in sorted(host_report_file_names):
        #TODO: This is static and will be buggy. I think i need to use a regex here to get the hostname which is in between /hostname/celerystalkoutput
        #host=report.split("/celerystalkOutput")[0].split("/")[2]
        combined_report_file.write("""  <a href="#{0}">{0}</a>\n""".format(host))


    #HTML Report header
    combined_report_file.write("""</div>
<div class="main">

<h1 id="top">celerystalk Report</h1>
\n""")


    #Text Report
    combined_report_file_name_txt = os.path.join(workspace_report_directory,'Workspace-Report[' + workspace + '].txt')
    combined_report_file_txt = open(combined_report_file_name_txt, 'w')

    # Create the rest of the report
    for host,report in sorted(host_report_file_names):
        #host = report.split("/celerystalkOutput")[0].split("/")[2]
        ip = lib.db.get_vhost_ip(host,workspace)
        ip = ip[0][0]
        services = lib.db.get_all_services_for_ip(ip,workspace)

        #These lines write to the parent report file (1 report for however many hosts)
        combined_report_file.write("""<a name="{0}"></a><br>\n""".format(host))
        combined_report_file.write("""<h2>Host Report: {0}</h2>\n""".format(host))
        #TODO: print services for each host - but onlyh for hte ip??
        services_table_html = "<table><tr><th>Port</th><th>Protocol</th><th>Service</th></tr>"
        for id,ip,port,proto,service,workspace in services:
            services_table_html = services_table_html + "<tr><td>{0}</td><td>{1}</td><td>{2}</td>".format(port,proto,service)
        services_table_html = services_table_html + "</table>"
        combined_report_file.write(services_table_html)

        #Text report
        #These lines write to the parent report file (1 report for however many hosts)
        combined_report_file_txt.write('*' * 80 + '\n\n')
        combined_report_file_txt.write('  ' + "Host Report:" + report + '\n')
        combined_report_file_txt.write('\n' + '*' * 80 + '\n\n')

        with open(report, 'r') as host_report_file:
            screenshot_html = paths_report(host)
            combined_report_file.write(screenshot_html)

            combined_report_file.write('<pre>\n')
            for line in host_report_file:
                #HTML report
                line = unicode(line, errors='ignore')
                sanitized = bleach.clean(line)
                combined_report_file.write(sanitized)
                #txt Report
                combined_report_file_txt.write(line)
            combined_report_file.write('</pre>\n')



        combined_report_file.write("\n\n")
        combined_report_file_txt.write("\n\n")


    combined_report_file.write('</pre>\n')
    combined_report_file.close()
    combined_report_file_txt.close()


    print("\n[+] Report file (All workspace hosts): {0} (has screenshots!!!)".format(combined_report_file_name))
    print("[+] Report file (All workspace hosts): {0}\n".format(combined_report_file_name_txt))
    print("\n[+] For quick access, open with local firefox (works over ssh with x forwarding):\n")
    print("\tfirefox " + combined_report_file_name + " &\n")
    print("[+] Or you can copy the celerystalkReports folder, which contains everythign you need to view the report\n")




def populate_report_head():
    #https: // www.w3schools.com / howto / howto_css_fixed_sidebar.asp
    web_head =  ("""<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {
    font-family: "Lato", sans-serif;
    font-size: 16px;
}

.sidenav {
    width: 130px;
    position: fixed;
    z-index: 1;
    top: 20px;
    left: 10px;
    background: #eee;
    overflow-x: hidden;
    padding: 8px 0;
}

.sidenav a {
    padding: 6px 8px 6px 16px;
    text-decoration: none;
    font-size: 12px;
    color: #2196F3;
    display: block;
}

.sidenav a:hover {
    color: #064579;
}

.main {
    margin-left: 140px; /* Same width as the sidebar + left position in px */
    font-size: 14px; /* Increased text to enable scrolling */
    padding: 0px 10px;
}

@media screen and (max-height: 450px) {
    .sidenav {padding-top: 15px;}
    .sidenav a {font-size: 18px;}
}

#linkwrap {
    position:relative;

}
.link img { 
    border:5px solid gray;
    margin:3px;
    float:left;
    width:100%;
    border-style: outset;
    border-radius: 25px;
    display:block;
    position:relative;    
}
.link span { 
    position:absolute;
    visibility:hidden;
    font-size: 16px;
}
.link:hover, .link:hover span { 
    visibility:visible;
    top:0; left:250px; 
    z-index:1;
    
}




</style>
</head>
<body>

<div class="sidenav">
<a href="#top">Top</a>\n""")
    return web_head





def populate_report_data(report_file,vhost,workspace):
    """

    :param report_file:
    :param vhost:
    :param workspace:
    :return:
    """
    reportable_tasks = lib.db.get_report_info_for_ip(workspace,vhost)


    # try:
    #     #Start off the report with the scan summary log that prings which services were detected
    #     summary_file_name = glob.glob(os.path.join(host_output_directory, "*ScanSummary.log"))[0]
    #     with open(summary_file_name, "r") as summary_file:
    #         report_file.write('-' * 80 + '\n')
    #         report_file.write(summary_file_name + '\n')
    #         report_file.write('-' * 80 + '\n')
    #         report_file.write('\n')
    #         for line in summary_file:
    #             report_file.write(line)
    # except:
    #     pass

    for output_file,command_name,command,status,start_time,run_time in reportable_tasks:

        report_file.write('\n\n')
        report_file.write('-' * 50 + '\n')
        report_file.write("Command Name:\t" + command_name + '\n')
        report_file.write("Start Time:\t" + start_time + '\n')
        if status == "COMPLETED":
            report_file.write("Run Time:\t" + run_time + '\n')
        report_file.write("Command:\t" + command + '\n')
        report_file.write("Output File:\t" + output_file + '\n')
        report_file.write("Status:\t\t" + status + '\n')
        report_file.write('-' * 50 + '\n\n')

        linecount = 0

        try:
            with open(output_file, "r") as scan_file:
                for line in scan_file:
                    if linecount < 500:
                        report_file.write(line)
                    linecount = linecount + 1
                if linecount > 500:
                    report_file.write("<<<Snip... Only displaying first 500 of the total " + str(linecount) + " lines>>>\n")
        except:
            print("Error opening file: " + output_file)