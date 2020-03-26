import os
import bleach
from bleach.sanitizer import Cleaner
import lib.db
import lib.config_parser
import lib.utils
import urllib
import time
from netaddr import IPAddress
import hashlib
import glob
import simplejson
from ansi2html import Ansi2HTMLConverter
from ansi2html.util import read_to_unicode



def summary_paths():
    pass

def summary_hosts():
    pass

def summary_services():
    pass

def summary_tasks():
    workspace = lib.db.get_current_workspace()[0][0]
    completed_rows = lib.db.get_completed_tasks(workspace)
    if completed_rows.__len__() > 0:
        for completed_row in completed_rows:
            command = completed_row[1]
            run_time = completed_row[2]
            run_time = time.strftime("%H:%M:%S", time.gmtime(float(run_time)))
            ip = completed_row[3]






def paths_report(host,all_paths):
    #all_paths = lib.db.get_all_paths_for_host(host)
    html_code = ""
    for row in all_paths:
        ip,port,path,url_screenshot_filename,workspace = row
        try:
            os.stat(url_screenshot_filename)
            url_screenshot_filename = urllib.quote(url_screenshot_filename)
            url_screenshot_filename_relative = os.path.join("screens/",url_screenshot_filename.split("/screens/")[1])
            html_code = html_code + """\n<div id="linkwrap">\n"""
            html_code = html_code + """<a href="{0}">{0}</a><br>\n""".format(path)
            html_code = html_code + "\n</div>\n"
        except:
            #print("Could not find screenshot for " + path)
            html_code = html_code + """\n<div id="linkwrap">\n"""
            html_code = html_code + """<a href="{0}">{0}</a><br>\n""".format(path)
            html_code = html_code + "\n</div>\n"
    return html_code


def aquatone_parse_paths():

    output_dir = lib.db.get_output_dir_for_workspace(lib.db.get_current_workspace()[0][0])[0][0]
    aquatone_session_file = os.path.join(output_dir, 'celerystalkReports/aquatone/aquatone_session.json')
    aquatone_report_dir = os.path.join(output_dir, 'celerystalkReports/aquatone/')
    workspace = lib.db.get_current_workspace()[0][0]

    good_sections = ["url", "screenshotPath"]

    with open(aquatone_session_file, 'r') as aquatone_file:
        aquatone_file_json = simplejson.load(aquatone_file)

        for key,value in aquatone_file_json['pages'].iteritems():
            #print(page)
            path = value['url']
            screenshot_path = value['screenshotPath']
            filename = os.path.join(aquatone_report_dir, screenshot_path)
            lib.db.update_path_with_filename(path, filename, workspace)



    #with open(aquatone_report_file) as file:
    #    soup = BeautifulSoup(file, 'html.parser')

    # for site in soup.find_all(class_='page card mb-3'):
    #     print(site.find(class_='card-title'))
    #     path = site.find(class_='card-title').split('card-title">')[1].split('<')[0]
    #
    #     print(site.find(class_='screenshot'))
    #     filename = site.find(class_='screenshot').split('src="')[1].split('"')[0]
    #     filename = os.path.join(aquatone_report_dir,filename)
    #     lib.db.update_path_with_filename(path,filename,workspace)


def paths_report_grid(host,all_paths):
    #all_paths = lib.db.get_all_paths_for_host(host)
    from collections import defaultdict
    d = defaultdict(list)
    row = 0
    for path in all_paths:
        column_number = row % 4
        d[column_number].append((path[3],path[2]))
        row = row + 1

    html_code = '''<div class="row"> '''
    for column in d:
        html_code = html_code + '''<div class="column">'''
        #ip,port,path,url_screenshot_filename,workspace = row
        for url_screenshot_filename,url in d[column]:
            try:
                os.stat(url_screenshot_filename)
                url_screenshot_filename = urllib.quote(url_screenshot_filename)
                url_screenshot_filename_relative = os.path.join("screens/",url_screenshot_filename.split("/screens/")[1])
                html_code = html_code + """<div class="gallery">"""
                html_code = html_code + """<img class="zoom" src="{0}" style="width:100%">\n""".format(url_screenshot_filename_relative)
                html_code = html_code + """<div class="desc"><a href="{0}">{0}</a></div>""".format(url)
                html_code = html_code + """</div>"""
            except:
                pass
        html_code = html_code + "\n</div>\n"
    html_code = html_code + "\n</div>\n"
    return html_code


