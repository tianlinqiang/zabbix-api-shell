#!/bin/bash
# 2020-06-18.
# 配置到zabbix discovery，用于获取DEPARTMENT列表。



DEPARTMENT=( $(cat /etc/zabbix/discovery_data/discover_deparment_list_json.json | jq '.''[]' | sed 's/"//g') )

echo "{\"data\":["
for((i=0;i<${#DEPARTMENT[@]};i++))
do 
   if (($((i+1)) < ${#DEPARTMENT[@]}));then
      echo "{\"{#DEPARTMENT}\":\"${DEPARTMENT[$i]}\"},"
   else
      echo "{\"{#DEPARTMENT}\":\"${DEPARTMENT[$i]}\"}"
   fi
done
echo "]}"
