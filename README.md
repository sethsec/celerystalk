# celerystalk

celerystalk helps you automate your network scanning/enumeration process with asynchronous jobs (aka *tasks*) while retaining full control of which tools you want to run.    

* **Configurable** - Some common tools are in the default config, but you can add any tool you want
* **Service Aware** - Uses nmap/nessus service names rather than port numbers to decide which tools to run 
* **Consistency** - Scan each service the same way so you don't have to keep track of what you ran against each host 
* **Scalability** - Designed for scanning multiple hosts, but works well for scanning one host at a time
* **VirtualHosts** - Supports subdomain recon and virtualhost scanning using the -d flag
* **Workspaces** - Supports multiple workspaces, inspired by Metasploit workspaces
* **Job Control** - Supports canceling, pausing, and resuming of tasks, inspired by Burp scanner
* **Easy to use** - Uses a command based interface inspired by CrackMapExec 
* **Measure twice, cut once** - A simulation mode shows you which tools will run without running them
* **Flexible** - Target only a subset of the hosts scanned in an previous Nmap/Nessus file
* **Audit Log** - Every executed command is logged in a file which contains start and end times, and the duration 

Under the hood:
* **Celery** - [Celery](http://www.celeryproject.org/) is used to execute your commands asynchronously 
* **Redis** - Celery submits tasks to, and pulls tasks from, a local instance of Redis (binds to localhost)
* **Selenium** is used with geckodriver to take *screenshots of every url identified* using gobuster and Photon (spider)
* **SQLite** is used to persist data and manage workspaces
     

## Install/Setup

* **Supported Operating Systems:** Kali (Setup script supports ubuntu, but for now you're on your own for installing tools like gobuster, nikto, etc...)
* **Supported Python Version:** 2.x

```
# git clone https://github.com/sethsec/celerystalk.git
# cd celerystalk/setup
# ./install.sh
# cd ..
# ./celerystalk -h
```
**At this time you must install and run celerystalk as root** - Sudo won't work either - any command that requires root that is kicked off asynchronously after the sudo grace period ends will fail to run.  


## Using celerystalk - The basics

**[CTF/HackTheBox mode]** - How to scan one host by IP only

```
# nmap 10.10.10.10 -Pn -p- -sV -oX tenten.xml                       # Run nmap
# ./celerystalk scan -f tenten.xml -o /htb                          # Run all enabled commands
# ./celerystalk query watch (then Ctrl+c)                           # Wait for scans to finish
# ./celerystalk report                                              # Generate report
# firefox /htb/celerystalkReports/Workspace-Report[Default.html] &  # View report 
```

[![asciicast](https://asciinema.org/a/Tg0FkxF7rXksYniwB5cbmk1Qg.png)](https://asciinema.org/a/Tg0FkxF7rXksYniwB5cbmk1Qg)

**[URL Mode]** - How to scan a URL (scans the specified path, not the root).  

```
# ./celerystalk scan -u http://10.10.10.10/secret_folder/ -o /assessments/client t  # Run all enabled commands
# ./celerystalk query watch (then Ctrl+c)                                           # Wait for scans to finish
# ./celerystalk report                                                              # Generate report
# firefox /assessments/client/celerystalkReports/Workspace-Report[Default].html &   # View report 
```

**[Vulnerability Assessment Mode]** - How to scan a list of in-scope hosts/networks and any subdomains that resolve to any of the in-scope IPs

```
# nmap -iL client-inscope-list.txt -Pn -p- -sV -oX client.xml                       # Run nmap
# ./celerystalk scan -f client.xml -o /assessments/client -d client.com,client.net  # Run all enabled commands
# ./celerystalk query watch (then Ctrl+c)                                           # Wait for scans to finish
# ./celerystalk report                                                              # Generate report
# firefox /assessments/client/celerystalkReports/Workspace-Report[Default].html &   # View report 
```
[![asciicast](https://asciinema.org/a/1Ucw8RKjwmWMaBAovXa772c4z.png)](https://asciinema.org/a/1Ucw8RKjwmWMaBAovXa772c4z)


**[Bug Bounty Mode]** - How to scan a bug bounty program by simply defining what domains/hosts are in scope and what is out of scope.
```bash
Not ready yet.  Coming soon...
```


## Using celerystalk - Some more detail

1. **Run Nmap or Nessus:** 
     
   * Nmap: Run nmap against your target(s). Required: enable version detection (-sV) and output to XML (-oX filename.xml). All other nmap options are up to you. Here are some examples:
     ```
      nmap target(s) -Pn -p- -sV -oX filename.xml 
      nmap -iL target_list.txt -Pn -sV -oX filename.xml
     ```
   * Nessus: Run nessus against your target(s) and export results as a .nessus file
    

1. **Configure which tools you'd like celerystalk to execute:** The install script drops a config.ini file in the celerystalk folder. The config.ini script is broken up into three sections:  

    ***Service Mapping*** - The first section normalizes Nmap & Nessus service names for celerystalk (this idea was created by @codingo_ in [Reconnoitre](https://github.com/codingo/Reconnoitre) AFAIK).  
    ```
    [nmap-service-names]
    http = http,http-alt,http-proxy,www,http?
    https = ssl/http,https,ssl/http-alt,ssl/http?
    ftp = ftp,ftp?
    mysql = mysql
    dns = dns,domain,domain
    ```

    ***Domain Recon Tools*** - The second section defines the tools you'd like to use for subdomain discovery (an optional feature):
    ```
    [domain-recon]
    amass               : /opt/amass/amass -d [DOMAIN]
    sublist3r           : python /opt/Sublist3r/sublist3r.py -d [DOMAIN]
    ```  

    ***Service Configuration*** - The rest of the confi.ini sections define which commands you want celerystalk to run for each identified service (i.e., http, https, ssh).    
    * Disable any command by commenting it out with a ; or a #. 
    * Add your own commands using [TARGET],[PORT], and [OUTPUT] placeholders.
    
    Here is an example:   
     ```
    [http]
    whatweb             : whatweb http://[TARGET]:[PORT] -a3 --colour=never > [OUTPUT].txt
    cewl                : cewl http://[TARGET]:[PORT]/ -m 6 -w [OUTPUT].txt
    curl_robots         : curl http://[TARGET]:[PORT]/robots.txt --user-agent 'Googlebot/2.1 (+http://www.google.com/bot.html)' --connect-timeout 30 --max-time 180  > [OUTPUT].txt
    nmap_http_vuln      : nmap -sC -sV -Pn -v -p [PORT] --script=http-vuln* [TARGET] -d -oN [OUTPUT].txt -oX [OUTPUT].xml --host-timeout 120m --script-timeout 20m
    nikto               : nikto -h http://[TARGET] -p [PORT] &> [OUTPUT].txt
    gobuster-common     : gobuster -u http://[TARGET]:[PORT]/ -k -w /usr/share/seclists/Discovery/Web-Content/common.txt -s '200,204,301,302,307,403,500' -e -n -q > [OUTPUT].txt
    photon              : python /opt/Photon/photon.py -u http://[TARGET]:[PORT] -o [OUTPUT]
    ;gobuster_2.3-medium : gobuster -u http://[TARGET]:[PORT]/ -k -w /usr/share/wordlists/dirbuster/directory-list-lowercase-2.3-medium.txt -s '200,204,301,307,403,500' -e -n -q > [OUTPUT].txt
    ```
1. **Launch Scan:** Run celerystalk scan using the nmap or nessus XML file.  It will submit tasks to celery which asynchronously executes them and logs output to your output directory. 

    If you specify the -d flag, celerystalk will perfrom subdomain recon using your specified tools.  It will then check to see if the IP associated with each subdomain found is in the list of IP's in your nmap/nessus file.  If the subdomain is in scope celerystalk will scan it using the subdomain/virtualhost.
     
    ```    
    Start from Nmap XML file:   celerystalk scan -f /pentest/nmap.xml -o /pentest
    Start from Nessus file:     celerystalk scan -f /pentest/scan.nessus -o /pentest
    Find in scope vhosts:       celerystalk scan -f <file> -o /pentest -d domain1.com,domain2.com
    Specify workspace:          celerystalk scan -f <file> -o /pentest -w test    
    Scan subset hosts in XML:   celerystalk scan -f <file> -o /pentest -w test -t 10.0.0.1,10.0.0.3
                                celerystalk scan -f <file> -o /pentest -w test -t 10.0.0.100-200
                                celerystalk scan -f <file> -o /pentest -w test -t 10.0.0.0/24
    Simulation mode:            celerystalk scan -f <file> -o /pentest -s
    ```   
1. **Query Status:** Asynchronously check the status of the tasks queue as frequently as you like. The watch mode actually executes the linux watch command so you don't fill up your entire terminal buffer.
    ```
    Query Tasks:                celerystalk query [-w workspace]
                                celerystalk query [-w workspace] watch                               
                                celerystalk query [-w workspace] brief
                                celerystalk query [-w workspace] summary                                
                                celerystalk query [-w workspace] summary watch
    ```

1. **Cancel/Pause/Resume Tasks:** Cancel/Pause/Resume any task(s) that are currently running or in the queue.

    * *Canceling a running task* will send a *kill -TERM*.  
    * *Canceling a queued task* will make celery ignore it (uses celery's revoke).
    * *Canceling all tasks* will kill running tasks and revoke all queued tasks.    
    * *Pausing a single task* uses *kill -STOP* to suspend the process.
    * *Pausing all tasks* attemps to *kill -STOP* all running tasks, but it is a little wonky and you mind need to run it a few times. It is possible a job completed before it was able to be paused, which means you will have a worker that is still accepting new jobs.
    * *Resuming tasks* sends a *kill -CONT* which allows the process to start up again where it left off.    
    ```
    Cancel/Pause/Resume Tasks:  celerystalk <verb> 5,6,10-20          #Cancel/Pause/Resume tasks 5, 6, and 10-20
                                celerystalk <verb> all                #Cancel/Pause/Resume all tasks from default workspaces
                                celerystalk <verb> all -w test        #Cancel/Pause/Resume all tasks in the test workspace
    ```
1. **Run Report:** Run a report which combines all of the tool output into an html file and a txt file. Run this as often as you like. Each time you run the report it overwrites the previous report.  
    ```
    Create Report:              celerystalk report [-w workspace]     #Create a report for all scanneed hosts in a workspace
    ```
    
    Screenshot:
     
    ![](https://preview.ibb.co/ixYTsz/report.png)

## Usage
```
Usage:
    celerystalk scan -f <nmap_file> -o <output_dir> [-w <workspace>] [-t <targets>] [-d <domains>] [-s]
    celerystalk query [-w <workspace>] ([full] | [summary] | [brief]) [watch]
    celerystalk query [-w <workspace>] [watch] ([full] | [summary] | [brief])
    celerystalk report [-w <workspace>]
    celerystalk cancel ([all]|[<task_ids>]) [-w <workspace>]
    celerystalk pause  ([all]|[<task_ids>]) [-w <workspace>]
    celerystalk resume ([all]|[<task_ids>]) [-w <workspace>]
    celerystalk shutdown
    celerystalk (help | -h | --help)

Options:
    -h --help         Show this screen
    -v --version      Show version
    -f <nmap_file>    Nmap xml import file
    -o <output_dir>   Output directory
    -t <targets>      Target(s): IP, IP Range, CIDR
    -w <workspace>    Workspace [default: Default]
    -d --domains      Domains to scan for vhosts
    -s --simulation   Simulation mode.  Submit tasks comment out all commands

Examples:

    Start from Nmap XML file:   celerystalk scan -f /pentest/nmap.xml -o /pentest
    Start from Nessus file:     celerystalk scan -f /pentest/scan.nessus -o /pentest
    Specify workspace:          celerystalk scan -f <file> -o /pentest -w test
    Find in scope vhosts:       celerystalk scan -f <file> -o /pentest -d domain1.com,domain2.com
    Scan subset hosts in XML:   celerystalk scan -f <file> -o /pentest -w test -t 10.0.0.1,10.0.0.3
                                celerystalk scan -f <file> -o /pentest -w test -t 10.0.0.100-200
                                celerystalk scan -f <file> -o /pentest -w test -t 10.0.0.0/24
    Simulation mode:            celerystalk scan -f <file> -o /pentest -d
    Query Tasks:                celerystalk query [-w workspace]
                                celerystalk query [-w workspace] watch
                                celerystalk query [-w workspace] summary
                                celerystalk query [-w workspace] summary watch
    Create Report:              celerystalk report [-w workspace]     #Create a report for all scanneed hosts in a workspace 
    Cancel/Pause/Resume Tasks:  celerystalk <verb> 5,6,10-20          #Cancel/Pause/Resume tasks 5, 6, and 10-20
                                celerystalk <verb> all                #Cancel/Pause/Resume all tasks from all workspaces
                                celerystalk <verb> all -w test        #Cancel/Pause/Resume all tasks in the test workspace
                                celerystalk <verb> 10.0.0.1           #Cancel/Pause/Resume all tasks related to 10.0.0.1
                                celerystalk <verb> 10.0.0.0/24        #Cancel/Pause/Resume all tasks related to 10.0.0.0/24
    Shutdown Celery processes:  celerystalk shutdown
```

## Credit
This project was inspired by many great tools:  
1. https://github.com/codingo/Reconnoitre by @codingo_
1. https://github.com/frizb/Vanquish by @frizb
1. https://github.com/leebaird/discover by @discoverscripts
1. https://github.com/1N3/Sn1per
1. https://github.com/SrFlipFlop/Network-Security-Analysis by @SrFlipFlop

Thanks to @offensivesecurity and @hackthebox_eu for their lab networks

Also, thanks to:
1. @decidedlygray for pointing me towards celery, helping me solve python problems that were over my head, and for the extensive beta testing  
1. @kerpanic for inspiring me to dust off an old project and turn it into celerystalk
1. My TUV OpenSky team and my IthacaSec hackers for testing this out and submitting bugs and features