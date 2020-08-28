#!/bin/bash
# 2020-06-18.
# 配置到zabbix discovery，用于获取Project列表。



PROJECTNAME=( $(cat /etc/zabbix/discovery_data/discover_project_list_json.json | jq '.''[]' | sed 's/"//g') )

echo "{\"data\":["
for((i=0;i<${#PROJECTNAME[@]};i++))
do 
   if (($((i+1)) < ${#PROJECTNAME[@]}));then
      echo "{\"{#PROJECTNAME}\":\"${PROJECTNAME[$i]}\"},"
   else
      echo "{\"{#PROJECTNAME}\":\"${PROJECTNAME[$i]}\"}"
   fi
done
echo "]}"
