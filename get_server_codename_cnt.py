# -*- coding: utf-8 -*-
import requests
import json
import commands
import configparser
import time
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

host = 'https://cmdb.yeahmobi.com/api/v1'
data_dir = '/etc/zabbix/python_script/data_json/'
#data_dir = ""
hostname = "k8s-node3"  #根据实际情况修改
zabbix_server = "192.168.81.100"

def get_access():
    conf = configparser.ConfigParser()
    conf.read("/etc/zabbix/python_script/access.ini", encoding="utf8")
    username = conf.get('access', 'username_cmdb')
    password = conf.get('access', 'password_cmdb')
    return username, password


def get_token():
    """
    获取token
    参数：username是邮箱账号，password是邮箱密码
    :return:token
    """
    username, password = get_access()
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


def get_all_server_ec():  # 获取所有服务器
    """
    获取ec2列表，如果要单独查询codename，使用search=pink,要单独查询区域，search=sa-east-1，不能同时查询
    分页查询：page是页码，page_size是每页返回数据的条数
    :return: 服务器列表
    """
    token = get_token()
    params = {
        # 'search': 'pink',
        'page_size': 1000,
        'page': 1
    }

    url = "{}/server".format(host)
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer %s" % token
    }
    response = requests.get(url, params=params, headers=headers)
    res = json.loads(response.text)

    all_servers_json = json.dumps(res, sort_keys=False, indent=4, separators=(',', ': '))
    f = open(data_dir+'all_server_list.json', 'w')
    f.write(all_servers_json)


def load_json_service_dict():  # 读本地所有服务器的json文件
    load_json = open(data_dir+'all_server_list.json', 'r')
    all_server_json = json.load(load_json)
    return all_server_json


def codename_load_json_dict():  ##读本地保存的项目-部门-codename关系的json文件
    load_json = open(data_dir+'Project_Department_Codename.json', 'r')
    Project_Department_Codename = json.load(load_json)
    return Project_Department_Codename


def get_all_servers_num():  # 获取服务器总数
    all_server_json = load_json_dict()
    all_server_num = all_server_json['count']
    return all_server_num


def get_server_flavor_num():
    cmd_flavor_C = 'cat all_server_list.json | grep -w "InstanceType" |' \
                   'grep -v info| sed -e \'s/"InstanceType": "//\' -e \'s/",//\'' \
                   ' -e \'s/ecs.//\' -e \'s/ //g\'|grep "^c[0-9]"|wc -l'
    cmd_flavor_M = 'cat all_server_list.json | grep -w "InstanceType" |' \
                   'grep -v info| sed -e \'s/"InstanceType": "//\' -e \'s/",//\'' \
                   ' -e \'s/ecs.//\' -e \'s/ //g\'|grep "^m[0-9]"|wc -l'
    cmd_flavor_R = 'cat all_server_list.json | grep -w "InstanceType" |' \
                   'grep -v info| sed -e \'s/"InstanceType": "//\' -e \'s/",//\'' \
                   ' -e \'s/ecs.//\' -e \'s/ //g\'|grep "^r[0-9]"|wc -l'
    cmd_flavor_G = 'cat all_server_list.json | grep -w "InstanceType" |' \
                   'grep -v info| sed -e \'s/"InstanceType": "//\' -e \'s/",//\'' \
                   ' -e \'s/ecs.//\' -e \'s/ //g\'|grep "^g[0-9]"|wc -l'
    cmd_flavor_O = 'cat all_server_list.json | grep -w "InstanceType" |' \
                   'grep -v info| sed -e \'s/"InstanceType": "//\' -e \'s/",//\'' \
                   ' -e \'s/ecs.//\' -e \'s/ //g\'|grep -v "^[m|c|r|g][0-9]"|wc -l'

    all_num = get_all_servers_num()

    C_flavor_num = commands.getoutput(cmd_flavor_C)
    M_flavor_num_tmp = commands.getoutput(cmd_flavor_M)
    R_flavor_num = commands.getoutput(cmd_flavor_R)
    G_flavor_num_tmp = commands.getoutput(cmd_flavor_G)
    O_flavor_num = commands.getoutput(cmd_flavor_O)

    M_flavor_num = int(M_flavor_num_tmp) + int(G_flavor_num_tmp)

    print "all_num:%s" % (all_num)
    print "C系列num:%s" % (C_flavor_num)
    print "M系列num:%s" % (M_flavor_num)
    print "R系列num:%s" % (R_flavor_num)
    print "Other:%s" % (O_flavor_num)

    return all_num, C_flavor_num, M_flavor_num, R_flavor_num, O_flavor_num