def paths_report_grid_aquatone(host,all_paths):
    host = host.replace('.', '_')
    #all_paths = lib.db.get_all_paths_for_host(host)
    from collections import defaultdict
    d = defaultdict(list)
    row = 0
    for path in all_paths:
        column_number = row % 4
        d[column_number].append((path[3],path[2]))
        row = row + 1

    html_code = '''<div class="row"> '''
    for column in d:
        html_code = html_code + '''<div class="column">'''
        #ip,port,path,url_screenshot_filename,workspace = row
        for url_screenshot_filename,url in d[column]:
            try:
                os.stat(url_screenshot_filename)
                url_screenshot_filename = urllib.quote(url_screenshot_filename)
                url_screenshot_filename_relative = url_screenshot_filename.split("/celerystalkReports/")[1]

                #url_screenshot_filename_relative = os.path.join("aquatone/",url_screenshot_filename)
                html_code = html_code + """<div class="gallery">"""
                html_code = html_code + """<img class="zoom" src="{0}" style="width:100%">\n""".format(url_screenshot_filename_relative)
                html_code = html_code + """<div class="desc"><a href="{0}">{0}</a></div>""".format(url)
                html_code = html_code + """</div>"""
            except:
                pass
        html_code = html_code + "\n</div>\n"
    html_code = html_code + "\n</div>\n"
    return html_code



def paths_report_grid_aquatone_orig(host):
    #all_paths = lib.db.get_all_paths_for_host(host)

    host = host.replace('.','_')
    output_dir = lib.db.get_output_dir_for_workspace(lib.db.get_current_workspace()[0][0])[0][0]
    aquatone_screenshots_dir = os.path.join(output_dir,'celerystalkReports/aquatone/screenshots/')

    files = glob.glob(aquatone_screenshots_dir + 'http?__' + host + '__*')

    from collections import defaultdict
    d = defaultdict(list)
    row = 0
    for path in files:
        column_number = row % 4
        d[column_number].append((path))
        row = row + 1


    html_code = '''<div class="row"> '''
    for column in d:
        html_code = html_code + '''<div class="column">'''
        #ip,port,path,url_screenshot_filename,workspace = row
        for file in d[column]:
            try:
                os.stat(file)
                #url_screenshot_filename = urllib.quote(url_screenshot_filename)
                #url_screenshot_filename_relative = os.path.join("screens/",url_screenshot_filename.split("/screens/")[1])
                url_screenshot_filename_relative = os.path.join("aquatone/screenshots/",os.path.basename(file))
                html_code = html_code + """<div class="gallery">"""
                html_code = html_code + """<img class="zoom" src="{0}" style="width:100%">\n""".format(url_screenshot_filename_relative)
                #html_code = html_code + """<div class="desc"><a href="{0}">{0}</a></div>""".format(url_screenshot_filename_relative)
                html_code = html_code + """<div class="desc"><a href="aquatone/aquatone_report.html">Aquatone Report</a></div>"""
                html_code = html_code + """</div>"""
            except:
                pass
        html_code = html_code + "\n</div>\n"
    html_code = html_code + "\n</div>\n"
    return html_code

def sort_report_hosts(host_list):
    ip_list = []
    vhost_list = []
    for item in host_list:
        try:
            IPAddress(item)
            ip_list.append(item)
        except:
            vhost_list.append(item)
    sorted(vhost_list)
    ip_list.sort(key=lambda s: map(int, s.split('.')))
    return vhost_list + ip_list


