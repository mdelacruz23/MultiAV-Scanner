#!/bin/bash
DAILY_CLD=/var/lib/clamav/daily.cld
DAILY_CVD=/var/lib/clamav/daily.cvd

if [ ! -f "$DAILY_CLD" ] && [ ! -f "$DAILY_CVD" ]
then
    echo "waiting for clamav daily signatures.... "
    exit 1
fi
if [ -f "$DAILY_CLD" ]
then 
    DAILY=${DAILY_CLD}
else [  -f "$DAILY_CVD" ] 
    DAILY=${DAILY_CVD}
fi
MOD_TIME=`date -d "@$(stat -c '%Y' $DAILY)" '+%c'`
SIZE=`du -h $DAILY | cut -f1`
if [[ $(find $DAILY -mtime +3 -print) ]]
then
    echo "WARNING! $(basename $DAILY) signatures last updated: ${MOD_TIME} size: ${SIZE}"
    exit 1
else
    echo "$(basename $DAILY) signatures last updated: ${MOD_TIME} size: ${SIZE}"
    exit 0
fi
