import os
import glob
import bleach
from bleach.sanitizer import Cleaner
import lib.db

def paths_report(host):
#     hosts = lib.db.get_unique_hosts_with_paths(workspace)
#     html_code = ""
#     for host in hosts:
#         all_paths = lib.db.get_all_paths_for_host(workspace,host)
#         for row in all_paths:
#             ip,port,path,url_screenshot_filename,workspace = row
#             html_code = html_code + """
#             <div class="hover_img">
#      <a href="#">{0}<span><img src="{1}" alt="image" height="100" /></span></a>
# </div>
#             """.format(path,url_screenshot_filename)

    html_code = ""

    all_paths = lib.db.get_all_paths_for_host(host)
    html_code = """<div id="linkwrap">"""
    for row in all_paths:
        ip,port,path,url_screenshot_filename,workspace = row
#         html_code = html_code + """
#         <div class="hover_img">
#  <a href="#">{0}<span><img src="{1}" alt="image" height="400" /></span></a>
# </div>
#         """.format(path,url_screenshot_filename)

        html_code = html_code + """<a class="link" href="#">{0}<span><img src="{1}" alt="image"/></span></a><br>\n""".format(path,url_screenshot_filename)
    html_code = html_code + "</div>"
    return html_code




def report(output_dir,workspace=None):
    cleaner = Cleaner()
    report_count = 0
    host_report_file_names = []

    for host_output_directory in [y for x in os.walk(output_dir) for y in sorted(glob.glob(os.path.join(x[0], 'celerystalkOutput')))]:
        report_count = report_count +  1
        #These lines create a host specific report file
        host_report_file_name = host_output_directory + "/" + 'report.html'
        host_report_file_names.append(host_report_file_name)
        host_report_file = open(host_report_file_name, 'w')
        #host_report_file.write('<pre>\n')
        populate_report_data(host_report_file, host_output_directory)
        #host_report_file.write('</pre>\n')

        host_report_file.close()

        print("[+] Report file (single host): {0}".format(host_report_file_name))


    if report_count > 0:

        #HTML Report
        combined_report_file_name = output_dir + 'celerystalkReport-combined.html'
        combined_report_file = open(combined_report_file_name, 'w')
        combined_report_file.write(populate_report_head())
        #combined_report_file.write('<pre>\n')

        # Create sidebar navigation
        for report in sorted(host_report_file_names):
            #TODO: This is static and will be buggy. I think i need to use a regex here to get the hostname which is in between /hostname/celerystalkoutput
            host=report.split("/celerystalkOutput")[0].split("/")[2]
            combined_report_file.write("""  <a href="#{0}">{0}</a>\n""".format(host))

        combined_report_file.write("""</div>
<div class="main">

<h1 id="top">celerystalk Report</h1>
\n""")


        #Text Report
        combined_report_file_name_txt = output_dir + 'celerystalkReport-combined.txt'
        combined_report_file_txt = open(combined_report_file_name_txt, 'w')

        # Create the rest of the report
        for report in sorted(host_report_file_names):
            host = report.split("/celerystalkOutput")[0].split("/")[2]

            #These lines write to the parent report file (1 report for however many hosts)
            combined_report_file.write("""<a name="{0}"></a><br>\n""".format(host))
            #combined_report_file.write('*' * 80 + '\n\n')
            #combined_report_file.write(' ' * 20 + "Host Report:" + report + '\n')
            combined_report_file.write("""<h2>Host Report: {0}</h2>\n""".format(host))
            #combined_report_file.write('\n' + '*' * 80 + '\n\n')


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


        print("\n[+] Report file (multiple hosts): {0}".format(combined_report_file_name))
        print("[+] Report file (multiple hosts): {0}\n".format(combined_report_file_name_txt))




def populate_report_head():
    #https: // www.w3schools.com / howto / howto_css_fixed_sidebar.asp
    web_head =  ("""<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {
    font-family: "Lato", sans-serif;
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
    font-size: 12px; /* Increased text to enable scrolling */
    padding: 0px 10px;
}

@media screen and (max-height: 450px) {
    .sidenav {padding-top: 15px;}
    .sidenav a {font-size: 18px;}
}

.hover_img a { position:relative; }
.hover_img a span { position:relative; left:100px; display:none; z-index:99;}
.hover_img a:hover span { display:block; overflow: visible; }

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
	
}
.link span { 
	position:absolute;
	visibility:hidden;
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





def populate_report_data(report_file, host_output_directory):
    """ Takes scan data and writes to report file.
        :param output_dir: Connection object
        :param create_table_sql: a CREATE TABLE statement
        :return:
        """
    try:
        #Start off the report with the scan summary log that prings which services were detected
        summary_file_name = glob.glob(os.path.join(host_output_directory, "*ScanSummary.log"))[0]
        with open(summary_file_name, "r") as summary_file:
            report_file.write('-' * 80 + '\n')
            report_file.write(summary_file_name + '\n')
            report_file.write('-' * 80 + '\n')
            report_file.write('\n')
            for line in summary_file:
                report_file.write(line)
    except:
        pass
    for filename in sorted(glob.glob(os.path.join(host_output_directory, '*.txt'))):
        report_file.write('\n\n')
        report_file.write('-' * 50 + '\n')
        report_file.write(filename + '\n')
        report_file.write('-' * 50 + '\n')
        report_file.write('\n')
        linecount = 0
        with open(filename, "r") as scan_file:
            for line in scan_file:
                if linecount < 500:
                    report_file.write(line)
                linecount = linecount + 1
            if linecount > 500:
                report_file.write("<<<Snip... Only displaying first 500 of the total " + str(linecount) + " lines>>>\n")