def report(workspace,config_file,target_list=None):
    terminal_width = lib.utils.get_terminal_width()
    if not terminal_width:
        terminal_width = 80
    workspace_mode = lib.db.get_workspace_mode(workspace)[0][0]
    cleaner = Cleaner()
    report_count = 0

    host_report_file_names = []
    if target_list:
        #TODO for loop around targets in scope or somethign...
        a=""
    else:
        #unique_hosts = lib.db.get_unique_hosts_in_workspace(workspace)
        unique_ips = lib.db.get_unique_hosts(workspace)
        unique_submittted_vhosts = lib.db.get_unique_submitted_vhosts(workspace)
        unique_vhosts = lib.db.get_unique_inscope_vhosts(workspace)

        if len(unique_ips) == 0:
            print("[!] - There are no hosts in the [{0}] workspace. Try another?\n".format(workspace))
            exit()
        elif len(unique_submittted_vhosts) == 0:
            print("[!] - There are [{0}] in-scope hosts this workspace, but no hosts have been scanned.\n".format(str(len(unique_vhosts))))
            exit()

    print("\n[+] Generating a report for the [" + workspace + "] workspace (" + str(len(unique_ips)) +") unique in-scope vhosts(s) and (" + str(len(unique_submittted_vhosts)) + ") have been scanned\n")

    print("*" * terminal_width)
    banner = "Text based report file per target"
    print(" " * ((terminal_width / 2) - (len(banner) / 2)) + banner)
    print("*" * terminal_width + "\n")

    # HTML Report
    output_dir = lib.db.get_output_dir_for_workspace(workspace)[0][0]
    workspace_report_directory = os.path.join(output_dir, "celerystalkReports")
    try:
        os.stat(workspace_report_directory)
    except:
        os.mkdir(workspace_report_directory)

    combined_report_file_name = os.path.join(workspace_report_directory,'index.html')
    combined_report_file = open(combined_report_file_name, 'w')
    combined_report_file.write(populate_report_head())

    for vhost in unique_submittted_vhosts:
        vhost = vhost[0]
        is_vhost_submitted = lib.db.is_vhost_submitted(vhost,workspace)
        is_tasks_for_vhost = lib.db.get_unique_non_sim_command_names_for_vhost(vhost,workspace)
        if is_vhost_submitted and is_tasks_for_vhost:
            host_report_file_name = os.path.join(workspace_report_directory,vhost + '_hostReport.txt')
            host_report_file_names.append([vhost,host_report_file_name])
            host_report_file = open(host_report_file_name, 'w')
            populate_report_data(host_report_file,vhost,workspace)
            host_report_file.close()
            print("[+] Report file (single host): {0}".format(host_report_file_name))
    sorted_report_hosts = sort_report_hosts(host_report_file_names)

    workspace = lib.db.get_current_workspace()[0][0]
    outdir = lib.db.get_output_dir_for_workspace(workspace)[0][0]
    aquatone_dir = os.path.join(outdir, 'celerystalkReports/aquatone/')
    try:
        os.stat(aquatone_dir)
        print("\n[+] Generating combined report file with screenshots. This might take a while...")
        print("[+] Grabbing screenshots from Aquatone.")
        aquatone_parse_paths()
    except:
        print("\n[+] Generating combined report file without screenshots. You can always run the screenshot command and")
        print("[+] re-run this report later.")


    # Create sidebar navigation
    #combined_report_file.write('''<font size="5">celerystalk</font><br>\n''')

    for vhost,report in sorted_report_hosts:
        hash=hashlib.md5(vhost).hexdigest()
        #TODO: This is static and will be buggy. I think i need to use a regex here to get the hostname which is in between /hostname/celerystalkoutput
        #host=report.split("/celerystalkOutput")[0].split("/")[2]
        #combined_report_file.write("""  <a href="#{0}">{0}</a>\n""".format(vhost))

        combined_report_file.write("""
            <li class="nav-item">
                <a class="nav-link" href="#{0}">{1}</a>
            </li>       
        \n""".format("loc_" + hash,vhost))

    combined_report_file.write('''
        </ul>
    </nav>\n''')


    combined_report_file.write("""<div class="col-sm-12">\n<div class="header" id="myHeader">\n""")


    #HTML Report header



    #Text Report
    combined_report_file_name_txt = os.path.join(workspace_report_directory,'report.txt')
    combined_report_file_txt = open(combined_report_file_name_txt, 'w')
    unique_non_sim_command_names = lib.db.get_unique_non_sim_command_names(workspace)

    filter_html_body = '''<div id="myBtnContainer">\n'''
    #filter_html_body = filter_html_body + '''<font size="5">celerystalk Report</font><br>\n'''
    filter_html_body = filter_html_body + '''<button class="btn" onclick="filterSelection('all')"> Show all</button>\n'''
    filter_html_body = filter_html_body + '''<a class="btn" href="aquatone/aquatone_report.html" target="_blank">Aquatone Report</a>\n'''
    filter_html_body = filter_html_body + '''<button class="btn" onclick="filterSelection('services')"> Services</button>\n'''
    filter_html_body = filter_html_body + '''<button class="btn" onclick="filterSelection('screenshots')"> Screenshots</button>\n'''
    filter_html_body = filter_html_body + '''<button class="btn" onclick="filterSelection('hostheader')"> Host Header</button>\n'''


    for command_name in unique_non_sim_command_names:
        command_name = command_name[0]
        if not ((command_name == "Screenshots") or (command_name == "nmap_tcp_scan")):
            filter_html_body = filter_html_body + "<button class=\"btn\" onclick=\"filterSelection(\'{0}\')\"> {0}</button>\n".format(command_name)
    filter_html_body = filter_html_body + "</div>"

    combined_report_file.write(filter_html_body)
    combined_report_file.write("""</div>\n<div class="main">\n""")
    combined_report_file.write("""<a name="top"></a>""")
    # Create the rest of the report
    for vhost,report in sorted_report_hosts:
        hash = hashlib.md5(vhost).hexdigest()
        report_string = ""
        ip = lib.db.get_vhost_ip(vhost, workspace)
        ip = ip[0][0]
        if workspace_mode == "vapt":
            services = lib.db.get_all_services_for_ip(ip,workspace)
        elif workspace_mode == "bb":
            services = lib.db.get_all_services_for_ip(vhost,workspace)
        #Text report
        #These lines write to the parent report file (1 report for however many hosts)
        combined_report_file_txt.write('*' * 80 + '\n\n')
        combined_report_file_txt.write('  ' + "Host Report:" + report + '\n')
        combined_report_file_txt.write('\n' + '*' * 80 + '\n\n')

        #These lines write to the parent report file (1 report for however many hosts)
        combined_report_file.write("""\n\n\n\n\n\n\n\n\n\n<div id="{0}">\n""".format("loc_" + hash))
        combined_report_file.write('''\n\n<div class="filterDiv hostheader">\n''')
        combined_report_file.write(
            '''<button class="collapsible">Host Header and Associations[''' + vhost + ''']</button>\n''')
        #combined_report_file.write('''<div class="content">''')
        combined_report_file.write("""<h3>Host Report: {0}</h3>\n""".format(vhost))


        if ip == vhost:
            at_least_one_vhost = False
            unique_vhosts_for_ip = lib.db.get_unique_inscope_vhosts_for_ip(ip, workspace)
            for vhost_for_ip in unique_vhosts_for_ip:
                vhost_for_ip = vhost_for_ip[0]
                hash = hashlib.md5(vhost_for_ip).hexdigest()
                if vhost_for_ip != ip:
                    at_least_one_vhost = True
                    combined_report_file.write("""Associated vhost: <a href="#{0}">{1}</a>\n<br>\n""".format("loc_" + hash,vhost_for_ip))
            if at_least_one_vhost:
                combined_report_file.write("<br>")
        #combined_report_file.write("\n</div>")
        combined_report_file.write("\n</div>")



        services_table_html = "<table><tr><th>Port</th><th>Protocol</th><th>Service</th><th>Product</th><th>Version</th><th>Extra Info</th></tr>"
        for ip,port,proto,service,product,version,extra_info in services:
            services_table_html = services_table_html + "<tr>\n<td>{0}</td>\n<td>{1}</td>\n<td>{2}</td>\n\n<td>{3}</td>\n<td>{4}</td>\n<td>{5}</td></tr>\n".format(port,proto,service,product,version,extra_info)
        services_table_html = services_table_html + "</table>\n<br>\n"

        combined_report_file.write('''\n<div class="filterDiv services">\n''')
        combined_report_file.write('''<button class="collapsible">Services ''' + ''' [''' + vhost + ''']''' + '''</button><br>\n''')
        combined_report_file.write("\n<br>" + services_table_html + "\n<br>")
        combined_report_file.write("\n</div>")

        all_paths = lib.db.get_all_paths_for_host_exclude_404(vhost)
        #print(str(all_paths))
        #print(len(all_paths))
        if len(all_paths) > 0:
            screenshot_html = paths_report(vhost,all_paths)
            #TODO: uncomment this when adding if/then logic if allowing a user to still do it the old way
            #screenshot_grid_html = paths_report_grid(vhost,all_paths)
            #screenshot_grid_html = paths_report_grid_aquatone(vhost)
            screenshot_grid_html = paths_report_grid_aquatone(vhost,all_paths)

            combined_report_file.write('''\n\n<div class="filterDiv screenshots">\n''')
            combined_report_file.write('''<button class="collapsible">Screenshots ''' + ''' [''' + vhost + '''] <center><b>(Click to see all paths)</b></center>''' + '''</button>\n''')
            combined_report_file.write('''<div class="content">''')
            combined_report_file.write('''\n<div class="pathsdata">\n''')
            combined_report_file.write("\n<br>" + screenshot_html + "\n<br>")
            combined_report_file.write("\n</div>")
            combined_report_file.write("\n</div>")
            combined_report_file.write('''\n<div class="screenshotdata">\n''')
            combined_report_file.write("\n<br>" + screenshot_grid_html + "\n<br>")
            #combined_report_file.write("\n</div>")
            combined_report_file.write("\n</div>")
            combined_report_file.write("\n</div>\n")

        #Generate the html code for all of that command output and headers
        report_host_string = populate_report_data_html(vhost, workspace)
        report_string = report_string + report_host_string
        #combined_report_file.write('</pre>\n')
        combined_report_file.write(report_string)
        combined_report_file.write("\n</div>\n")



    combined_report_file.write("\n\n")
    combined_report_file_txt.write("\n\n")





    report_footer = """
<script>
var coll = document.getElementsByClassName("collapsible");
var i;

for (i = 0; i < coll.length; i++) {
  coll[i].addEventListener("click", function() {
    this.classList.toggle("active");
    var content = this.nextElementSibling;
    if (content.style.display === "block") {
      content.style.display = "none";
    } else {
      content.style.display = "block";
    }
  });
}
</script>

<script>
filterSelection("all")
function filterSelection(c) {
  var x, i;
  x = document.getElementsByClassName("filterDiv");
  if (c == "all") c = "";
  for (i = 0; i < x.length; i++) {
    w3RemoveClass(x[i], "show");
    if (x[i].className.indexOf(c) > -1) w3AddClass(x[i], "show");
  }
}

function w3AddClass(element, name) {
  var i, arr1, arr2;
  arr1 = element.className.split(" ");
  arr2 = name.split(" ");
  for (i = 0; i < arr2.length; i++) {
    if (arr1.indexOf(arr2[i]) == -1) {element.className += " " + arr2[i];}
  }
}

function w3RemoveClass(element, name) {
  var i, arr1, arr2;
  arr1 = element.className.split(" ");
  arr2 = name.split(" ");
  for (i = 0; i < arr2.length; i++) {
    while (arr1.indexOf(arr2[i]) > -1) {
      arr1.splice(arr1.indexOf(arr2[i]), 1);     
    }
  }
  element.className = arr1.join(" ");
}

// Add active class to the current button (highlight it)
var btnContainer = document.getElementById("myBtnContainer");
var btns = btnContainer.getElementsByClassName("btn");
for (var i = 0; i < btns.length; i++) {
  btns[i].addEventListener("click", function(){
    var current = document.getElementsByClassName("active");
    btns[i].className = ("btn");
    this.className += " active";
  });
}
</script>

<script>
window.onscroll = function() {myFunction()};

var header = document.getElementById("myHeader");
var sticky = header.offsetTop;

function myFunction() {
  if (window.pageYOffset > sticky) {
    header.classList.add("sticky");
  } else {
    header.classList.remove("sticky");
  }
}
</script>

"""

    combined_report_file.write(report_footer)
    combined_report_file.close()
    combined_report_file_txt.close()

    print("\n")
    print("*" * terminal_width)
    banner = "Combined Report files"
    print(" " * ((terminal_width / 2) - (len(banner) / 2)) + banner )
    print("*" * terminal_width + "\n")

    print("[+] Report file (All workspace hosts): {0} (has screenshots!!!)".format(combined_report_file_name))
    print("[+] Report file (All workspace hosts): {0}\n".format(combined_report_file_name_txt))

    print("*" * terminal_width)
    banner = "Suggestions for viewing your html report:"
    print(" " * ((terminal_width / 2) - (len(banner) / 2)) + banner )
    print("*" * terminal_width + "\n")
    print("[+] Option 1: Open with local firefox (works over ssh with x forwarding)")
    print("\t\tfirefox " + combined_report_file_name + " &")
    print("[+] Option 2: Use Python's SimpleHTTPserver (Don't serve this on a publicly accessible IP!!)")

    try:
        simple_server_port = lib.config_parser.get_simpleserver_port(config_file)
        print("\t\tcd {0} && python -m SimpleHTTPServer {1}".format(workspace_report_directory, str(simple_server_port)))
    except:
        print("\t\tcd {0} && python -m SimpleHTTPServer 27007".format(workspace_report_directory))

    #print("\t\tcd {0} && python -m SimpleHTTPServer 27007".format(workspace_report_directory))
    print("[+] Option 3: Copy the {0} folder to another machine and view locally.\n\n".format(workspace_report_directory))



