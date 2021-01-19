#!/bin/bash
# 2021-01-18.
# 配置到zabbix discovery，用于获取Project列表。



DRUID=( $(cat /etc/zabbix/json_data/druid.json | jq '.''[]' | sed 's/"//g') )

echo "{\"data\":["
for((i=0;i<${#DRUID[@]};i++))
do 
   if (($((i+1)) < ${#DRUID[@]}));then
     echo "{\"{#DRUID}\":\"${DRUID[$i]}\"},"
   else
     echo "{\"{#DRUID}\":\"${DRUID[$i]}\"}"
   fi
done
echo "]}"
