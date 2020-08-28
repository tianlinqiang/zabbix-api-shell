#!/bin/bash
# 2020-06-18.
# 配置到zabbix discovery，用于获取Project列表。



VOLUMESIZE=( $(cat /etc/zabbix/discovery_data/get_groups_list_json.json | jq '.''[]' | sed 's/"//g') )

echo "{\"data\":["
for((i=0;i<${#VOLUMESIZE[@]};i++))
do 
   if (($((i+1)) < ${#VOLUMESIZE[@]}));then
      echo "{\"{#VOLUMESIZE}\":\"${VOLUMESIZE[$i]}\"},"
   else
      echo "{\"{#VOLUMESIZE}\":\"${VOLUMESIZE[$i]}\"}"
   fi
done
echo "]}"
