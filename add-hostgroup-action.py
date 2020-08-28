# coding:utf8
import requests
import json
import configparser
import sys
import time

reload(sys)
sys.setdefaultencoding('utf-8')

# 定义url头部信息
headers = {'Content-Type': 'application/json-rpc'}  # zabbix地址
server_ip = '192.168.81.100'
# zabbix url
url = 'http://%s/zabbix/api_jsonrpc.php' % server_ip
host = 'https://cmdb.yeahmobi.com/api/v1'
data_dir = '/etc/zabbix/python_script/data_json/'
def get_access(tokens):

    conf = configparser.ConfigParser()
    conf.read("access.ini", encoding="utf8")
    if tokens == "cmdb":
        username_cmdb = conf.get('access', 'username_cmdb')
        password_cmdb = conf.get('access', 'password_cmdb')
        return username_cmdb, password_cmdb
    elif tokens == "zabbix":
        username_zabbix = conf.get('zabbix', 'username_zabbix')
        password_zabbix = conf.get('zabbix', 'password_zabbix')
        return username_zabbix, password_zabbix

def get_cmdb_token():
    """
    获取token
    参数：username是邮箱账号，password是邮箱密码
    :return:token
    """
    username, password = get_access("cmdb")
    auth_token = None
    url = '{}/auth'.format(host)
    # print(url)
    query_args = {
        "username": username,
        "password": password,
        "type": "normal"
    }
    try:
        response = requests.post(url, data=query_args)
        auth_token = json.loads(response.text)['auth_token']
    except:
        pass

    return auth_token

def get_codename():  # 获取所有的codename列表

    token = get_cmdb_token()
    params = {
        'page_size': 1000,
        'page': 1
    }

    url = "{}/application/get_codename".format(host)
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer %s" % token
    }
    response = requests.get(url, params=params, headers=headers)
    res = json.loads(response.text)
    return res

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

# 获取groupID
def getGroupid():
    token = get_zabbix_Token()
    group = {}
    data = {"jsonrpc": "2.0",
            "method": "hostgroup.get",
            "params": {
                "output": ["groupid", "name"]
            },
            "auth": token,
            "id": 0
            }

    request = requests.post(url=url, headers=headers, data=json.dumps(data))
    dict = json.loads(request.content)
    for i in dict['result']:
        groupid = i['groupid']
        name = i['name']
        group[name] = groupid
    return group

#获取CMDB上的codename列表

def codename_load_json_dict():  ##读本地保存的项目-部门-codename关系的json文件
    load_json = open(data_dir+'Project_Department_Codename.json', 'r')
    Project_Department_Codename = json.load(load_json)
    return Project_Department_Codename

#获取project，department列表

def Project_Department_list():
    date_dict = codename_load_json_dict()
    date_list = date_dict["results"]
    project_list = []
    department_list = []
    code_list = []

    for i in range(len(date_list)):
        project_name = date_list[i]['project_extra_info']["name"]
        department_name = date_list[i]['department_extra_info']["name"]
        code_name = date_list[i]["codename"]
        project_list.append(project_name)
        department_list.append(department_name)
        code_list.append(code_name)

    project_list = set(project_list)
    project_list = list(project_list)

    department_list = set(department_list)
    department_list = list(department_list)

    return project_list, department_list


#判断有无新增的分组
def new_hostgroup():
    codenames = get_codename()
    hostgroup = getGroupid().keys()
    project_list, department_list = Project_Department_list()
    codenames_add = []
    project_list_add = []
    department_list_add = []
    for i in codenames:
        codenames_add.append("CodeName_" + i)
    for j in project_list:
        project_list_add.append("Project_" + j )
    for x in department_list:
        department_list_add.append("Department_" + x )
    codenames_project_department = codenames_add + project_list_add + department_list_add
    new_hostgroup = []
    for i in codenames_project_department:
        if i not in hostgroup:
            new_hostgroup.append(i)
    return new_hostgroup


def get_action_data():
    project_list, department_list = Project_Department_list()
    code_list= get_codename()
    data = codename_load_json_dict()['results']
    group_id = getGroupid()
    action_data = []

    for i in code_list:
        a = {}
        if "CodeName_"+i in group_id.keys():
            id = group_id["CodeName_"+i]
            a["ID_codename"] = id
            a["codename"] = i
        for j in range(len(data)):
            if i == data[j]["codename"]:
                project = data[j]['project_extra_info']['name']
                department = data[j]['department_extra_info']['name']
                id_pro = group_id["Project_"+ project]
                id_dept = group_id["Department_"+department ]
                a["ID_project"] = id_pro
                a["ID_deparment"] = id_dept
                action_data.append(a)
    return action_data

def add_action():
    action_data = get_action_data()
    for i in range(len(action_data)):
        token = get_zabbix_Token()
        codename = action_data[i]["codename"]
        ID_codename = action_data[i]["ID_codename"]
        ID_deparment = action_data[i]["ID_deparment"]
        ID_project = action_data[i]["ID_project"]
        data = {
        "jsonrpc": "2.0",
        "method": "action.create",
        "params":{
                "status": "0",
                "operations": [
                    {
                        "operationtype": "4",
                        "esc_period": "0",
                        "recovery": "0",
                        "evaltype": "0",
                        "opconditions": [],
                        "esc_step_to": "1",
                        "esc_step_from": "1",
                        "opgroup": [
                        {
                            "groupid": ID_codename,
                        },
                        {
                            "groupid": ID_deparment,
                        },
                        {
                            "groupid": ID_project,
                        }
                    ],
                    }
                ],
                #"def_shortdata": "Auto registration: {HOST.HOST}",
                "name": "auto-registration_" + codename,
                "esc_period": "0",
                #"def_longdata": "Host name: {HOST.HOST}\r\nHost IP: {HOST.IP}\r\nAgent port: {HOST.PORT}",
                "filter": {
                    "formula": "",
                    "evaltype": "0",
                    "conditions": [
                        {
                            "operator": "2",        #2 - like
                            "conditiontype": "24",  #主机元数据
                            "formulaid": "A",
                            "value2": "",
                            "value": codename
                        }
                    ],
                },
                "eventsource": "2",
                "r_shortdata": "",
                "r_longdata": "",
                "recoveryOperations": []
            },
        "auth": token,
        "id": 10
    }
        request = requests.post(url=url, headers=headers, data=json.dumps(data))
        dict = json.loads(request.content)



#添加主机组
def add_hostgroup():
    all_hostgroup = new_hostgroup()
    if len(all_hostgroup) != 0:
        for i in all_hostgroup:
            token = get_zabbix_Token()
            data = {
            "jsonrpc": "2.0",
            "method": "hostgroup.create",
            "params": {
                "name": i
            },
            "auth": token,
            "id": 1
        }

            request = requests.post(url=url, headers=headers, data=json.dumps(data))
            res = json.loads(request.content)
        time.sleep(1)
	add_action()
    else:
        print "no add hostgroup and action"

def main():
    add_hostgroup()
if __name__ == "__main__":
    main()
