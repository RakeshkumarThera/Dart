#!/bin/bash

hostname=$1
CLUSTER_NAME=`echo $2 | sed 's/-/_/g'`
password=$3

sshpass -p $password ssh -o StrictHostKeyChecking=no -l root $hostname "/etc/init.d/ambari-server start"

sleep 180

curl -u admin:admin -i -H 'X-Requested-By: ambari' -X PUT -d  '{"RequestInfo":{"context":"_PARSE_.START.ALL_SERVICES","operation_level":{"level":"CLUSTER","cluster_name":"Sandbox"}},"Body":{"ServiceInfo":{"state":"STARTED"}}}' http://$hostname:8080/api/v1/clusters/$CLUSTER_NAME/services

#curl -u admin:admin -i -H 'X-Requested-By: ambari' -X PUT -d '{"RequestInfo": {"context" :"Start HDFS via REST"}, "Body": {"ServiceInfo": {"state": "STARTED"}}}' http://$hostname:8080/api/v1/clusters/$CLUSTER_NAME/services/HDFS
 
#sleep 3

#curl -u admin:admin -i -H 'X-Requested-By: ambari' -X PUT -d '{"RequestInfo": {"context" :"Start YARN via REST"}, "Body": {"ServiceInfo": {"state": "STARTED"}}}' http://$hostname:8080/api/v1/clusters/$CLUSTER_NAME/services/YARN
 
#sleep 3

#curl -u admin:admin -i -H 'X-Requested-By: ambari' -X PUT -d '{"RequestInfo": {"context" :"Start MAPREDUCE2 via REST"}, "Body": {"ServiceInfo": {"state": "STARTED"}}}' http://$hostname:8080/api/v1/clusters/$CLUSTER_NAME/services/MAPREDUCE2
 
#sleep 3

#curl -u admin:admin -i -H 'X-Requested-By: ambari' -X PUT -d '{"RequestInfo": {"context" :"Start HIVE via REST"}, "Body": {"ServiceInfo": {"state": "STARTED"}}}' http://$hostname:8080/api/v1/clusters/$CLUSTER_NAME/services/HIVE
 
#sleep 3

#curl -u admin:admin -i -H 'X-Requested-By: ambari' -X PUT -d '{"RequestInfo": {"context" :"Start TEZ via REST"}, "Body": {"ServiceInfo": {"state": "STARTED"}}}' http://$hostname:8080/api/v1/clusters/$CLUSTER_NAME/services/TEZ

#sleep 3

#curl -u admin:admin -i -H 'X-Requested-By: ambari' -X PUT -d '{"RequestInfo": {"context" :"Start FLUME via REST"}, "Body": {"ServiceInfo": {"state": "STARTED"}}}' http://$hostname:8080/api/v1/clusters/$CLUSTER_NAME/services/FLUME
 
#sleep 3

#curl -u admin:admin -i -H 'X-Requested-By: ambari' -X PUT -d '{"RequestInfo": {"context" :"Start HBASE via REST"}, "Body": {"ServiceInfo": {"state": "STARTED"}}}' http://$hostname:8080/api/v1/clusters/$CLUSTER_NAME/services/HBASE
 
#sleep 3

#curl -u admin:admin -i -H 'X-Requested-By: ambari' -X PUT -d '{"RequestInfo": {"context" :"Start AMBARI_METRICS via REST"}, "Body": {"ServiceInfo": {"state": "STARTED"}}}' http://$hostname:8080/api/v1/clusters/$CLUSTER_NAME/services/AMBARI_METRICS
 
#sleep 3

#curl -u admin:admin -i -H 'X-Requested-By: ambari' -X PUT -d '{"RequestInfo": {"context" :"Start ZOOKEEPER via REST"}, "Body": {"ServiceInfo": {"state": "STARTED"}}}' http://$hostname:8080/api/v1/clusters/$CLUSTER_NAME/services/ZOOKEEPER
 
#sleep 3

#curl -u admin:admin -i -H 'X-Requested-By: ambari' -X PUT -d '{"RequestInfo": {"context" :"Start HCATALOG via REST"}, "Body": {"ServiceInfo": {"state": "STARTED"}}}' http://$hostname:8080/api/v1/clusters/$CLUSTER_NAME/services/HCATALOG
 
#curl -u admin:admin -i -H 'X-Requested-By: ambari' -X PUT -d '{"RequestInfo": {"context" :"Start WEBHCAT via REST"}, "Body": {"ServiceInfo": {"state": "STARTED"}}}' http://$hostname:8080/api/v1/clusters/$CLUSTER_NAME/services/WEBHCAT
 
#curl -u admin:admin -i -H 'X-Requested-By: ambari' -X PUT -d '{"RequestInfo": {"context" :"Start NAGIOS via REST"}, "Body": {"ServiceInfo": {"state": "STARTED"}}}' http://$hostname:8080/api/v1/clusters/$CLUSTER_NAME/services/NAGIOS
 
#curl -u admin:admin -i -H 'X-Requested-By: ambari' -X PUT -d '{"RequestInfo": {"context" :"Start GANGLIA via REST"}, "Body": {"ServiceInfo": {"state": "STARTED"}}}' http://$hostname:8080/api/v1/clusters/$CLUSTER_NAME/services/GANGLIA
