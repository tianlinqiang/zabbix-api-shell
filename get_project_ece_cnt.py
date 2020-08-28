# -*- coding: utf-8 -*-
import json
import commands
import sys
import time
reload(sys)
sys.setdefaultencoding('utf-8')

zabbix_server = "192.168.81.100"
hostname = "k8s-node3"
data_dir = '/etc/zabbix/python_script/data_json/'
#data_dir = ""

def Project_Department_Codename_json_dict(): ##读本地保存的项目-部门-codename关系的json文件
    load_json = open(data_dir+'Project_Department_Codename.json', 'r')
    date_dict = json.load(load_json)
    date_list = date_dict["results"]
    project_list = []
    department_list = []

    for i in range(len(date_list)):
        project_name = date_list[i]['project_extra_info']["name"]
        department_name = date_list[i]['department_extra_info']["name"]
        project_list.append(project_name)
        department_list.append(department_name)

    project_list = set(project_list)
    project_list = list(project_list)

    department_list = set(department_list)
    department_list = list(department_list)
    return department_list,project_list

def get_project_ecs_cnt():
    department_list, project_list = Project_Department_Codename_json_dict()
    project_ecs_cnt_list = []
    load_json = open(data_dir+'codename_count_data.json', 'r')  # 路径正式用的时候需要修改
    date_dict = json.load(load_json)
    for i in department_list:

        date_list = date_dict[i]  #第一个部门里面的项目循环，date_list第一个项目字典。
        for j in date_list: #j=各个项目名称
            sum_C = 0
            sum_R = 0
            sum_O = 0
            sum_M = 0
            sum_All = 0
            project_ecs_cnt_dic = {}
            for x in range(len(date_list[j].values())):#循环第一个部门里面的第一个项目里面的所有字典的值（x=列表序号）       #[{u'ecscnt_tkyweb_C': 0, u'ecscnt_tkyweb_R': 0, u'ecscnt_tkyweb_All': 1, u'ecscnt_tkyweb_O': 1, u'ecscnt_tkyweb_M': 0}, {}]
                for z in date_list[j].values()[x].keys():
#循环的是所有的key,date_list[j].values()[x].keys()是列表，[u'ecscnt_cx003_O', u'ecscnt_cx003_M',
                    if str(z).endswith('C'): # u'ecscnt_cx003_R', u'ecscnt_cx003_C', u'ecscnt_cx003_All']
                        sum_C = int(sum_C) + int(date_list[j].values()[x][z])
                    elif str(z).endswith('R'):
                        sum_R = int(sum_R) + int(date_list[j].values()[x][z])
                    elif str(z).endswith('O'):
                        sum_O = int(sum_O) + int(date_list[j].values()[x][z])
                    elif str(z).endswith('M'):
                        sum_M = int(sum_M) + int(date_list[j].values()[x][z])
                    elif str(z).endswith('All'):
                        sum_All = int(sum_All) + int(date_list[j].values()[x][z])
            project_ecs_cnt_dic["ecscnt_"+j + "_C"] = sum_C
            project_ecs_cnt_dic["ecscnt_"+j + "_R"] = sum_R
            project_ecs_cnt_dic["ecscnt_"+j + "_O"] = sum_O
            project_ecs_cnt_dic["ecscnt_"+j + "_M"] = sum_M
            project_ecs_cnt_dic["ecscnt_"+j + "_All"] = sum_All
            project_ecs_cnt_list.append(project_ecs_cnt_dic)

    project_ecs_cnt = json.dumps(project_ecs_cnt_list, sort_keys=False, ensure_ascii=False, indent=4,
                                  separators=(',', ': '))
    f = open(data_dir+'project_ecs_cnt.json', 'w')
    f.write(project_ecs_cnt)

def zabbix_sender_date():
    load_json = open(data_dir+'project_ecs_cnt.json', 'r')
    codename_count_data = json.load(load_json)

    cmd_zabix_sender_data = 'cat '+data_dir+'project_ecs_cnt.json | grep ":" | sed -e \'s/"//g\'' \
                            ' -e \'s/:/ /g\' -e \'s/,//\' -e \'s/^/"'+hostname+'"/\'' \
                            ' -e \'s/_/_[/\' -e \'s/_[B-Z]/&]/\' -e \'s/All/&]/\' > zabbix_sendfile_project'

    commands.getoutput(cmd_zabix_sender_data)
    time.sleep(1)
    zabbix_file = 'zabbix_sender -z '+zabbix_server+' -i zabbix_sendfile_project > /dev/null 2>&1'
    commands.getoutput(zabbix_file)


def main():
    get_project_ecs_cnt()
    time.sleep(1)
    zabbix_sender_date()

if __name__ == '__main__':
    main()


