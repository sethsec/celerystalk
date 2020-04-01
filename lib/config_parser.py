from collections import OrderedDict
from ConfigParser import ConfigParser


class MultiOrderedDict(OrderedDict):
    '''Taken from: https://stackoverflow.com/questions/15848674/how-to-configparse-a-file-keeping-multiple-values-for-identical-keys'''
    def __setitem__(self, key, value):
        if isinstance(value, list) and key in self:
            self[key].extend(value)
        else:
            super(MultiOrderedDict, self).__setitem__(key, value)
            # super().__setitem__(key, value) in Python 3


def read_config_ini(config_file=None):
    config = ConfigParser()
    config.read([config_file])
    supported_services = []
    for (key,val) in config.items("nmap-service-names"):
        services = val.split(",")
        for service in services:
            service = service.strip()
            supported_services.append(service)
    return config,supported_services

def get_concurrent_tasks(config_file):
    config,supported_services = read_config_ini(config_file)
    for (key, val) in config.items("celerystalk-config"):
        if key == "concurrent_tasks":
            return val

def get_simpleserver_port(config_file):
    config,supported_services = read_config_ini(config_file)
    for (key, val) in config.items("celerystalk-config"):
        if key == "simple_server_port":
            return val

def get_screenshot_max(config_file):
    config,supported_services = read_config_ini(config_file)
    for (key, val) in config.items("celerystalk-config"):
        if key == "max_screenshots_per_vhost":
            return val

def get_user_config(config_file):
    config,supported_services = read_config_ini(config_file)
    return config.items("user-config")


def extract_bb_nmap_options(config_file=None):
    config = ConfigParser(allow_no_value=True)
    config.read([config_file])

    for (key, val) in config.items("nmap-commands"):
        if key == "tcp_scan":
            bb_nmap_command = val
            options = bb_nmap_command.replace('nmap', '').replace('[TARGET]', '')
            return options

def extract_udp_scan_nmap_options(config_file=None):
    config = ConfigParser(allow_no_value=True)
    config.read([config_file])

    for (key, val) in config.items("nmap-commands"):
        if key == "udp_scan":
            udp_nmap_command = val
            options = udp_nmap_command.replace('nmap', '').replace('[TARGET]', '')
            return options

def read_bb_scope_ini(bb_scope_file):
    bb_config = ConfigParser(allow_no_value=True)
    bb_config.read([bb_scope_file])

    in_scope_domains = []
    in_scope_hosts = []
    out_of_scope_hosts = []

    #print(type(bb_config.items(['in-scope-domains'])))

    try:
        for key,val in bb_config.items('in-scope-domains'):
            in_scope_domains.append(key)
    except:
        pass
    try:
        for key in bb_config.items('in-scope-hosts'):
            in_scope_hosts.append(key)
    except:
        pass
    try:
        for key in bb_config.items('out-of-scope-hosts'):
            out_of_scope_hosts.append(key)
    except:
        pass

    return in_scope_domains,in_scope_hosts,out_of_scope_hosts

