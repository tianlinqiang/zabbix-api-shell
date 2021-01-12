# -*- coding: utf-8 -*-

import json
import configparser
import sys
import boto3
import datetime
import requests
import commands
import time

from multiprocessing import Manager,Process
from multiprocessing import Pool

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkcms.request.v20190101.DescribeMetricListRequest import DescribeMetricListRequest

reload(sys)
sys.setdefaultencoding('utf8')

data_dir = "/etc/zabbix/python_script/data_json/"
host = 'https://cmdb.xxxxxxxx.com/api/v1'

hostname = "ali-sin101-pubservice-255-103"
# zabbix_server = '10.2.255.21'
zabbix_server = '10.xxx.xxx.91'
awk_file = '/root/xxx/xxxx'  # 正式环境使用
ali_file = '/root/xxx/xxx.json'  # 正式环境使用



def get_access():
    conf = configparser.ConfigParser()
    conf.read("/etc/zabbix/python_script/access.ini", encoding="utf8")
    username_cmdb = conf.get('access', 'username_cmdb')
    password_cmdb = conf.get('access', 'password_cmdb')
    return username_cmdb, password_cmdb


def get_profile_load_json_dict():
    load_json = open('/etc/zabbix/discovery_data/discovery_ecs_account_region.json', 'r')
    profile = json.load(load_json)
    return profile


def get_aws_s3_totle_size(ak, sk, region, bucketname):
    client = boto3.client('cloudwatch',
                          aws_access_key_id=ak,
                          aws_secret_access_key=sk,
                          region_name=region)
    oneday = datetime.timedelta(days=1)
    starttime = datetime.datetime.now() - oneday
    nowtime = datetime.datetime.now()
    aws_total_size_all = 0
    StorageType_list = ["DeepArchiveS3ObjectOverhead", "GlacierObjectOverhead", "DeepArchiveStorage",
                        "GlacierS3ObjectOverhead", "StandardStorage", "DeepArchiveObjectOverhead", "StandardIAStorage",
                        "GlacierStorage"]
    for i in StorageType_list:
        response = client.get_metric_statistics(
            Namespace='AWS/S3',
            MetricName='BucketSizeBytes',
            Dimensions=[
                {
                    'Name': 'BucketName',
                    'Value': bucketname
                },
                {
                    'Name': 'StorageType',
                    'Value': i
                }
            ],
            StartTime=starttime.strftime('%Y-%m-%d'),
            EndTime=nowtime.strftime('%Y-%m-%d'),
            Period=86400,
            Statistics=[
                'Average'
            ],
            Unit='Bytes',
        )

        if len(response.get('Datapoints')) != 0:
            a_list = response.get('Datapoints')[0]
            aws_total_size = round(a_list.get('Average') / 1024, 3)  # 单位kb
            aws_total_size_all = aws_total_size_all + aws_total_size
        else:
            aws_total_size = 0.0
            aws_total_size_all = aws_total_size_all + aws_total_size
    return aws_total_size_all


def get_ali_oss_totle_size(ak, sk, region, bucketname):
    onehours = datetime.timedelta(hours=12)
    starttime = datetime.datetime.now() - onehours

    nowtime = datetime.datetime.now()

    client = AcsClient(ak, sk, region)

    request = DescribeMetricListRequest()
    request.set_accept_format('json')

    request.set_MetricName("MeteringStorageUtilization")
    request.set_Namespace("acs_oss")
    request.set_Period("43200")
    request.set_StartTime(starttime)
    request.set_EndTime(nowtime)
    request.set_Dimensions("{\"BucketName\":" + bucketname + "}")

    response = client.do_action_with_exception(request)

    data_dict = json.loads(response)
    total_size = json.loads(data_dict.get("Datapoints"))
    try:
        if len(total_size) > 0:
            ali_total_size_all = 0
            for i in total_size:
                ali_total_size = round(i.get('MeteringStorageUtilization') / 1024, 3)  # 单位kb
                ali_total_size_all = int(ali_total_size) + int(ali_total_size_all)
            return ali_total_size_all
        else:
            ali_total_size = 0
            return ali_total_size
    except IndexError:
        print "except %s,%s" % (region, bucketname)
        ali_total_size = 0
        return ali_total_size


def get_cmdb_token():
    username, password = get_access()
    auth_token = None
    url = '{}/auth'.format(host)
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


def get_cmdb_bucket_data():
    token = get_cmdb_token()
    params = {}

    url = "{}/s3/list_buckets".format(host)
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer %s" % token
    }
    response = requests.get(url, params=params, headers=headers)
    res = json.loads(response.text)
    return res


def get_codename():  # 调接口获取项目/部门/Item对应关系

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