def populate_report_head():
    #https: // www.w3schools.com / howto / howto_css_fixed_sidebar.asp
    web_head =  ("""<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css">
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.3/umd/popper.min.js"></script>
<script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.1.3/js/bootstrap.min.js"></script>
<style>
body {
    font-family: "Lato", sans-serif;
    margin: unset;
    background: dimgray;
}

ul.nav-pills {
    top: 0px;
    position: fixed;
    overflow-x: auto;
    overflow-y: auto;
    display: unset;
    z-index: 1;
    left: 0;
    bottom: 0;
    font-size: 12px;
    background: black;
    overflow-wrap: break-word;
    width: 170px;
    background-color: dimgray;	
}

ul.nav-pills a {
    color: lightgray;
}


table {
}

th, td {
    text-align: left;
    padding: 8px;
    border-radius: 5px;
    -moz-border-radius: 5px;
    padding: 5px;
}

tr:nth-child(even){background-color: #f2f2f2}

th {
    background-color: #777;
    color: white;
    padding: 4px;
}

.title {
  background: #d1e7ff;
  color: #f1f1f1;
  margin-left: 160px; /* Same width as the sidebar + left position in px */
  font-size: 28px; /* Increased text to enable scrolling */
}

.header {
  background: white;
  margin-left: 170px; /* Same width as the sidebar + left position in px */
  font-size: 14px; /* Increased text to enable scrolling */
  padding: 5px 5px 10px 10px;
  border-radius: 11px 11px 0px 0px;
 }

_myBtnContainer {
    width: 100%;
}

.topcontent {
  padding: 16px;
}

.sticky {
  position: sticky;
  top: 0;
}

.sticky + .topcontent {
  padding-top: 142px;
  width: 100px;
}

.sticky + .main {
  padding-top: 142px;
  border-radius: 10px;
}

.sidenav {
    width: 160px;
    position: fixed;
    z-index: 1;
    top: 0;
    left: 0;
    bottom: 0;
    background: #eee;
    overflow-x: auto;
    overflow-y: auto
    padding: 8px 0;
    display: block;
}

.sidenav a {
    padding: 6px 12px 6px;
    text-decoration: none;
    font-size: 12px;
    color: #2196F3;
    display: block;
}

.sidenav a:hover {
    color: #064579;
}

.main {
    margin-left: 170px; /* Same width as the sidebar + left position in px */
    font-size: 12px; /* Increased text to enable scrolling */
    padding: 10px 10px;
    background: white;
    border-radius: 0px 0px 10px 10px;

        
}

div.desc {
    padding: 1px;
    text-align: center;
    overflow-wrap: break-word;
    color: white;
    font-size: smaller
}

div.desc a {
    color: white;
}

div.gallery {
    margin: 1px;
}

.host_header {
  position: -webkit-sticky;
  position: sticky;
  top: 12%;
  right: 0px;
  background-color: steelblue;
  color: white;
  border: none;
  outline: none;
  border-radius: 10px;
  padding: 20px 10px;
  float: right; 
  font-size: 14px;
  margin-right: 5%;
  z-index:100;
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
    max-height:400px;S
}
.link:hover, .link:hover span { 
    visibility:visible;
    top:0; left:280px; 
    z-index:100;
}
.collapsible {
    background-color: #777;
    color: white;
    cursor: pointer;
    padding: 4px;
    width: 95%;
    border: none;
    border-radius: 12px;
    text-align: left;
    text-indent: 5px;    
    outline: none;
}

.active, .collapsible:hover {
    background-color: #555;
}

.content {
    padding: 0 18px;
    display: none;
    font-size: 12px;
    overflow: auto;
    max-height: 500px;    
    width: 95%;
    background-color: #f1f1f1;    
}

.filterDiv {
  margin: 2px;
  display: none;
}

.filedata {
  margin: 2px;  
  max-height: 500px;
  overflow: auto;
  width: 95%;
}

.pathsdata {
  margin: 2px;  
  max-height: 600px;
  overflow: auto;
  width: 95%;
  text-indent: 10px;
}

.screenshotdata {
  max-height: 600px;
  overflow: auto;
  width: 95%;
  background: dimgray;
  border-radius: 10px;
  margin: 5px;
  padding: 15px;
  
}



.show {
  display: block;
}

.container {
  margin-top: 10px;
  
}

/* Style the buttons */
.btn {
  border: none;
  outline: none;
  border-radius: 10px;
  padding: 6px 3px;
  font-size: 12px;
  margin-bottom:4px;

}

.btn:hover {
  background-color: #ddd;
}

.btn.active {
  background-color: #666;
  color: white;
}


* {
    box-sizing: border-box;
}

.row {
    display: -ms-flexbox; /* IE10 */
    display: flex;
    -ms-flex-wrap: wrap; /* IE10 */
    flex-wrap: wrap;
    padding: 0 4px;
}

/* Create four equal columns that sits next to each other */
.column {
    -ms-flex: 25%; /* IE10 */
    flex: 25%;
    max-width: 25%;
    padding: 0 4px;
}

.column img {
    margin-top: 8px;
    vertical-align: middle;
}

/* Responsive layout - makes a two column-layout instead of four columns */
@media screen and (max-width: 800px) {
    .column {
        -ms-flex: 50%;
        flex: 50%;
        max-width: 50%;
    }
}

/* Responsive layout - makes the two columns stack on top of each other instead of next to each other */
@media screen and (max-width: 600px) {
    .column {
        -ms-flex: 100%;
        flex: 100%;
        max-width: 100%;
    }
}

.zoom {
    transition: transform .2s; /* Animation */
    margin: 0 auto;
}

.zoom:hover {
    transform: scale(1.5); 
    transform-origin: 0% 0%;
	position: relative;
	transform-style: preserve-3d;
}


</style>
</head>
<body data-spy="scroll" data-target="#myScrollspy" data-offset="1">
<br>
<div class="container-fluid">
  <div class="row">
    <nav class="left" id="myScrollspy">
      <ul class="nav nav-pills nav-stacked">
        <li>
            <center><b><font size="4" color="lightgray" family="Tahoma">celerystalk</font></b><br><font color="lightgray" family="Tahoma">v1.2</font></center>
        </li> 
        <li class="nav-item">
          <a class="nav-link active" href="#top">Top&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</a>
        </li>\n       
        """)
    return web_head


