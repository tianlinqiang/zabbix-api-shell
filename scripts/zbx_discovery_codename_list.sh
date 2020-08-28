#!/bin/bash
# 2020-06-18.
# 配置到zabbix discovery，用于获取codename列表。



CODENAME=( $(cat /etc/zabbix/discovery_data/discovery_ecs_codename.json | jq '.''[]' | sed 's/"//g') )

echo "{\"data\":["
for((i=0;i<${#CODENAME[@]};i++))
do 
   if (($((i+1)) < ${#CODENAME[@]}));then
      echo "{\"{#CODENAME}\":\"${CODENAME[$i]}\"},"
   else
      echo "{\"{#CODENAME}\":\"${CODENAME[$i]}\"}"
   fi
done
echo "]}"
