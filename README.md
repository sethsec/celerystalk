# celerystalk

celerystalk automates your network scanning/enumeration process with asynchronous jobs (aka *tasks*). Scan each service the same way so you don't have to keep track of what you ran where. celerystalk works well when used against one host, but it was designed for scanning multiple hosts. celerystalk uses [Celery](http://www.celeryproject.org/) as the task queue and celery uses Redis as the broker.      

### Install/Setup

Kali: 

```
# git clone https://github.com/sethsec/celerystalk.git
# cd celerystalk
# ./install.sh
```


The basic workflow: 


1. **Run Nmap or Nessus:** 
     
    ```
    Nnmap: Run nmap against your target(s) with version detection on and output to XML (nmap target -Pn -p- -sV -oX target.xml)
    Nessus: Run nessus against your target(s) and export a .nessus file
   ``` 

1. **Configure celerystalk:** For each service type (i.e., http, https, ssh), configure which commands you want to run in the (config.ini). Add your own commands using [TARGET],[PORT], and[OUTPUT] placeholders. Disable any command by commenting it out with a ; or a #.  
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
1. **Launch Scan:** Run celerystalk against the nmap or nessus XML and it will submit tasks to celery workers which asynchronously execute them and log output to your output directory
    ```    
    Start from Nmap XML file:   celerystalk scan -f /pentest/nmap.xml -o /pentest
    Start from Nessus file:     celerystalk scan -f /pentest/scan.nessus -o /pentest
    Specify workspace:          celerystalk scan -f <file> -o /pentest -w test
    Find in scope vhosts:       celerystalk scan -f <file> -o /pentest -d domain1.com,domain2.com
    Scan subset hosts in XML:   celerystalk scan -f <file> -o /pentest -w test -t 10.0.0.1,10.0.0.3
                                celerystalk scan -f <file> -o /pentest -w test -t 10.0.0.100-200
                                celerystalk scan -f <file> -o /pentest -w test -t 10.0.0.0/24
    Simulation mode:            celerystalk scan -f <file> -o /pentest -d
    ```   
1. **Query Status:** Asynchronously check the status of the tasks queue, as frequently as you like
    ```
    Query Tasks:                celerystalk query [-w workspace]
                                celerystalk query [-w workspace] watch                               
                                celerystalk query [-w workspace] brief
                                celerystalk query [-w workspace] summary                                
                                celerystalk query [-w workspace] summary watch
    ```

1. **Cancel/Pause/Resume Tasks:** Cancel/Pause/Resume any task(s) that are currently running or in the queue.
    ```
    Cancel/Pause/Resume Tasks:  celerystalk <verb> 5,6,10-20          #Cancel/Pause/Resume tasks 5, 6, and 10-20
                                celerystalk <verb> all                #Cancel/Pause/Resume all tasks from default workspaces
                                celerystalk <verb> all -w test        #Cancel/Pause/Resume all tasks in the test workspace
    ```
1. **Run Report:** Run a report which combines all of the tool output into an html file and a txt file (Run this as often as you like) 
    ```
    Create Report:              celerystalk report /pentest           #Create a report for all scanneed hosts in /pentest
                                celerystalk report /pentest/10.0.0.1  #Create a report for a single host
    ```


### Usage
```
Usage:
    celerystalk scan -f <nmap_file> -o <output_dir> [-w <workspace>] [-t <targets>] [-d <domains>] [-s]
    celerystalk query [-w <workspace>] ([full] | [summary] | [brief]) [watch]
    celerystalk query [-w <workspace>] [watch] ([full] | [summary] | [brief])
    celerystalk report <report_dir> [-w <workspace>]
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
    Create Report:              celerystalk report /pentest           #Create a report for all scanneed hosts in /pentest
                                celerystalk report /pentest/10.0.0.1  #Create a report for a single host
    Cancel/Pause/Resume Tasks:  celerystalk <verb> 5,6,10-20          #Cancel/Pause/Resume tasks 5, 6, and 10-20
                                celerystalk <verb> all                #Cancel/Pause/Resume all tasks from all workspaces
                                celerystalk <verb> all -w test        #Cancel/Pause/Resume all tasks in the test workspace
                                celerystalk <verb> 10.0.0.1           #Cancel/Pause/Resume all tasks related to 10.0.0.1
                                celerystalk <verb> 10.0.0.0/24        #Cancel/Pause/Resume all tasks related to 10.0.0.0/24
    Shutdown Celery processes:  celerystalk shutdown
```

### Credit
This project was inspired by many great tools:  
1. https://github.com/codingo/Reconnoitre by @codingo_
1. https://github.com/frizb/Vanquish by @frizb
1. https://github.com/leebaird/discover by @discoverscripts
1. https://github.com/1N3/Sn1per
1. https://github.com/SrFlipFlop/Network-Security-Analysis by @SrFlipFlop

Thanks to @offensivesecurity and @hackthebox_eu for their lab networks :)

Also, thanks to:
1. @decidedlygray for pointing me towards celery, helping me solve python problems that were over my head, and for the extensive beta testing  
1. @kerpanic for inspiring me to dust off an old project and turn it into celerystalk
1. My TUV OpenSky team and my IthacaSec hackers for testing this out and submitting bugs and features