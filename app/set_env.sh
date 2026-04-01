#!/bin/bash
#sudo su <<EOF
# cp ~/.aws/credentials /home/mvs/.aws/credentials
# chown -R mvs:mvs /home/mvs/.aws
# EOF
# env >> /etc/bash.bashrc
source /app/scanners/commons/get_instance_id.sh
set -a
INSTANCE=$(get_instance_id)
PATH=$PATH:/sbin
set +a
