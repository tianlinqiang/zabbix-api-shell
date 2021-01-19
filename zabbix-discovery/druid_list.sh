#!/bin/bash
# Author: TLQ


# Set Variables
#http://10.102.133.191:8888/druid/indexer/v1/supervisor/
#http://10.102.133.191:8888/druid/indexer/v1/supervisor/ymds_cps_datasource/status

HOST="10.102.133.191"
PORT="8888"

URL1="http://${HOST}:${PORT}/druid/indexer/v1/supervisor/"
URL2="http://${HOST}:${PORT}/druid/indexer/v1/supervisor/$1/status"

zabbix_1(){
  data1=`curl --connect-timeout 5 ${URL1} >/dev/null 2>&1`
  a=`echo ${data1} | grep "$1"`
  if [ ! $? -eq 0 ];then
  echo "-1"
  else
  echo "0"
 fi

} 

aggregateLag(){
 data2=$(curl -s --connect-timeout 5 ${URL2})
 aggregateLag=`echo ${data2} | jq ."payload"."aggregateLag"` #数字，大于10万告警
 echo ${aggregateLag}

}

healthy(){
 data2=$(curl -s --connect-timeout 5 ${URL2})
 healthy=`echo ${data2} | jq ."payload"."healthy"`      #true
 echo ${healthy}
}

state(){
 data2=$(curl -s --connect-timeout 5 ${URL2})
 state=`echo ${data2} | jq ."payload"."state"`    #RUNNING
 echo ${state}

}



zabbix_1