def add_data_profile():
    profile = get_profile_load_json_dict()
    cmdb_data = get_cmdb_bucket_data()

    new_all_data = []
    profile_accountID = []

    for j in profile.get("aws"):
        profile_accountID.append(j.get("AccountID"))

    for j in profile.get("ali"):
        profile_accountID.append(j.get("AccountName"))

    grouplsit = json.dumps(profile_accountID, sort_keys=False, ensure_ascii=False, indent=4, separators=(',', ': '))

    for data in cmdb_data:
        cloud = data.get("cloud")
        if cloud == "aws":
            for i in profile.get(cloud):

                if data.get('account') in profile_accountID:
                    if data.get('account') == i.get('AccountID'):
                        data['Profile'] = i.get('Profile')
                        new_all_data.append(data)

                else:
                    pass
                    # print "accountID: %s no have configfile,place add." %(data.get('account'))
        else:
            for i in profile.get("ali"):
                if data.get('account') in profile_accountID:
                    if data.get('account') == i.get('AccountName'):
                        data['Profile'] = i.get('Profile')
                        new_all_data.append(data)
                else:
                    pass
                    # print "accountID: %s no have configfile,place add." % (data.get('account'))
    return new_all_data


def get_aws_akAndsk(profile):
    conf = configparser.ConfigParser()
    conf.read(awk_file, encoding="utf8")
    try:
        ak = conf.get(profile, 'aws_access_key_id')
        sk = conf.get(profile, 'aws_secret_access_key')
        return ak, sk
    except Exception as e:
        # print "%s not %s" %(awk_file,profile)
        ak = None
        sk = None
        return ak, sk


def get_ali_akAndsk(profile):
    aliconfig = open(ali_file, 'r')
    config_dict = json.load(aliconfig)
    ak = None
    sk = None
    for data in config_dict.get('profiles'):
        if profile == data.get('name'):
            ak = data.get('access_key_id')
            sk = data.get('access_key_secret')
    return ak, sk

def action_get_s3_size(q,aws_profile):
    p = Pool(5)
    res_l = {}
    for data in aws_profile:
        profile = data.get('Profile')
        region = data.get('region')
        bucketname = data.get('resourceId')
        cloud = data.get('cloud')
        if cloud == 'aws':
            ak, sk = get_aws_akAndsk(profile)
            if ak != None:
                if region:
                    #aws_totle_size = get_aws_s3_totle_size(ak, sk, region, bucketname)
                    #print cloud, bucketname, aws_totle_size
                    res = p.apply_async(get_aws_s3_totle_size, args=(ak, sk, region, bucketname,))
                    res_l[res]=data
                else:
                    print "%s,%s region is null." % (cloud, bucketname)
            else:
                print "%s,%s,%s ak is null." % (cloud, region, bucketname)
        else:
            print "This is aws. Other %s" % (cloud)
    for res in res_l.keys():
        aws_totle_size = res.get() 
        datas = res_l[res]
        datas["totle_size"] = aws_totle_size
        q.put(datas)


def action_get_oss_size(q,ali_profile):
    p = Pool(5)
    res_l = {}
    for data in ali_profile:
        profile = data.get('Profile')
        region = data.get('region')
        bucketname = data.get('resourceId')
        cloud = data.get('cloud')
        if cloud == 'aliyun':
            ak, sk = get_ali_akAndsk(profile)
            if ak != None:
                if region:
                    #ali_totle_size = get_ali_oss_totle_size(ak, sk, region, bucketname)
                    res = p.apply_async(get_ali_oss_totle_size, args=(ak, sk, region, bucketname,))
                    res_l[res]=data
                    #print cloud, bucketname, ali_totle_size
                else:
                    print "%s,%s region is null." % (cloud, bucketname)
            else:
                print "%s,%s ak is null." % (cloud, bucketname)
        else:
            print "This is ali. Other %s" % (cloud)
    for res in res_l.keys():
        ali_totle_size = res.get()
        datas = res_l[res]
        datas["totle_size"] =  ali_totle_size
        q.put(datas)

def get_codename_bucketname_size():
    codename_lsit = get_codename()
    
    aws_profile = add_data_profile()
    q = Manager().Queue()
    p_action_get_s3_size = Process(target=action_get_s3_size,args=(q,aws_profile))
    p_action_get_oss_size = Process(target=action_get_oss_size,args=(q,aws_profile))

    p_action_get_s3_size.start()
    p_action_get_oss_size.start()

    p_action_get_s3_size.join()
    p_action_get_oss_size.join()
    all_data = []
    for i in range(q.qsize()):
        all_datas = q.get(True)
        all_data.append(all_datas)
    codename_bucketname_dict = {}
    codename_bucketname_dict_sender = {}

    for codename in codename_lsit:
        codename_bucketname_list = []
        for data in all_data:
            if codename == data.get('codename'):
                totle_size = data.get('totle_size')  # kb
                codename_bucketname_list.append(totle_size)
        codename_bucketname_dict[codename] = round(sum(codename_bucketname_list) / 1024 / 1024, 3)  # "s3oss_CodeName_"+
        codename_bucketname_dict_sender["s3osssize_CodeName_" + codename + "_ALL"] = round(sum(codename_bucketname_list) / 1024 / 1024, 3)
    codename_bucketname_dict_sender["s3osssize_CodeName_errortag_ALL"] = 0.0
    s3_codename_data_sender = json.dumps(codename_bucketname_dict_sender, sort_keys=False, ensure_ascii=False, indent=4,
                                         separators=(',', ': '))
    f = open(data_dir + 's3_codename_data_sender11.json', 'w')
    f.write(s3_codename_data_sender)
    return codename_bucketname_dict


