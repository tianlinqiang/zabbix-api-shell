# -*- coding: utf-8 -*-
import requests
import json
import configparser
import sys
import time
import commands

reload(sys)
sys.setdefaultencoding('utf-8')

# 定义url头部信息
headers = {'Content-Type': 'application/json-rpc'}  # zabbix地址
server_ip = '192.168.81.100'
# zabbix url
url = 'http://%s/zabbix/api_jsonrpc.php' % server_ip
data_dir_script = '/etc/zabbix/discovery_data/'
hostname = "k8s-node3"
zabbix_server = "192.168.81.100"



def get_access(tokens):

    conf = configparser.ConfigParser()
    conf.read("/etc/zabbix/python_script/access.ini", encoding="utf8")
    if tokens == "cmdb":
        username_cmdb = conf.get('access', 'username_cmdb')
        password_cmdb = conf.get('access', 'password_cmdb')
        return username_cmdb, password_cmdb
    elif tokens == "zabbix":
        username_zabbix = conf.get('zabbix', 'username_zabbix')
        password_zabbix = conf.get('zabbix', 'password_zabbix')
        return username_zabbix, password_zabbix


# 获取zabbix 的 token
def get_zabbix_Token():
    username, passwd = get_access("zabbix")
    data = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {
            "user": username,
            "password": passwd
        },
        "id": 0

    }

    request = requests.post(url=url, headers=headers, data=json.dumps(data))
    dict = json.loads(request.text)
    return dict['result']


def get_groupnames():
    token = get_zabbix_Token()
    groups_list = []
    data = {"jsonrpc": "2.0",
            "method": "hostgroup.get",
            "params": {
                "output": ["name"]
            },
            "auth": token,
            "id": 0
            }

    request = requests.post(url=url, headers=headers, data=json.dumps(data))
    dict = json.loads(request.content)
    for i in dict['result']:
        name = i['name']
        groups_list.append(name)
    return groups_list


def get_datasize():
    data_list = []
    data_dict = {}
    groups_list = get_groupnames()
    groups_list.remove("Discovered hosts")
    groups_list.remove("Linux servers")
    groups_list.remove("Templates")
    groups_list.remove("Zabbix servers")
    groups_list.remove("Virtual machines")
    groups_list.remove("Hypervisors")
    for i in groups_list:
        token = get_zabbix_Token()
        data = {
        "jsonrpc": "2.0",
        "method": "item.get",
        "params": {
            "output": ["lastvalue"],
            "type": 0,
            "group": i,
            "search": {
                "name": "Total disk space on $1"
            },
        },
        "auth": token,
        "id": 1
    }
        request = requests.post(url=url, headers=headers, data=json.dumps(data))
        dict = json.loads(request.content)
        if len(dict['result'])> 0:
            data_size = 0
            for j in range(len(dict['result'])):
                data_size = int(dict['result'][j]['lastvalue'])+ data_size
        else:
            data_size = 0
        b = 1024
        data_size = format(float(data_size)/float(b)/float(b)/float(b),'.2f')
        data_dict["volumesize_"+i+"_All"]=data_size

        #data_list.append(data_dict)

    all_servers_json = json.dumps(data_dict, sort_keys=False, ensure_ascii=False,indent=4, separators=(',', ': '))
    f = open(data_dir_script + 'get_datasize_json.json', 'w')
    f.write(all_servers_json)
    grouplsit = json.dumps(groups_list, sort_keys=False, ensure_ascii=False, indent=4, separators=(',', ': '))
    f = open(data_dir_script + 'get_groups_list_json.json', 'w')
    f.write(grouplsit)

def zabbix_sendfile_volumesize():
    cmd_zabix_sender_data = 'cat ' + data_dir_script + 'get_datasize_json.json | grep ":" | sed -e \'s/"//g\'' \
                            ' -e \'s/:/ /g\' -e \'s/,//\' -e \'s/^/"'+hostname+'"/\'' \
                            ' -e \'s/[A-Z]/[&/\' -e \'s/All/&]/\' > zabbix_sendfile_volumesize'

    commands.getoutput(cmd_zabix_sender_data)
    time.sleep(1)
    zabbix_file = 'zabbix_sender -z '+zabbix_server+' -i zabbix_sendfile_volumesize > /dev/null 2>&1'
    commands.getoutput(zabbix_file)


def main():
    get_datasize()
    zabbix_sendfile_volumesize()
if __name__ == "__main__":
    main()
