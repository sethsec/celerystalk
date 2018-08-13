# celerystalk

celerystalk automates your network scanning/enumeration process with asynchronous jobs (aka *tasks*). This allows you to scan each service the same way so you don't have to keep track of what you ran where. celerystalk works well when used against one host, but it was designed for scanning multiple hosts.  

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


### Install/Setup

Directly into Kali: 

```
# git clone <repo>
# ./install.sh
```

Install with virtualenv: 

(Below Not working yet)

```
# apt install redis-server python-libnmap seclists -y
# pip install --user pipenv
# git clone --recursive <repo>
# cd celerystalk && pipenv install
# pipenv shell
# python setup.py install

```

The basic workflow: 


1. **Run Nmap or Nessus:** 
     
     Run nmap against your target(s) with version detection on and output to XML (nmap target -Pn -p- -sV -oX target.xml)
     
     or
     
     Run nessus against your target(s) and export a .nessus file 

1. **Configure celerystalk:** For each service type (i.e., http, https, ssh), configure what commands you want to run (config.json)
1. **Launch Scan:** Run celerystalk against the nmap or nessus XML and it will submit tasks to celery workers which asynchronously execute them and log output to your output directory   
1. **Query Status:** Asynchronously check the status of the tasks queue, as frequently as you like
1. **Cancel/Pause/Resume Tasks:** Cancel/Pause/Resume any task(s) that are currently running or in the queue.
1. **Run Report:** Run a report which combines all of the tool output into an html file and a txt file (Run this as often as you like) 


### Usage
```
Usage:
    celerystalk scan -f <nmap_file> -o <output_dir> [-w <workspace>] [-t <targets>] [-d]
    celerystalk query [-w <workspace>] [repeat]
    celerystalk report <report_dir> [-w <workspace>]
    celerystalk cancel ([all]|[<task_ids>]|[ip]) [-w <workspace>]
    celerystalk pause  ([all]|[<task_ids>]|[ip]) [-w <workspace>]
    celerystalk resume ([all]|[<task_ids>]|[ip]) [-w <workspace>]
    celerystalk shutdown
    celerystalk (help | -h | --help)

Options:
    -h --help         Show this screen
    -v --version      Show version
    -f <nmap_file>    Nmap xml import file
    -o <output_dir>   Output directory
    -t <targets>      Target(s): IP, IP Range, CIDR
    -w <workspace>    Workspace [default: Default]
    -d --dry_run      Dry run


Prerequisites:
Scan target(s) with: Nessus and export nessus db (scan.nessus ) or 
                     nmap target(s) -Pn -p- -sV -oX /pentest/nmap.xml    

Examples:           
    Start from Nmap XML file:   celerystalk scan -f /pentest/nmap.xml -o /pentest
    Start from Nessus file:     celerystalk scan -f /pentest/scan.nessus -o /pentest    
    Use non-default workspace:  celerystalk scan -f <file> -o /pentest -w test    
    Scan subset of Nmap XML:    celerystalk scan -f <file> -o /pentest -w test -t 10.0.0.1,10.0.0.3
                                celerystalk scan -f <file> -o /pentest -w test -t 10.0.0.100-200
                                celerystalk scan -f <file> -o /pentest -w test -t 10.0.0.0/24
    Dry Run:                    celerystalk scan -f <file> -o /pentest -d
    Query Tasks:                celerystalk query [-w workspace]
    Create Report:              celerystalk report /pentest           #Create a report for all scanneed hosts in /pentest
                                celerystalk report /pentest/10.0.0.1  #Create a report for a single host
    Cancel/Pause/Resume Tasks:  celerystalk <verb> 5,6,10-20          #Cancel/Pause/Resume tasks 5, 6, and 10-20
                                celerystalk <verb> all                #Cancel/Pause/Resume all tasks from all workspaces
                                celerystalk <verb> all -w test        #Cancel/Pause/Resume all tasks in the test workspace
                                celerystalk <verb> 10.0.0.1           #Cancel/Pause/Resume all tasks related to 10.0.0.1
                                celerystalk <verb> 10.0.0.0/24        #Cancel/Pause/Resume all tasks related to 10.0.0.0/24
    Shutdown Celery processes:  celerystalk shutdown

```

