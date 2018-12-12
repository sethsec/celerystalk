# celerystalk

celerystalk helps you automate your network scanning/enumeration process with asynchronous jobs (aka *tasks*) while retaining full control of which tools you want to run.    

* **Configurable** - Some common tools are in the default config, but you can add any tool you want
* **Service Aware** - Uses nmap/nessus service names rather than port numbers to decide which tools to run 
* **Scalable** - Designed for scanning multiple hosts, but works well for scanning one host at a time
* **VirtualHosts** - Supports subdomain recon and virtualhost scanning
* **Job Control** - Supports canceling, pausing, and resuming of tasks, inspired by Burp scanner
* **Screenshots** Automatically takes *screenshots of every URL identified* via brute force (gobuster) and spidering (Photon)

## Install/Setup

* **Supported Operating Systems:** Kali 
* **Supported Python Version:** 2.x

**You must install and run celerystalk as root**   

```
# git clone https://github.com/sethsec/celerystalk.git
# cd celerystalk/setup
# ./install.sh
# cd ..
# ./celerystalk -h
```
**You must install and run celerystalk as root**   


## Using celerystalk - The basics

**[CTF/HackTheBox mode]** 

How to scan a host or multiple hosts by IP

Option 1: Run nmap yourself and import results
```
# nmap 10.10.10.10 -Pn -p- -sV -oX tenten.xml                       # Run nmap
# ./celerystalk workspace create -w htb -o /htb -m vapt             # Create workspace. Set output dir and mode
# ./celerystalk import -f tenten.xml                                # Import nmap scan 
# ./celerystalk db services                                         # If you want to see what services were loaded
# ./celerystalk scan                                                # Run all enabled commands
# ./celerystalk query watch (then Ctrl+c)                           # Watch scans as move from pending > running > complete
# ./celerystalk report                                              # Generate report
```

Option 2: Have celerystalk run nmap and parse results
```
# ./celerystalk workspace create -w htb -o /htb -m vapt             # Create workspace. Set output dir and mode
# ./celerystalk import -S scope.txt                                 # Import IP/CIDR/Ranges and mark as in scope
# ./celerystalk nmap                                                # Nmap all in-scope hosts (reads options from config.ini)
# ./celerystalk query watch (then Ctrl+c)                           # Watch nmap scans as they move from pending > running > complete
# ./celerystalk db services                                         # If you want to see what services were loaded
# ./celerystalk scan                                                # Run all enabled commands
# ./celerystalk query watch (then Ctrl+c)                           # Watch scans as they move from pending > running > complete
# ./celerystalk report                                              # Generate report
```

**[Vulnerability Assessment Mode]**  
* In VAPT mode, IP addresses/ranges/CIDRs define scope.
* Subdomains that match an in-scope IP are also added to scope.

How to scan a list of in-scope hosts/networks and any subdomains that resolve to any of the in-scope IPs

Option 1: Run nmap yourself and import results (optionally define IPs or hostnames that are out of scope)
```
# nmap -iL client-inscope-list.txt -Pn -p- -sV -oX client.xml       # Run nmap
# ./celerystalk workspace create -o /assessments/client -m vapt     # Create default workspace and set output dir
# ./celerystalk import -f client.xml                                # Import services and mark all hosts as in scope
# ./celerystalk import -S scope.txt                 (optional)      # Import IP/CIDR/Ranges and mark as in scope
# ./celerystalk import -O out_scope.txt             (optional)      # Define HOSTS/IPs that are out of scope
# ./celerystalk import -d subdomains.txt            (optional)      # Define HOSTS/IPs that are out of scope
# ./celerystalk subdomains -d client.com,client.net (optional)      # Find subdomains and determine if in scope
# ./celerystalk scan                                                # Run all enabled commands
# ./celerystalk query watch (then Ctrl+c)                           # Wait for scans to finish
# ./celerystalk report                                              # Generate report
```
**Note:**  You can run the subdomains command first and then define scope, or you can define scope and import subdomains.  

