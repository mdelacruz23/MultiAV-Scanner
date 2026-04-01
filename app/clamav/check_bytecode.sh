#!/bin/bash
# This script verifies that the clamav bytecode can be retrieved and 
# is upto date 
# 
SECONDSPERDAY=86400
TZ=UTC
BYTECODE_CVD=/var/lib/clamav/bytecode.cvd
if [ ! -f $BYTECODE_CVD ]
then
    echo "waiting for bytecode signatures..."
    exit 1
fi
CURRENT_VER_NFO=`sigtool --info=$BYTECODE_CVD`
CURRENT_VER=$(echo $CURRENT_VER_NFO | awk -F':' '{print $5}'| awk '{print $1}')
CURRENT_VER_TIME=$(echo $CURRENT_VER_NFO | awk -F':' '{print $3":"$4}')
CURRENT_VER_TIME=${CURRENT_VER_TIME%Version*}
CURRENT_VER_SEC_TIME=$(date -d"$CURRENT_VER_TIME" +%s)
LATEST_VER_INFO=`dig +noall +answer current.cvd.clamav.net TXT`
LATEST_VER=${LATEST_VER_INFO##*:}
LATEST_VER=${LATEST_VER::-1}
LATEST_VER_TIME=`echo $LATEST_VER_INFO | cut -d':' -f4`
let DIFF=($LATEST_VER_TIME - $CURRENT_VER_SEC_TIME)/$SECONDSPERDAY
# echo "CURRENT_VER_TIME: $CURRENT_VER_TIME CURRENT_VER_SEC_TIME: $CURRENT_VER_SEC_TIME CURRENT_VER: $CURRENT_VER LATEST_VER_TIME: $LATEST_VER_TIME LATEST_VER: $LATEST_VERDIFF:$DIFF days"

if [[ "$LATEST_VER" -gt "$CURRENT_VER" ]] && [[ "$DIFF" -gt 2 ]]
then
    echo "ALERT: clamav bytecode latest: $LATEST_VER  -- > using: $CURRENT_VER not synced for $DIFF days"
    exit 1
else
   echo "clamav bytecode upto date latest: $LATEST_VER --> current: $CURRENT_VER"
   exit 0
fi
