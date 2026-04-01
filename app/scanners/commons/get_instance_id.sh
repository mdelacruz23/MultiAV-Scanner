#!/bin/bash
# set -x
# Retrieve instance id
is_ec2_instance() {
if $(curl -s -m 5 http://169.254.169.254/latest/dynamic/instance-identity/document | grep -q availabilityZone) ; then
    echo "yes"
  else
    echo "no"
  fi
}

get_instance_id() {
    if [ "$(is_ec2_instance)" = "yes" ]
    then
        instance_id="$(curl -s http://169.254.169.254/latest/meta-data/instance-id)"
    else
        instance_id="00001"
    fi
    echo "$instance_id"
}