Option 2: Have celerystalk run nmap and parse results (optionally define IPs or hostnames that are out of scope)
```
# ./celerystalk workspace create -o /assessments/client -m vapt     # Create default workspace and set output dir
# ./celerystalk import -S client-inscope-list.txt                   # Import IP/CIDR/Ranges and mark as in scope
# ./celerystalk import -O out_scope.txt             (optional)      # Define HOSTS/IPs that are out of scope
# ./celerystalk nmap                                                # Nmap all in-scope hosts (reads options from config.ini)
# ./celerystalk query watch (then Ctrl+c)                           # Watch nmap scans as they move from pending > running > complete
# ./celerystalk subdomains -d client.com,client.net                 # Find subdomains and determine if in scope
# ./celerystalk scan                                                # Run all enabled commands
# ./celerystalk query watch (then Ctrl+c)                           # Watch scans as they move from pending > running > complete
# ./celerystalk report                                              # Generate report
```
**Note:**  You can run the subdomains command first and then define scope, or you can define scope and import subdomains.  

**[Bug Bounty Mode]** - How to scan all subdomains identified within a domain or domains, while excluding hosts that are out of scope.  
*  In BB mode, all subdomains found with celerystalk or manually imported are marked in scope.

```
# ./celerystalk workspace create -o /assessments/company -m bb      # Create default workspace and set output dir
# ./celerystalk subdomains -d company.com,company.net               # Find subdomains and determine if in scope
# ./celerystalk import -S scope.txt     (optional)                  # Import IP/CIDR/Ranges and mark as in scope
# ./celerystalk import -O out_scope.txt (optional)                  # Define HOSTS/IPs that are out of scope
# ./celerystalk nmap                    (optional)                  # Nmap all in-scope hosts (reads options from config.ini)
# ./celerystalk import -f client.xml    (optional)                  # If you would rather import an nmap file you already ran

# ./celerystalk scan [--noIP]                                       # Run all enabled commands against all in scope hosts
# ./celerystalk query watch (then Ctrl+c)                           # Wait for scans to finish
# ./celerystalk report                                              # Generate report
```
**Note:**  You can run the subdomains command first and then define scope, or you can define scope and import subdomains.


**[URL Mode]** - How to scan a a URL  
* Use this as a follow up whenever you find an interesting directory, or just as quick way to scan one web app without importing anything.
```
# ./celerystalk workspace create -o /assessments/client -m {vapt|bb]# Create default workspace and set output dir
# ./celerystalk scan -u http://10.10.10.10/secret_folder/           # Run all enabled commands
# ./celerystalk query watch (then Ctrl+c)                           # Wait for scans to finish
# ./celerystalk report                                              # Generate report
```

## Using celerystalk - Some more detail


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

1. **Run Nmap or Nessus:** 
     
   * Nmap: Run nmap against your target(s). Required: enable version detection (-sV) and output to XML (-oX filename.xml). All other nmap options are up to you. Here are some examples:
     ```
      nmap target(s) -Pn -p- -sV -oX filename.xml 
      nmap -iL target_list.txt -Pn -sV -oX filename.xml
     ```
   * Nessus: Run nessus against your target(s) and export results as a .nessus file

1. **Create workspace:**

    | Option | Description |
    | --- | --- |
    | no options | Prints current workspace |
    | create | Creates new workspace |
    | -w | Define new workspace name |
    | -o | Define output directory assigned to workspace |   
    | -m | Mode [vapt|bb] |

    ```
      Create default workspace    ./celerystalk workspace create -o /assessments/client -m bb
      Create named workspace      ./celerystalk workspace create -o /assessments/client -w client -m vapt
      Switch to another workspace ./celerystalk workspace client
    ```
    
1. **Import Data:** Import data into celerystalk

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
    
1. **Find Subdomains (Optional):** celerystalk will perform subdomain recon using the tools specified in the config.ini.
  
   | Option | Description |
   | --- | --- |
   | -d domain1,domain2,etc| <b>Run Amass, Sublist3r, etc. and store domains in DB</b><ul><li>After running your subdomain recon tools celerystalk determines whether each subdomain is in scope by resolving the IP and looking for IP in the DB. If there is a match, the domain is marked as in scope and will be scanned.</li></ul>

    ```
    Find subdomains:       celerystalk subdomains -d domain1.com,domain2.com
    ```