def codename_load_json_dict():  ##读本地保存的项目-部门-codename关系的json文件
    load_json = open(data_dir + 'Project_Department_Codename.json', 'r')
    Project_Department_Codename = json.load(load_json)
    return Project_Department_Codename


def Project_Department_Codename():
    all_codename_num = get_codename_bucketname_size()

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
        a[i] = code_name_list

    for i in department_list:
        project_name_list = {}
        for j in range(len(date_list)):
            if date_list[j]['department_extra_info']["name"] == i:
                for x in a.keys():  # x是项目ID
                    if x == date_list[j]['project_extra_info']["name"]:
                        project_name_list[date_list[j]['project_extra_info']["name"]] = a[x]
        b[i] = project_name_list
    department_name_list = b
    all_servers_json = json.dumps(department_name_list, sort_keys=False, ensure_ascii=False, indent=4,
                                  separators=(',', ': '))
    # print all_servers_json
    f = open(data_dir + 'all_codename_count_data.json', 'w')
    f.write(all_servers_json)
    return department_name_list, project_list, department_list


def get_ProjectAndDepartment_s3_size():
    all_data, project_list, department_list = Project_Department_Codename()
    a_dict = {}
    for i in all_data.keys():
        for j in all_data[i].keys():
            a_list = []
            for x in all_data[i][j].keys():
                a_list.append(all_data[i][j][x])
            a_dict["s3osssize_[Project_" + j + "_ALL]"] = round(sum(a_list), 3)

    sendfile_s3_project_size = json.dumps(a_dict, sort_keys=False, ensure_ascii=False, indent=4,
                                          separators=(',', ': '))
    f = open(data_dir + 'zabbix_sendfile_s3_project_size.json', 'w')
    f.write(sendfile_s3_project_size)

    b_dict = {}
    for i in all_data.keys():
        b_list = []
        for j in all_data[i].keys():
            for x in all_data[i][j].keys():
                b_list.append(all_data[i][j][x])
        b_dict["s3osssize_[Department_" + i + "_ALL]"] = round(sum(b_list), 3)

    sendfile_s3_department_size = json.dumps(b_dict, sort_keys=False, ensure_ascii=False, indent=4,
                                             separators=(',', ': '))
    f = open(data_dir + 'zabbix_sendfile_s3_department_size.json', 'w')
    f.write(sendfile_s3_department_size)


def send_codename_size_data():
    time.sleep(1)
    cmd_zabix_sender_data = 'cat ' + data_dir + 's3_codename_data_sender.json | grep s3 | sed -e \'s/"//g\'' \
                            ' -e \'s/:/ /g\' -e \'s/,//\' -e \'s/^/"' + hostname + '"/\'' \
                            ' -e \'s/_/_[/\' -e \'s/ALL/&]/\' > /etc/zabbix/python_script/zabbix_sendfile_s3_codename_size'

    commands.getoutput(cmd_zabix_sender_data)
    time.sleep(1)
    zabbix_file = 'zabbix_sender -z ' + zabbix_server + ' -i /etc/zabbix/python_script/zabbix_sendfile_s3_codename_size > /dev/null 2>&1'
    commands.getoutput(zabbix_file)


def send_project_size_data():
    time.sleep(1)
    cmd_zabix_sender_data = 'cat ' + data_dir + 'zabbix_sendfile_s3_project_size.json | grep s3 | sed -e \'s/"//g\'' \
                            ' -e \'s/:/ /g\' -e \'s/,//\' -e \'s/^/"' + hostname + '"/\' > /etc/zabbix/python_script/zabbix_sendfile_s3_project_size'
    commands.getoutput(cmd_zabix_sender_data)
    time.sleep(1)
    zabbix_file = 'zabbix_sender -z ' + zabbix_server + ' -i /etc/zabbix/python_script/zabbix_sendfile_s3_project_size > /dev/null 2>&1'
    commands.getoutput(zabbix_file)


def send_department_size_data():
    cmd_zabix_sender_data = 'cat ' + data_dir + 'zabbix_sendfile_s3_department_size.json | grep s3 | sed -e \'s/"//g\'' \
                            ' -e \'s/:/ /g\' -e \'s/,//\' -e \'s/^/"' + hostname + '"/\' > /etc/zabbix/python_script/zabbix_sendfile_s3_department_size'
    commands.getoutput(cmd_zabix_sender_data)
    time.sleep(1)
    zabbix_file = 'zabbix_sender -z ' + zabbix_server + ' -i /etc/zabbix/python_script/zabbix_sendfile_s3_department_size > /dev/null 2>&1'
    commands.getoutput(zabbix_file)


def main():
    get_ProjectAndDepartment_s3_size()
    send_codename_size_data()
    send_project_size_data()
    send_department_size_data()


if __name__ == '__main__':
    main()