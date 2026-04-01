#!/bin/bash
set -x
# This is the first command executed within docker image
# to be able to switch the set of monitoring resources 
# based on
# 1 - either local or remote downloads of virus definitions
# 2 - whether FS scanners are enabled or disabled
# 3 - whether engines are updated dynamically
mkdir /run/clamav
mkdir /run/mvs
source /app/scanners/commons/get_instance_id.sh
EC2_INSTANCE=$(get_instance_id)

# chown -R mvs:mvs /var/log/
LOGGER=/var/log/main_switch.log
#echo -e "$(date) Instance: $EC2_INSTANCE -- MVS Initialization - Configuration Info Begin -- \n" >> $LOGGER 2>&1
if [[ -z "${LOCAL_DEFS}" ]] 
then
#   echo -e "$(date) Instance: $EC2_INSTANCE -- Remote definitions -- \n" >> $LOGGER 2>&1
    cp /app/monit/remote-monitrc /etc/monit/monitrc
elif [ "$LOCAL_DEFS" = true ]
then

#    echo -e "$(date) Instance: $EC2_INSTANCE --  Local definitions -- \n" >> $LOGGER 2>&1
    cp  /app/monit/local-monitrc /etc/monit/monitrc
else
#    echo -e "$(date) Instance: $EC2_INSTANCE -- Remote definitions -- \n" >> $LOGGER 2>&1
    cp /app/monit/remote-monitrc /etc/monit/monitrc
fi
if [ "${FS_SCANNERS}" = false ]  
then
#    echo -e "$(date) Instance: $EC2_INSTANCE -- FS Scanners disabled -- \n" >> $LOGGER 2>&1
#    echo -e "$(date) Instance: $EC2_INSTANCE -- S3 Scanners active -- \n" >> $LOGGER 2>&1
    sed -i '/# BEGIN FS/,/# END FS/ s/^#*/#/' /etc/monit/monitrc
else
#    echo -e "$(date) Instance: $EC2_INSTANCE -- FS Scanners active -- \n" >> $LOGGER 2>&1
#    echo -e "$(date) Instance: $EC2_INSTANCE -- S3 Scanners disabled -- \n" >> $LOGGER 2>&1
    sed -i '/# BEGIN S3/,/# END S3/ s/^#*/#/' /etc/monit/monitrc
fi
if [ "${ENGINE_UPDATES}" = false ]
then
#    echo -e "$(date) Instance: $EC2_INSTANCE -- Dynamic Engines Updates disabled -- \n" >> $LOGGER 2>&1
#    echo -e "$(date) Instance: $EC2_INSTANCE -- Virus Engines installed at build time -- \n" >> $LOGGER 2>&1
    sed -i '/# BEGIN ENG_UP/,/# END ENG_UP/ s/^#*/#/' /etc/monit/monitrc
else
 #   echo -e "$(date) Instance: $EC2_INSTANCE -- Dynamic Engines Updates active -- \n" >> $LOGGER 2>&1
     echo "Done"
fi
#echo -e "$(date) Instance: $EC2_INSTANCE -- MVS Initialization  - Configuration Info End -- \n" >> $LOGGER 2>&1
