#!/bin/bash
# Call this script with the topography type you wish to use.
# eg. sh test.sh ring
# 
# If you want to use the fat_tree topo, include:
# The number of bottom switches
# The number of hosts/per bottom switch
# The number of middle switches 
# eg. sh test.sh fat_tree 4 2 2


echo "first parameter is $1"
/home/admin/flow_validator/src/mininet/launch_topo.sh $1 &

docker run -ti -p 80:80 -p 8080:8080 -p 6633:6633 -p 6363:6363 ODL /bin/bash
export JAVA_HOME=/usr/lib/jvm/java-7-openjdk-amd64/jre
/distribution-karaf-0.2.0-Helium/bin/karaf