def populate_report_data(report_file,vhost,workspace):
    """

    :param report_file:
    :param vhost:
    :param workspace:
    :return:
    """

    reportable_output_files_for_vhost = lib.db.get_reportable_output_files_for_vhost(workspace,vhost)
    for vhost_output_file in reportable_output_files_for_vhost:
        vhost_output_file = vhost_output_file[0]
        normalized_output_file = os.path.normpath(vhost_output_file)
        tasks_for_output_file = lib.db.get_tasks_for_output_file(workspace,vhost,vhost_output_file)
        for command_name,command,status,start_time,run_time in tasks_for_output_file:
            #Don't print header info for simulation jobs
            if not command.startswith('#'):
                try:
                    if os.stat(normalized_output_file).st_size == 0:
                        report_file.write('\n')
                        report_file.write('-' * 50 + '\n')
                        report_file.write("Command Name:\t" + command_name + " (No data produced)\n")

                        # report_file.write("{0} did not produce any data\n".format(command_name))
                        report_file.write('-' * 50)
                    else:
                        report_file.write('\n\n')
                        report_file.write('-' * 50 + '\n')
                        report_file.write("Command Name:\t" + command_name + '\n')
                        report_file.write("Start Time:\t" + start_time + '\n')
                        if status == "COMPLETED":
                            report_file.write("Run Time:\t" + run_time + '\n')
                        report_file.write("Command:\t" + command + '\n')
                        report_file.write("Output File:\t" + normalized_output_file + '\n')
                        report_file.write("Status:\t\t" + status + '\n')
                        report_file.write('-' * 50 + '\n\n')
                except OSError, e:
                    report_file.write('\n')
                    report_file.write('-' * 50 + '\n')
                    report_file.write("Command Name:\t" + command_name+ '\n')
                    report_file.write("Command:\t" + command + '\n')
                    report_file.write("\nNo such file or directory: " + normalized_output_file + "\n")
                    # report_file.write("{0} did not produce any data\n".format(command_name))
                    report_file.write('-' * 50)



        linecount = 0
        try:
            with open(normalized_output_file, "r") as scan_file:
                for line in scan_file:
                    if linecount < 300:
                        report_file.write(line)
                    linecount = linecount + 1
                if linecount > 300:
                    report_file.write("\nSnip... Only displaying first 300 of the total " + str(
                        linecount) + " lines...\n")
        except IOError, e:
            #dont tell the user at the concole that file didnt exist.
            pass