1. **Launch Scan:** I recommend using the import command first and running scan with no options, however you do have the option to do it all at once (import and scan) by using the flags below. celerystalk will submit tasks to celery which asynchronously executes them and logs output to your output directory. 

   | Option | Description |
   | --- | --- |
   | no options | <b>Scan all in scope hosts</b><ul><li>Reads DB and scans every in scope IP and subdomain.</li><li>Launches all enabled tools for IPs, but only http/http specific tools against virtualhosts</li></ul>   |
   | -t ip,vhost,cidr | <b>Scan specific target(s) from DB or scan file</b><ul><li>Scan a subset of the in scope IPs and/or subdomains.</li></ul> |  
   |-s | <b>Simulation</b><br> Sends all of the tasks to celery, but all commands are executed with a # before them rendering them inert.</li></ul> |
   |<b>Use these only if you want to skip the import phase and import/scan all at once</b>||
   | -f scan.xml | <b>Import and process Nmap/Nessus xml before scan</b><ul><li>Adds all IP addresses from this file to hosts table and marks them all in scope to be scanned.<br>Adds all ports and service types to services table.</li></ul> |
   | -S scope.txt | <b>Import and process scope file before scan</b><ul><li>This adds targets as in scope but does not import any ports/services data.</li></ul> |
   | -D subdomains.txt | <b>Import and process (sub)domains file before scan </b><ul><li>celerystalk determines whether each subdomain is in scope by resolving the IP and looking for IP in the DB. If there is a match, the domain is marked as in scope and will be scanned.</li></ul>| 
   | -d domain1,domain2,etc| <b>Find Subdomains and scan in scope hosts</b><ul><li>After running your subdomain recon tools celerystalk determines whether each subdomain is in scope by resolving the IP and looking for IP in the DB. If there is a match, the domain is marked as in scope and will be scanned.</li></ul>|

 
    Scan imported hosts/subdomains
    ```    
    Scan all in scope hosts:    ./celerystalk scan    
    Scan subset of DB hosts:    ./celerystalk scan -t 10.0.0.1,10.0.0.3
                                ./celerystalk scan -t 10.0.0.100-200
                                ./celerystalk scan -t 10.0.0.0/24
                                ./celerystalk scan -t sub.domain.com
    Simulation mode:            ./celerystalk scan -s
    ```
    
    Import and Scan
    ```
    Start from Nmap XML file:   ./celerystalk scan -f /pentest/nmap.xml -o /pentest
    Start from Nessus file:     ./celerystalk scan -f /pentest/scan.nessus -o /pentest
    Scan all in scope vhosts:   ./celerystalk scan -f <file> -o /pentest -d domain1.com,domain2.com
    Scan subset hosts in XML:   ./celerystalk scan -f <file> -o /pentest -t 10.0.0.1,10.0.0.3
                                ./celerystalk scan -f <file> -o /pentest -t 10.0.0.100-200
                                ./celerystalk scan -f <file> -o /pentest -t 10.0.0.0/24
    Simulation mode:            ./celerystalk scan -f <file> -o /pentest -s
    ```   

1. **Rescan:** Use this command to rescan an already scanned host.

   | Option | Description |
   | --- | --- |
   | no option| For each in scope host in the DB, celerystalk will ask if if you want to rescan it| 
   | -t ip,vhost,cidr | Scan a subset of the in scope IPs and/or subdomains. |
   
   ```
   Rescan all hosts:           ./celerystalk rescan
   Rescan some hosts           ./celerystalk rescan-t 1.2.3.4,sub.domain.com  
   Simulation mode:            ./celerystalk rescan -s   
   ```  

1. **Query Status:** Asynchronously check the status of the tasks queue as frequently as you like. The watch mode actually executes the linux watch command so you don't fill up your entire terminal buffer.
     
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