def get_data_list():  # 从json文件中获取的需要的信息，输出字典格式[{"resourceId"："xxx","cloud":"ali","codename":"xxx","InstanceType":"s1.xxx"},{}]
    data = []
    res1 = load_json_service_dict()
    res = res1["results"]
    for i in range(len(res)):
        data_dic = {}
        resourceId = res[i]["resourceId"]
        cloud = res[i]["cloud"]
        codename = res[i]["codename"]
        InstanceType = res[i]["instance_type"]
        region = res[i]["region"]
        data_dic["resourceId"] = resourceId
        data_dic["cloud"] = cloud
        data_dic["codename"] = codename
        data_dic["InstanceType"] = InstanceType
        data_dic["region"] = region
        data.append(data_dic)
    return data


def get_Project_Department_Codename():  # 调接口获取项目/部门/Item对应关系
    """
    获取ec2列表，如果要单独查询codename，使用search=pink,要单独查询区域，search=sa-east-1，不能同时查询
    分页查询：page是页码，page_size是每页返回数据的条数
    :return: 服务器列表
    """
    token = get_token()
    # params = {
    #        'page_size': 100,
    #        'page': 3
    #   }
    i = 1
    res = []
    res_data = {}
    while i <= 3:
        url = "{}/application?project=&ordering=&search=&page_size=100&page=%d".format(host) %(i)
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer %s" % token
        }
        response = requests.get(url, params=" ", headers=headers)
        res1 = json.loads(response.text)
        for j in range(len(res1['results'])):
            res.append(res1['results'][j])
        i = i+1
    res_data['results'] = res
    Project_Department_Codename = json.dumps(res_data, sort_keys=False, ensure_ascii=False, indent=4, separators=(',', ': '))
    f = open(data_dir+'Project_Department_Codename.json', 'w')
    f.write(Project_Department_Codename)


def get_codename():  # 获取所有的codename列表

    token = get_token()
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
    discovery_ecs_codename = json.dumps(res, sort_keys=False, ensure_ascii=False, indent=4, separators=(',', ': '))
    f = open('/etc/zabbix/discovery_data/discovery_ecs_codename.json', 'w')
    f.write(discovery_ecs_codename)
    return res