def populate_report_data_html(vhost,workspace):
    """

    :param report_file:
    :param vhost:
    :param workspace:
    :return:
    """
    report_host_html_string = ""
    command_header_html = ""
    file_contents_html = ""

    reportable_output_files_for_vhost = lib.db.get_reportable_output_files_for_vhost(workspace,vhost)
    for vhost_output_file in reportable_output_files_for_vhost:
        vhost_output_file = vhost_output_file[0]
        normalized_output_file = os.path.normpath(vhost_output_file)
        tasks_for_output_file = lib.db.get_tasks_for_output_file(workspace,vhost,vhost_output_file)
        if len(tasks_for_output_file) > 1:
            command_name, command, status, start_time, run_time = tasks_for_output_file[0]
            if not ((command_name == "Screenshots") or (command_name == "nmap_tcp_scan")):
                report_host_html_string = report_host_html_string + '''<div class="filterDiv ''' + command_name + '''">\n'''
                for command_name,command,status,start_time,run_time in tasks_for_output_file:
                    start_time = time.strftime("%m/%d/%Y %H:%M:%S", time.localtime(float(start_time)))
                    if run_time:
                        run_time = time.strftime('%H:%M:%S', time.gmtime(float(run_time)))
                    # Don't print header info for simulation jobs
                    if not command.startswith('#'):
                        command_header_html = get_command_header_and_info(vhost,normalized_output_file,command_name,command,status,start_time,run_time)
                        report_host_html_string = report_host_html_string + command_header_html
                file_contents_html = convert_file_contents_to_html(normalized_output_file)
                report_host_html_string = report_host_html_string + file_contents_html
                report_host_html_string = report_host_html_string + "        </div>\n"
        elif len(tasks_for_output_file) == 1:
            command_name, command, status, start_time, run_time = tasks_for_output_file[0]
            if not ((command_name == "Screenshots") or (command_name == "nmap_tcp_scan")):
                report_host_html_string = report_host_html_string + '''<div class="filterDiv ''' + command_name + '''">\n'''
                start_time = time.strftime("%m/%d/%Y %H:%M:%S", time.localtime(float(start_time)))
                if run_time:
                    run_time = time.strftime('%H:%M:%S', time.gmtime(float(run_time)))
                if not command.startswith('#'):
                    command_header_html = get_command_header_and_info(vhost,normalized_output_file,command_name, command, status, start_time,run_time)
                    file_contents_html = convert_file_contents_to_html(normalized_output_file)

                    report_host_html_string = report_host_html_string + command_header_html + file_contents_html
                report_host_html_string = report_host_html_string + "        </div>\n"
    return report_host_html_string