1. **Cancel/Pause/Resume Tasks:** Cancel/Pause/Resume any task(s) that are currently running or in the queue.

    | Option | Description |
    | --- | --- |
    | cancel | <ul><li>Canceling a running task will send a **kill -TERM**</li><li>Canceling a queued task* will make celery ignore it (uses celery's revoke).</li><li>Canceling all tasks* will kill running tasks and revoke all queued tasks.</li></ul>
    | pause | <ul><li>Pausing a single task uses **kill -STOP** to suspend the process.</li><li>Pausing all tasks* attemtps to *kill -STOP* all running tasks, but it is a little wonky and you mind need to run it a few times. It is possible a job completed before it was able to be paused, which means you will have a worker that is still accepting new jobs.</li></ul>
    | resume | <ul><li>Resuming tasks* sends a **kill -CONT** which allows the process to start up again where it left off.</li></ul>|

    ```
    Cancel/Pause/Resume Tasks:  ./celerystalk <verb> 5,6,10-20          #Cancel/Pause/Resume tasks 5, 6, and 10-20 from current workspace
                                ./celerystalk <verb> all                #Cancel/Pause/Resume all tasks from current workspaces
    ```
1. **Run Report:** Run a report which combines all of the tool output into an html file and a txt file. Run this as often as you like. Each time you run the report it overwrites the previous report.  
    ```
    Create Report:              ./celerystalk report                    #Create a report for all scanned hosts in current workspace

    ```
   
1. **Access the DB:** List or export the workspaces, hosts, services, or paths stored in the celerystalk database

    | Option | Description |
    | --- | --- |
    | workspaces | Show all known workspaces and the output directory associated with each workspace |
    | services | Show all known open ports and service types by IP |
    | hosts | Show all hosts (IP addresses and subdomains/vhosts) and whether they are in scope and whether they have been submitted for scanning |
    | paths | Show all paths that have been identified by vhost |
    | export | Export the services, hosts, and paths tables
   
    ```
    Show workspaces:            ./celerystalk db workspaces
    Show services:              ./celerystalk db services    
    Show hosts:                 ./celerystalk db hosts
    Show paths:                 ./celerystalk db paths
    Export current DB:          ./celerystalk db export
    ```

1. **Administrative Functions:** 
 
    |    Options    | Description                                   |
    | --- | --- |
    |     start     | Start Celery & Redis processes                |
    |      stop     | Stop Celery & Redis processes                 |
    |     reset     | Destroy DB, Flush Redis, start over           |
    |     backup    | Backup DB and all workspace data directories  |
    |    restore    | Restore DB and all workspace data directories |
    | -f [filename] | Restore file name                             |
   
    ```
    Examples:
    ./celerystalk admin start
    ./celerystalk admin stop
    ./celerystalk admin reset
    ./celerystalk admin backup -f
    ./celerystalk admin restore -f <filename>
    
    ```



## Usage
```
Usage:
    celerystalk workspace ([create]|[switch]) [-w workspace_name] [-o <output_dir>] [-m <mode>] [-h]
    celerystalk import [-f <nmap_file>] [-S scope_file] [-D subdomains_file] [-O outOfScope.txt] [-u <url>] [-h]
    celerystalk subdomains [-d <domains>] [-s] [-h]
    celerystalk nmap [-t <targets>] [-s] [-h]
    celerystalk scan [-f <nmap_file>] [-t <targets>] [-d <domains>] [-S scope_file] [-D subdomains_file] [--noIP] [-s] [-h]
    celerystalk scan -u <url> [-s] [-h]
    celerystalk rescan [-t <targets>] [-s] [-h]
    celerystalk query ([full] | [summary] | [brief]) [watch] [-h]
    celerystalk query [watch] ([full] | [summary] | [brief]) [-h]
    celerystalk report [-h]
    celerystalk cancel ([all]|[<task_ids>]) [-h]
    celerystalk pause  ([all]|[<task_ids>]) [-h]
    celerystalk resume ([all]|[<task_ids>]) [-h]
    celerystalk db ([workspaces] | [services] | [hosts] | [vhosts] | [paths]) [-h]
    celerystalk db export [-h]
    celerystalk admin ([start]|[stop]|[reset]|[backup]|[restore]) [-f <restore_file>] [-h]
    celerystalk interactive [-h]
    celerystalk (help | -h | --help)

Options:
    -h --help           Show this screen
    -v --version        Show version
    -f <nmap_file>      Nmap xml import file
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

    celerystalk workspace -h
    celerystalk subdomains -h
    celerystalk import -h
    celerystalk nmap -h
    celerystalk scan -h
    celerystalk rescan -h
    celerystalk query -h
    celerystalk report -h
    celerystalk pause -h
    celerystalk resume -h
    celerystalk cancel -h
    celerystalk db -h
    celerystalk admin -h

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