def codename_num():  # 从all_server_list.json里面获取数据
    all_codename_num = {}
    all_codename_num_aws = {}
    all_codename_num_ali = {}
    code_name = get_codename()
    data = get_data_list()
    codename_error_dict = {}
    codename_error_list = []
    for i in range(len(code_name)):
        code_name_tag = code_name[i]
        sum_c = 0
        sum_m = 0
        sum_r = 0
        sum_g = 0
        sum_o = 0
        sum_notag_aws_c = 0
        sum_notag_aws_m = 0
        sum_notag_aws_r = 0
        sum_notag_aws_g = 0
        sum_notag_aws_o = 0

        sum_notag_ali_c = 0
        sum_notag_ali_m = 0
        sum_notag_ali_r = 0
        sum_notag_ali_g = 0
        sum_notag_ali_o = 0
        for j in range(len(data)):
            if str(data[j]["codename"]) != "None":
                if str(data[j]["codename"]) == str(code_name_tag):# 判断all_server里面的codename是否在列表中
                    if str(data[j]["cloud"]) == "aws":
                        if str(data[j]["InstanceType"]).startswith('c'):
                            sum_c = sum_c + 1
                        elif str(data[j]["InstanceType"]).startswith('m'):
                            sum_m = sum_m + 1
                        elif str(data[j]["InstanceType"]).startswith('r'):
                            sum_r = sum_r + 1
                        elif str(data[j]["InstanceType"]).startswith('g'):
                            sum_g = sum_g + 1
                        else:
                            sum_o = sum_o + 1

                    elif str(data[j]["cloud"]) == "aliyun":
                        if str(data[j]["InstanceType"]).startswith('ecs.c'):
                            sum_c = sum_c + 1
                        elif str(data[j]["InstanceType"]).startswith('ecs.m'):
                            sum_m = sum_m + 1
                        elif str(data[j]["InstanceType"]).startswith('ecs.r'):
                            sum_r = sum_r + 1
                        elif str(data[j]["InstanceType"]).startswith('ecs.g'):
                            sum_g = sum_g + 1
                        else:
                            sum_o = sum_o + 1

                else:
                    if data[j]["codename"] not in code_name:
                        if str(data[j]["cloud"]) == "aws":
                            if str(data[j]["InstanceType"]).startswith('c'):
                                sum_notag_aws_c = sum_notag_aws_c + 1
                            elif str(data[j]["InstanceType"]).startswith('m'):
                                sum_notag_aws_m = sum_notag_aws_m + 1
                            elif str(data[j]["InstanceType"]).startswith('r'):
                                sum_notag_aws_r = sum_notag_aws_r + 1
                            elif str(data[j]["InstanceType"]).startswith('g'):
                                sum_notag_aws_g = sum_notag_aws_g + 1
                            else:
                                sum_notag_aws_o = sum_notag_aws_o + 1
                        elif str(data[j]["cloud"]) == "aliyun":
                            if str(data[j]["InstanceType"]).startswith('ecs.c'):
                                sum_notag_ali_c = sum_notag_ali_c + 1
                            elif str(data[j]["InstanceType"]).startswith('ecs.m'):
                                sum_notag_ali_m = sum_notag_ali_m + 1
                            elif str(data[j]["InstanceType"]).startswith('ecs.r'):
                                sum_notag_ali_r = sum_notag_ali_r + 1
                            elif str(data[j]["InstanceType"]).startswith('ecs.g'):
                                sum_notag_ali_g = sum_notag_ali_g + 1
                            else:
                                sum_notag_ali_o = sum_notag_ali_o + 1
            else:
                if str(data[j]["cloud"]) == "aws":
                    if str(data[j]["InstanceType"]).startswith('c'):
                        sum_notag_aws_c = sum_notag_aws_c + 1
                    elif str(data[j]["InstanceType"]).startswith('m'):
                        sum_notag_aws_m = sum_notag_aws_m + 1
                    elif str(data[j]["InstanceType"]).startswith('r'):
                        sum_notag_aws_r = sum_notag_aws_r + 1
                    elif str(data[j]["InstanceType"]).startswith('g'):
                        sum_notag_aws_g = sum_notag_aws_g + 1
                    else:
                        sum_notag_aws_o = sum_notag_aws_o + 1
                elif str(data[j]["cloud"]) == "aliyun":
                    if str(data[j]["InstanceType"]).startswith('ecs.c'):
                        sum_notag_ali_c = sum_notag_ali_c + 1
                    elif str(data[j]["InstanceType"]).startswith('ecs.m'):
                        sum_notag_ali_m = sum_notag_ali_m + 1
                    elif str(data[j]["InstanceType"]).startswith('ecs.r'):
                        sum_notag_ali_r = sum_notag_ali_r + 1
                    elif str(data[j]["InstanceType"]).startswith('ecs.g'):
                        sum_notag_ali_g = sum_notag_ali_g + 1
                    else:
                        sum_notag_ali_o = sum_notag_ali_o + 1

        sum_M = sum_m + sum_g
        sum_all = sum_c + sum_M + sum_r + sum_o
        all_codename_num[code_name_tag] = {}
        all_codename_num[code_name_tag]["ecscnt_" + code_name_tag + "_C"] = sum_c
        all_codename_num[code_name_tag]["ecscnt_" + code_name_tag + "_M"] = sum_M
        all_codename_num[code_name_tag]["ecscnt_" + code_name[i] + "_R"] = sum_r
        all_codename_num[code_name_tag]["ecscnt_" + code_name_tag + "_O"] = sum_o
        all_codename_num[code_name_tag]["ecscnt_" + code_name_tag + "_All"] = sum_all

        # all_codename_num[code_name_tag + "_M"] = sum_m
        # all_codename_num[code_name_tag + "_R"] = sum_r
        # all_codename_num[code_name_tag + "_O"] = sum_o

        sum_notag_aws_M = sum_notag_aws_m + sum_notag_aws_g
        sum_notag_aws_all = sum_notag_aws_o + sum_notag_aws_r + sum_notag_aws_M + sum_notag_aws_c
        all_codename_num_aws["cnt_notag_aws"]={}
        all_codename_num_aws["cnt_notag_aws"]["ecscnt_notag-aws_C"] = sum_notag_aws_c
        all_codename_num_aws["cnt_notag_aws"]["ecscnt_notag-aws_M"] = sum_notag_aws_M
        all_codename_num_aws["cnt_notag_aws"]["ecscnt_notag-aws_R"] = sum_notag_aws_r
        all_codename_num_aws["cnt_notag_aws"]["ecscnt_notag-aws_O"] = sum_notag_aws_o
        all_codename_num_aws["cnt_notag_aws"]["ecscnt_notag-aws_All"] = sum_notag_aws_all

        sum_notag_ali_M = sum_notag_ali_m + sum_notag_ali_g
        sum_notag_ali_all = sum_notag_ali_c + sum_notag_ali_M + sum_notag_ali_r + sum_notag_ali_o
        all_codename_num_ali["cnt_notag-ym-diangao-ali"]={}
        all_codename_num_ali["cnt_notag-ym-diangao-ali"]["ecscnt_notag-ym-diangao-ali_C"] = sum_notag_ali_c
        all_codename_num_ali["cnt_notag-ym-diangao-ali"][ "ecscnt_notag-ym-diangao-ali_M"] = sum_notag_ali_M
        all_codename_num_ali["cnt_notag-ym-diangao-ali"]["ecscnt_notag-ym-diangao-ali_R"] = sum_notag_ali_r
        all_codename_num_ali["cnt_notag-ym-diangao-ali"]["ecscnt_notag-ym-diangao-ali_O"] = sum_notag_ali_o
        all_codename_num_ali["cnt_notag-ym-diangao-ali"]["ecscnt_notag-ym-diangao-ali_All"] = sum_notag_ali_all

    # for j in range(len(data)):  #查找标签错误的虚拟机。
    #     if str(data[j]["codename"]) != "None":
    #         if str(data[j]["codename"]) in code_name:
    #         else:
    #             if str(data[j]["cloud"]) == "aws":
    #                 codename_error_dict["resourceId"] = data[j]["resourceId"]
    #                 codename_error_dict["cloud"] = data[j]["cloud"]
    #                 codename_error_dict["codename"] = data[j]["codename"]
    #                 codename_error_dict["InstanceType"] = data[j]["InstanceType"]
    #                 codename_error_dict["region"] = data[j]["region"]
    #
    #                 codename_error_list.append(codename_error_dict)
    return all_codename_num, all_codename_num_aws, all_codename_num_ali


