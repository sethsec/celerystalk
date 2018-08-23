import simplejson
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


def read_config_ini():
    config = ConfigParser()
    config.read(['config.ini'])

    supported_services = []
    for (key,val) in config.items("nmap-service-names"):
        services = val.split(",")
        for service in services:
            supported_services.append(service)
    return config,supported_services


def extract_bb_nmap_options():
    config = ConfigParser(allow_no_value=True)
    config.read(['config.ini'])

    for (key, val) in config.items("nmap-commands"):
        if key == "bug_bounty_mode":
            bb_nmap_command = val
            options = bb_nmap_command.replace('nmap', '').replace('[TARGET]', '')
            return options


    # try:
    #     bb_nmap_command = config['nmap-commands']['bug_bounty_mode']
    #     options = bb_nmap_command.replace('nmap','').replace('[TARGET]','')
    #     return options
    # except:
    #     print("Are you sure only command is enabled in this section?")






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





# def read_config():
#     with open("config.json", "r") as config:
#         c = config.read()
#         json_config = simplejson.loads(
#             c.replace("$IP", "%(IP)s").replace("$PORT", "%(PORT)s").replace("$OUTPUTDIR", "%(OUTPUTDIR)s"))
#     # This make a list of all supported services so that later we can determine if each service is supported or not.
#     # If a service is not supported, we need to tell the user so they can test manually or look for commands to add to
#     # the config.
#
#     supported_services = []
#     for service in json_config["services"]:
#         for a in json_config["services"][service]["nmap-service-names"]:
#             supported_services.append(a)
#     return json_config, supported_services
#
#
# def read_config_post(path):
#     with open("config.json", "r") as config:
#         c = config.read()
#         json_config = simplejson.loads(
#             c.replace("http://$IP:$PORT/", path).replace("htts://$IP:$PORT/", path).replace("$OUTPUTDIR", "%(OUTPUTDIR)s"))
#
#     return json_config


