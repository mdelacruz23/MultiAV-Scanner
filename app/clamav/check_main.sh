#!/bin/bash
# There is not defined the frequency of main dats updates is quite random and can span days
# Therefore the olny way to determine if the main dats are up to date is to quiery clam server
# But freshclam does that for us 

SECONDSPERDAY=86400
TZ=UTC
MAIN_CLD=/var/lib/clamav/main.cld
MAIN_CVD=/var/lib/clamav/main.cvd

if [ ! -f $MAIN_CLD ] && [ ! -f $MAIN_CVD ]
then
    echo "waiting for clamav main signatures...."
    exit 1
elif [ -f $MAIN_CLD ]
then
    MAIN_DATS=${MAIN_CLD}
else
    MAIN_DATS=${MAIN_CVD}
fi
MOD_TIME=`date -d "@$(stat -c '%Y' $MAIN_DATS)" '+%c'`
SIZE=`du -h $MAIN_DATS | cut -f1`
echo "$(basename ${MAIN_DATS}) signatures last updated: ${MOD_TIME} size: ${SIZE}"
exit 0

# We don't want to hit clam server that very often 
# Use a small time range so that monit can hit it
# CURRENT_TIME=$(date +%H:%M)

# if [[ "$CURRENT_TIME" > "23:00" ]] && [[ "$CURRENT_TIME" < "23:05" ]]
#     then
#         if [ -f $MAIN_CLD ]
#         then
#             CURRENT_VER_INFO=`sigtool --info=$MAIN_CLD`
#         elif [ -f $MAIN_CVD ]
#         then 
#             CURRENT_VER_INFO=`sigtool --info=$MAIN_CVD`
#         fi
#         CURRENT_VER=$(echo $CURRENT_VER_INFO | awk -F':' '{print $5}'| awk '{print $1}')
#         
#         CURRENT_VER_TIME=$(echo $CURRENT_VER_INFO | awk -F':' '{print $3":"$4}')
#         CURRENT_VER_TIME=${CURRENT_VER_TIME%Version*}
#         
#         CURRENT_VER_SEC_TIME=$(date -d"$CURRENT_VER_TIME" +%s)
#         LATEST_VER_INFO=`dig +noall +answer current.cvd.clamav.net TXT`
#         LATEST_VER=`echo $LATEST_VER_INFO | cut -d':' -f2`
#         LATEST_VER_TIME=`echo $LATEST_VER_INFO | cut -d':' -f4`
#         let DIFF=($LATEST_VER_TIME - $CURRENT_VER_SEC_TIME)/$SECONDSPERDAY
#         # echo "CURRENT_VER_TIME: $CURRENT_VER_TIME CURRENT_VER_SEC_TIME: $CURRENT_VER_SEC_TIME CURRENT_VER: $CURRENT_VER LATEST_VER_TIME: $LATEST_VER_TIME LATEST_VER: $LATEST_VER DIFF:$DIFF days"
#         
#         if [[ "$LATEST_VER" -gt "$CURRENT_VER" ]] && [[ "$DIFF" -gt 2 ]]
#         then
#             echo "ALERT: clamav main.cvd latest: $LATEST_VER  -- > using: $CURRENT_VER not synced for $DIFF days"
#             exit 1
#         else
#            echo "latest: clamav main.cvd $LATEST_VER --> current: $CURRENT_VER"
#            exit 0
#         fi
#     else
#         exit 0
# fi