def Project_Department_Codename():
    all_codename_num, all_codename_num_aws, all_codename_num_ali = codename_num()
    date_dict = codename_load_json_dict()
    date_list = date_dict["results"]
    project_dict = {}

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

    code_list = set(code_list)
    code_list = list(code_list)
    a = {}
    b = {}
    for i in project_list:  # 项目ID
        code_name_list = {}
        for j in range(len(date_list)):
            if date_list[j]['project_extra_info']["name"] == i:
                for x in all_codename_num.keys():
                    if x == date_list[j]["codename"]:
                        code_name_list[date_list[j]["codename"]] = all_codename_num[x]
        a[i]=code_name_list

    for i in department_list:
        project_name_list = {}
        for j in range(len(date_list)):
            if date_list[j]['department_extra_info']["name"] == i:
                for x in a.keys(): #x是项目ID
                    if x  == date_list[j]['project_extra_info']["name"]:
                        project_name_list[date_list[j]['project_extra_info']["name"]] = a[x]
        b[i] = project_name_list
    department_name_list = b
    department_name_list["cnt_notag"] = all_codename_num_aws
    department_name_list["cnt_notag-ym-diangao-ali"] = all_codename_num_ali
    # department_name_list["codecame_error"] = codename_error_list
    all_servers_json = json.dumps(department_name_list, sort_keys=False, ensure_ascii=False, indent=4,separators=(',', ': '))
    # print all_servers_json
    f1 = open(data_dir+'codename_count_data.json', 'w')
    f1.write(all_servers_json)

    discover_project_list_json= json.dumps(project_list, sort_keys=False, ensure_ascii=False, indent=4,
                                  separators=(',', ': '))
    # print all_servers_json
    f2 = open('/etc/zabbix/discovery_data/discover_project_list_json.json', 'w')
    f2.write(discover_project_list_json)

    discover_deparment_list_json =  json.dumps(department_list, sort_keys=False, ensure_ascii=False, indent=4,separators=(',', ': '))
    f3 = open('/etc/zabbix/discovery_data/discover_deparment_list_json.json', 'w')
    f3.write(discover_deparment_list_json)

    return department_name_list


def zabbix_sender_date():
    load_json = open(data_dir+'codename_count_data.json', 'r')
    codename_count_data = json.load(load_json)

    cmd_zabix_sender_data = 'cat '+data_dir+'codename_count_data.json | grep ecs | sed -e \'s/"//g\'' \
                            ' -e \'s/:/ /g\' -e \'s/,//\' -e \'s/^/"'+hostname+'"/\'' \
                            ' -e \'s/_/_[/\' -e \'s/_[B-Z]/&]/\' -e \'s/All/&]/\' > zabbix_sendfile_codename'

    commands.getoutput(cmd_zabix_sender_data)
    time.sleep(1)
    zabbix_file = 'zabbix_sender -z '+zabbix_server+' -i zabbix_sendfile_codename > /dev/null 2>&1'
    commands.getoutput(zabbix_file)


def main():
    get_all_server_ec()  # 获取所有服务器并保存json文件
    get_Project_Department_Codename()  # 调接口获取项目/部门/Item对应关系并保存json文件
    a = Project_Department_Codename()
    zabbix_sender_date()


if __name__ == '__main__':
    main()