def get_command_header_and_info(vhost,normalized_output_file,command_name,command,status,start_time,run_time):
    command_header_html_string = ""

    command_header_html_string = command_header_html_string + '''<button class="collapsible">''' + command_name + ''' [''' + vhost + ''']''' + '''</button>\n'''
    command_header_html_string = command_header_html_string + '''<div class="content">'''
    command_header_html_string = command_header_html_string + '''<table>'''
    try:
        command_header_html_string = command_header_html_string + "<tr><td>Start Time:</td><td>" + start_time + '</td></tr>\n'
        if status == "COMPLETED":
            command_header_html_string = command_header_html_string + "<tr><td>Run Time:</td><td>" + run_time + '</td></tr>\n'
        command_header_html_string = command_header_html_string + "<tr><td>Command:</td><td>" + command + '</td></tr>\n'
        command_header_html_string = command_header_html_string + "<tr><td>Output File:</td><td>" + normalized_output_file + '</td></tr>\n'
        if os.stat(normalized_output_file).st_size == 0:
            command_header_html_string = command_header_html_string + "<tr><td>Status:</td><td>" + status + ' [No Output Data]</td></tr>\n'
        else:
            command_header_html_string = command_header_html_string + "<tr><td>Status:</td><td>" + status + '</td></tr>\n'
    except OSError, e:
        command_header_html_string = command_header_html_string + "<tr><td>Command:</td><td>" + command + '</td></tr>\n'
        command_header_html_string = command_header_html_string + "\nError!: No such file or directory: " + normalized_output_file + "</td></tr>\n"
        # command_header_html_string = command_header_html_string +  "{0} did not produce any data\n".format(command_name))
    command_header_html_string = command_header_html_string + "</table>\n</div>\n"
    return command_header_html_string

