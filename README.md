# celerystalk

celerystalk helps you automate your network scanning/enumeration process with asynchronous jobs (aka *tasks*) while retaining full control of which tools you want to run.    


![](https://i.imgur.com/tZ4RkOr.png)

Interactive Demo: [Bug Bounty Mode (HackerOne)](https://sethsec.github.io/celerystalk/bug_bounty_mode/celerystalkReports/)

Interactive Demo: [Vulnerability Assessment / PenTest Mode (Retired HackTheBox.eu machines)](https://sethsec.github.io/celerystalk/vapt_mode/celerystalkReports/)



## What celerystalk can automate for you

Phase | Command | Examples of tools used
--- | --- | ----
DNS Recon/Enumeration | ./celerystalk subdomains -d domain1,domain2 | Amass, sublist3r
Define Scope, Import nmap/nessus | ./celerystalk import [scan_data,scope_files,etc.] | celerystalk     
Port Scanning | ./celerystalk nmap | nmap
Directory and File Enumeration, Vulnerability Identification | ./celerystalk scan | Gobuster, Nikto, Photon, sqlmap, wpscan, hydra, medusa, wappalyzer, whatweb, etc.
Screenshots | ./celerystalk sceenshots | Aquatone
Analysis | ./celerystalk report | celerystalk

---
celerystalk is: 

* **Configurable** - Some common tools are in the default config, but you can add any tool you want
* **Service Aware** - Uses Nmap/Nessus service names rather than port numbers to decide which tools to run 
* **Scalable** - Designed for scanning multiple hosts, but works well for scanning one host at a time
* **VirtualHosts** - Supports subdomain recon and virtualhost scanning
* **Job Control** - Supports canceling, pausing, and resuming of tasks, inspired by Burp scanner
* **Screenshots** - Screenshots (aquatone) every in-scope URL that was identified by any tool (you can limit # of screenshots if you'd like)
---


## Install/Setup

* **Supported Operating Systems:** Kali 
* **Supported Python Version:** 2.x

**You must install and run celerystalk as root**   

```
git clone https://github.com/sethsec/celerystalk.git
cd celerystalk/setup
./install.sh
cd ..
./celerystalk -h
```

## Use docker container from Dockerhub

```
docker pull sethsec/celerystalk:latest
docker run -p 27007:27007 -ti celerystalk
```


## Docker Build
```
docker build -t celerystalk https://github.com/sethsec/celerystalk.git
docker run -p 27007:27007 -ti celerystalk 
```



## Using celerystalk - The basics


### [URL Mode] - How to scan a a URL (or multiple URLs in a file) 

#### Launch all enabled tools against a URL or many URLs in a file without having to import scope, nmap, etc. 
```
# ./celerystalk scan -u url or filename                 # Run all enabled commands against specified url(s)
# ./celerystalk query watch (then Ctrl+c)               # Wait for scans to finish
# ./celerystalk screenshots                             # Take screenshots
# ./celerystalk report                                  # Generate report
```

### [CTF/HackTheBox/Easy mode] - How to scan one or more hosts

#### Import nmap xml
```
# nmap 10.10.10.10 -Pn -p- -sV -oX tenten.xml           # Run nmap
# ./celerystalk import -f tenten.xml                    # Import nmap scan 
```
#### Or, import list of hosts that are in scope and have celerystalk run nmap for you
```
# ./celerystalk import -S scope.txt                     # Import IP/CIDR/Ranges and mark as in scope
# ./celerystalk nmap                                    # Nmap all in-scope hosts (reads options from config.ini)
```

#### Check imported services, launch scans, take screenshots, generate report  
```
# ./celerystalk db services                             # If you want to see what services were loaded
# ./celerystalk scan                                    # Run all enabled commands
# ./celerystalk query watch (then Ctrl+c)               # Watch scans as move from pending > running > complete
# ./celerystalk screenshots                             # Take screenshots
# ./celerystalk report                                  # Generate report
```

## Advanced Usage: Bug Bounty Mode vs Vulnerability Assessment Mode

You define the mode at workspace instantiation. The default workspace is VAPT mode, but you have two options for manually 
created workspaces.

* If you are starting with in scope IP addresses/ranges/CIDRs, use Vulnerability Assessment and PenTest (VAPT) mode.
* If you are starting with in scope domains, use Bug Bounty (BB) mode. 

### [Bug Bounty Mode] 

*  In BB mode, all subdomains found with celerystalk or manually imported are marked in scope.

#### Find subdomains, define out of scope hosts, scan everything else  

```
# ./celerystalk workspace create -o /dir -m bb          # Create default workspace and set output dir
# ./celerystalk subdomains -d company.com,dom.net       # Find subdomains and determine if in scope
# ./celerystalk import -S scope.txt     (optional)      # Import IP/CIDR/Ranges and mark as in scope
# ./celerystalk import -O out_scope.txt (optional)      # Define HOSTS/IPs that are out of scope
# ./celerystalk nmap                    (optional)      # Nmap all in-scope hosts (reads options from config.ini)
# ./celerystalk import -f client.xml    (optional)      # If you would rather import an nmap file you already ran
# ./celerystalk scan [--noIP]                           # Run all enabled commands against all in scope hosts
# ./celerystalk query watch (then Ctrl+c)               # Wait for scans to finish
# ./celerystalk screenshots                             # Take screenshots
# ./celerystalk report                                  # Generate report
```
**Note:**  You can run the subdomains command first and then define scope, or you can define scope and import subdomains.



### [Vulnerability Assessment Mode]  

* In VAPT mode, IP addresses/ranges/CIDRs define scope.
* Subdomains that match an in-scope IP are also added to scope.

#### Import nmap scan, optionally define IPs or hostnames that are out of scope
```
# nmap -iL inscope-list.txt -Pn -p- -sV -oX client.xml     # Run nmap
# ./celerystalk workspace create -o /dir -m vapt           # Create default workspace and set output dir
# ./celerystalk import -f client.xml                       # Import services and mark all hosts as in scope
# ./celerystalk import -S scope.txt             (optional) # Import IP/CIDR/Ranges and mark as in scope
# ./celerystalk import -O out_scope.txt         (optional) # Define HOSTS/IPs that are out of scope
# ./celerystalk import -d subdomains.txt        (optional) # Define subdomains that are in scope
# ./celerystalk subdomains -d dom1.com,dom2.net (optional) # Find subdomains and determine if in scope
# ./celerystalk scan                                       # Run all enabled commands
# ./celerystalk query watch (then Ctrl+c)                  # Wait for scans to finish
# ./celerystalk screenshots                                # Take screenshots
# ./celerystalk report                                     # Generate report
```
**Note:** You can run the subdomains command first and then define scope, or you can define scope and import subdomains.  

#### Import list of hosts that are in scope and have celerystalk run nmap and parse results 
```
# ./celerystalk workspace create -o /dir -m vapt        # Create default workspace and set output dir
# ./celerystalk import -S client-inscope-list.txt       # Import IP/CIDR/Ranges and mark as in scope
# ./celerystalk import -O out_scope.txt      (optional) # Define HOSTS/IPs that are out of scope
# ./celerystalk nmap                                    # Nmap all in-scope hosts (reads options from config.ini)
# ./celerystalk query watch (then Ctrl+c)               # Watch nmap scans as they move from pending > running > complete
# ./celerystalk subdomains -d client.com,client.net     # Find subdomains and determine if in scope
# ./celerystalk scan                                    # Run all enabled commands
# ./celerystalk query watch (then Ctrl+c)               # Watch scans as they move from pending > running > complete
# ./celerystalk screenshots                             # Take screenshots
# ./celerystalk report                                  # Generate report
```
**Note:** You can run the subdomains command first and then define scope, or you can define scope and import subdomains.  

## Using celerystalk - Some more detail

### Config.ini - Your configuration home. 

1. Configure celerystalk options like number of concurrent tasks
1. Create custom configuration replacement variables
1. Configure Nmap/Nessus to celerystalk service mapping
1. Configure which tools you'd like celerystalk to execute

For more detail, check out the [Configuration](https://github.com/sethsec/celerystalk/wiki/Configuration) page in the Wiki

### Subcommands

#### workspace
You need to create a workspace before you can do anything else. 

| Option | Description |
| --- | --- |
| no options | Prints current workspace |
| create | Creates new workspace |
| -w | Define new workspace name |
| -o | Define output directory assigned to workspace |   
| -m | Mode [vapt \ bb] |

```
  Create default workspace    ./celerystalk workspace create -o /assessments/client -m bb
  Create named workspace      ./celerystalk workspace create -o /assessments/client -w client -m vapt
  Switch to another workspace ./celerystalk workspace client
```
    
#### import
This command allows you to import port and host data into celerystalk, and allows you to define what is in scope and what is out of scope. 

| Option | Description |
| --- | --- |
| -f scan.xml | <b>Nmap/Nessus xml</b><br><ul><li>Adds all IP addresses from this file to hosts table and marks them all in scope to be scanned.</li><li>Adds all ports and service types to services table.</li></ul> |
| -S scope.txt | <b>Scope file</b><br><ul><li>Show file differences that haven't been staged </li></ul>|
| -D subdomains.txt | <b>(sub)Domains file</b><br><ul><li>celerystalk determines whether each subdomain is in scope by resolving the IP and looking for IP in the DB. If there is a match, the domain is marked as in scope and will be scanned.</li></ul>|
  

```
Import Nmap XML file:       ./celerystalk import -f /assessments/nmap.xml 
Import Nessus file:         ./celerystalk import -f /assessments/scan.nessus 
Import list of Domains:     ./celerystalk import -D <file>
Import list of IPs/Ranges:  ./celerystalk import -S <file>
Specify workspace:          ./celerystalk import -f <file>     
Import multiple files:      ./celerystalk import -f nmap.xml -S scope.txt -D domains.txt
```
    
#### subdomains
This command executes uses all of the subdomain search tools in your config file. If you prefer, you can do this outside of celerystalk and import the subdomains with the import command

| Option | Description |
| --- | --- |
| -d domain1,domain2,etc| <b>Run Amass, Sublist3r, etc. and store domains in DB</b><ul><li>After running your subdomain recon tools celerystalk determines whether each subdomain is in scope by resolving the IP and looking for IP in the DB. If there is a match, the domain is marked as in scope and will be scanned.</li></ul>|

```
Find subdomains:       celerystalk subdomains -d domain1.com,domain2.com
```

#### nmap
This command will run nmap for you, using the options you specified in the config.ini file. You can alternatively import port scan data from an nmap xml file or from a .nessus file 
     
| Option | Description |
| --- | --- |
| no options | Read nmap command from config and scan all services for in-scope hosts 
| -c [filename] | Specify a celerystalk configuration file [Default: ./config.ini]

#### scan
This command will submit tasks to celery, which asynchronously executes them and logs output to your output directory. 

| Option | Description |
| --- | --- |
| no options | <b>Scan all in scope hosts</b><ul><li>Reads DB and scans every in scope IP and subdomain.</li><li>Launches all enabled tools for IPs, but only http/http specific tools against virtualhosts</li></ul>   |
| --noIP      | Don't scan hosts by IP (only scan vhosts)
| -t ip,vhost,cidr | <b>Scan specific target(s) from DB or scan file</b><ul><li>Scan a subset of the in scope IPs and/or subdomains</li></ul> |  
| -s | <b>Simulation</b><br> Sends all of the tasks to celery, but all commands are executed with a # before them rendering them inert</li></ul> |
| -c [filename]   | Specify a celerystalk configuration file [Default: ./config.ini]          |
| -u [URL]     | Scan a specific URL, even if it is not in the DB yet                      |


```    
Scan all in scope hosts:    ./celerystalk scan    
Scan subset of DB hosts:    ./celerystalk scan -t 10.0.0.1,10.0.0.3
                            ./celerystalk scan -t 10.0.0.100-200
                            ./celerystalk scan -t 10.0.0.0/24
                            ./celerystalk scan -t sub.domain.com
Simulation mode:            ./celerystalk scan -s
```
 
#### rescan
This command will rescan an already scanned host.

| Option | Description |
| --- | --- |
| no option| For each in scope host in the DB, celerystalk will ask if if you want to rescan it| 
| -t ip,vhost,cidr | Scan a subset of the in scope IPs and/or subdomains. |
|        -s        | Sends all of the tasks to celery, but all commands are executed with a # before them rendering them inert.  
|  -c [filename]   | Specify a celerystalk configuration file [Default: ./config.ini] |


```
Rescan all hosts:           ./celerystalk rescan
                           ./celerystalk rescan -c myconfig.ini
Rescan some hosts           ./celerystalk rescan -t 1.2.3.4,sub.domain.com  
Simulation mode:            ./celerystalk rescan -s   
```  

#### query 
Asynchronously check the status of the tasks queue as frequently as you like. The watch mode actually executes the linux watch command so you don't fill up your entire terminal buffer.
     
| Option | Description |
| --- | --- |
| no options | Shows all tasks in the current workspace |
| watch | Sends command to the unix watch command which will let you get an updated status every 2 seconds|
| brief | Limit of 5 results per status (pending/running/completed/cancelled/paused) |
| summary | Shows only a banner with numbers and not the tasks themselves |  

```
Query Tasks:                ./celerystalk query 
                            ./celerystalk query watch                               
                            ./celerystalk query brief
                            ./celerystalk query summary                                
                            ./celerystalk query summary watch
```

#### cancel/pause/resume 
Cancel/Pause/Resume any task(s) that are currently running or in the queue.

| Option | Description |
| --- | --- |
| cancel | <ul><li>Canceling a running task will send a **kill -TERM**</li><li>Canceling a queued task* will make celery ignore it (uses celery's revoke).</li><li>Canceling all tasks* will kill running tasks and revoke all queued tasks.</li></ul>
| pause | <ul><li>Pausing a single task uses **kill -STOP** to suspend the process.</li><li>Pausing all tasks* attempts to *kill -STOP* all running tasks, but it is a little wonky and you mind need to run it a few times. It is possible a job completed before it was able to be paused, which means you will have a worker that is still accepting new jobs.</li></ul>
| resume | <ul><li>Resuming tasks* sends a **kill -CONT** which allows the process to start up again where it left off.</li></ul>|

```
Cancel/Pause/Resume Tasks:  ./celerystalk <verb> 5,6,10-20          #Cancel/Pause/Resume tasks 5, 6, and 10-20 from current workspace
                            ./celerystalk <verb> all                #Cancel/Pause/Resume all tasks from current workspaces
```

#### screenshots

|  Options   | Description                           |
| --- | --- |
| no options | Take screenshots for all known paths |

```
    ./celerystalk screenshots
```

#### report
Run a report which combines all of the tool output into an html file and a txt file. Run this as often as you like. Each time you run the report it overwrites the previous report.  

|  Options   | Description                           |
| --- | --- |
| no options | Create report for all in-scope hosts that have been scanned |

```
Create Report:              ./celerystalk report                    #Create a report for all scanned hosts in current workspace

```
   
#### db
List or export the workspaces, hosts, services, or paths stored in the celerystalk database

| Option | Description |
| --- | --- |
| workspaces | Show all known workspaces and the output directory associated with each workspace |
| workspace | Same as workspaces |
| services | Show all known open ports and service types by IP |
| ports    | Same as ports.                                                         |
| hosts | Show all hosts (IP addresses and subdomains/vhosts) and whether they are in scope and whether they have been submitted for scanning |
| vhosts   | Same as hosts command, but excludes vhosts that are IP addresses.      |
| paths | Show all paths that have been identified by vhost |
| paths_only | Show a newline separated list of paths in the db. Useful for piping into another tool |
| export | Export the services, hosts, and paths tables
| export_paths_only | Export just a newline separated list of paths in the db to a file. 

```
Show workspaces:            ./celerystalk db workspaces
                            ./celerystalk db workspace
Show services:              ./celerystalk db services
                            ./celerystalk db ports
Show hosts:                 ./celerystalk db hosts
Show vhosts only            ./celerystalk db vhosts
Show paths:                 ./celerystalk db paths
Show paths (no table)       ./celerystalk db paths_only     
Show tasks:                 ./celerystalk db tasks
Export tables to csv        ./celerystalk db export
Export paths to txt         ./celerystalk db export_paths_only
```

#### admin
Administrative Functions 
 
|    Options    | Description                                   |
| --- | --- |
|     start     | Start Celery & Redis processes                |
|      stop     | Stop Celery & Redis processes                 |
|    restart    | Restart Celery & Redis processes              |
|     reset     | Destroy DB, Flush Redis, start over           |
|     backup    | Backup DB and all workspace data directories  |
|    restore    | Restore DB and all workspace data directories |
| -f [filename] | Restore file name                             |


```
Examples:
./celerystalk admin start
./celerystalk admin stop
./celerystalk admin restart
./celerystalk admin reset
./celerystalk admin backup -f
./celerystalk admin restore -f <filename>

```



## Usage
```
Usage:
    celerystalk workspace ([create]|[switch]) [-w workspace_name] [-o <output_dir>] [-m <mode>] [-h]
    celerystalk import [-f <nmap_file>] [-S scope_file] [-D subdomains_file] [-O outOfScope.txt] [-u <url>] [-h]
    celerystalk subdomains [-d <domains>] [-c <config_file>] [-s] [-h]
    celerystalk nmap [-t <targets>] [-c <config_file>] [-s] [-h]
    celerystalk scan [-t <targets>] [--noIP] [-c <config_file>] [-s] [-h]
    celerystalk scan -u <url> [-c <config_file>] [-s] [-h]
    celerystalk rescan [-t <targets>] [-c <config_file>] [-s] [-h]
    celerystalk query ([full] | [summary] | [brief]) [watch] [-h]
    celerystalk query [watch] ([full] | [summary] | [brief]) [-h]
    celerystalk report [-h]
    celerystalk screenshots [-h]
    celerystalk cancel ([all]|[<task_ids>]) [-h]
    celerystalk pause  ([all]|[<task_ids>]) [-h]
    celerystalk resume ([all]|[<task_ids>]) [-h]
    celerystalk db ([workspaces]|[workspace]|[services]|[ports]|[hosts]|[vhosts]|[paths]|[paths_only]|[tasks]) [-h]
    celerystalk db export [-h]
    celerystalk admin ([start]|[stop]|[restart]|[reset]|[backup]|[restore]) [-f <restore_file>] [-h]
    celerystalk interactive [-h]
    celerystalk (help | -h | --help)

Options:
    -h --help           Show this screen
    -v --version        Show version
    -f <nmap_file>      Nmap xml import file
    -c <config_file>    Specify a non-default configuration file  by name
    -o <output_dir>     Output directory
    -m <mode>           vapt = VulnAssmt/PenTest, bb = Bug Bounty
    -S <scope_file>     Scope import file
    -O <outscope_file>  Out of scope hosts file
    -D <subdomains_file> Subdomains import file
    -t <targets>        Target(s): IP, IP Range, CIDR
    -u <url>            URL to parse and scan with all configured tools
    -w <workspace>      Workspace
    -d --domains        Domains to scan for vhosts
    -s --simulation     Simulation mode.  Submit tasks comment out all commands
    --noIP              Only scan targets by DNS hostname (Don't scan the IP address)

Context specific help with examples:

    ./celerystalk workspace -h
    ./celerystalk subdomains -h
    ./celerystalk import -h
    ./celerystalk nmap -h
    ./celerystalk scan -h
    ./celerystalk rescan -h
    ./celerystalk query -h
    ./celerystalk pause -h
    ./celerystalk resume -h
    ./celerystalk cancel -h
    ./celerystalk db -h
    ./celerystalk screenshots -h
    ./celerystalk report -h
    ./celerystalk admin -h
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
1. My friends at TUV OpenSky and IthacaSec for testing this out and submitting bugs and features
