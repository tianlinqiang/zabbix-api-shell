#!/bin/bash


HOST='https://cmdb.yeahmobi.com/api/v1'
#INSTANCE=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
INSTANCE="i-t4n3mqnlsy7zdbntmhv3"
HOSTNAME=`hostname`
TOKEN=`curl -i -k -s -X POST ${HOST}/auth \
       -H "Content-Type:application/json;charset=UTF-8" \
       -d '{"username":"username","password":"password","type":"normal"}'|sed 's/,/\n/g' \
       | grep -w "auth_token"|sed 's/:/ /'|awk '{print $2}'|sed -e 's/"//g' -e 's/}//g' `
           
           
           
CODENAME=`curl -i -k -s -X GET ${HOST}/application/get_codename -H "Content-Type:application/json" \
         -H "Authorization:Bearer ${TOKEN}"|grep "\["| tr "," " "| sed -e 's/\[//g' -e 's/\]//g'`



METADATA=`curl -i -k -s -X POST ${HOST}/server/get_codename_by_instance_id \
         -H "Content-Type:application/json" -H "Authorization:Bearer ${TOKEN}" \
         -d '{"instanceId":"'${INSTANCE}'"}'| grep data| awk -F ',' '{print $1}' \
         |awk -F ':' '{print $2}'| sed 's/"//g'`

if [ -z ${METADATA} ];then
 METADATA="notag"
fi

status=`for i in $CODENAME;do echo $i;done | grep -w $METADATA|wc -l`

if [ ${status} -eq 0 ];then
 METADATA="errortag"
fi

#sed -i '/Hostname=${HOSTNAME}/a\HostMetadata='"${METADATA}"'' /etc/zabbix/zabbix_agentd.conf
#echo "HostMetadata=${METADATA}" >> /etc/zabbix/zabbix_agentd.conf

#OS is centos or ubuntu 
if [ -e /etc/redhat-release ];then
 PLATFORM=$(cat /etc/redhat-release|awk -F' ' {'print $1'}|head -1)
# Test if OS is CentOS7
 CentOS7_Ver=`grep "CentOS Linux release 7" /etc/redhat-release | wc -l`
else
 PLATFORM=$(cat /etc/issue|awk -F' ' {'print $1'}|head -1)
 CentOS7_Ver=0
fi

#restrat zabbix-agent
if [ "${PLATFORM}" == "CentOS" ];then
 if [ ${CentOS7_Ver} -eq 1 ];then
  systemctl restart zabbix-agent.service 
 else 
  service zabbix-agent restart
 fi
elif [ "${PLATFORM}" == "Ubuntu" ];then
 /etc/init.d/zabbix-agent restart  
else
 /etc/init.d/zabbix-agent restart  
fi


if [ $? -eq 0 ];then
echo "${INSTANCE}"  >> at.log
mgess=`cat /etc/zabbix/zabbix_agentd.conf | grep -w "HostMetadata=${METADATA}"` >> at.log
echo $mgess >> at.log
else
echo "zabbix-agent restart fail"
fi