def convert_file_contents_to_html(normalized_output_file):
    # This is the part that reads the contents of each output file
    linecount = 0
    # file_html_string = file_html_string + "        <pre>"
    file_html_string = "        <div class=\"filedata\">"


    try:
        with open(normalized_output_file, "r") as scan_file:
            for line in scan_file:
                line = unicode(line, errors='ignore')
                try:
                    sanitized = bleach.clean(line)
                except:
                    print(
                        "[!] Could not output santize the following line (Not including it in report to be safe):")
                    print("     " + line)
                    sanitized = ""
                if linecount < 300:
                    file_html_string = file_html_string + sanitized + "<br />"
                linecount = linecount + 1
            if linecount > 300:
                file_html_string = file_html_string + "\nSnip... Only displaying first 300 of the total " + str(
                    linecount) + " lines...\n"
    except IOError, e:
        # dont tell the user at the concole that file didnt exist.
        pass
    file_html_string = file_html_string + "        </div>"
    return file_html_string

def convert_file_contents_to_html2(normalized_output_file):
    #conv = Ansi2HTMLConverter()
    with open(normalized_output_file, "rb") as scan_file:
        test_data = "".join(read_to_unicode(scan_file))
        #expected_data = [e.rstrip('\n') for e in read_to_unicode(scan_file)]
        html = Ansi2HTMLConverter().convert(test_data, ensure_trailing_newline=True)

    return html


def command_footer_html(tasks_for_output_file):
    for task in tasks_for_output_file:
        print {}