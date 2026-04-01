#!/bin/bash
# set -x
source /app/scanners/commons/get_instance_id.sh

### BEGIN INIT INFO
# Provides:          McAfee AntiVirus: Engine Updater
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: McAfee AntiVirus: Engine Updater
# Description:       The service to periodically update McAfee engine with new version
### END INIT INFO

DIR=/app/uvscan
DAEMON=/usr/local/bin/python 
DAEMON_NAME=uvscan_engine_updater
DAEMON_OPTS="$DIR/uvscan_engine_updater.py -d"
DAEMON_USER=mvs
LOG_DIR="/var/log/mcafee/"

PIDFILE=/var/run/mvs/$DAEMON_NAME.pid

INSTANCE=$(get_instance_id)
LOG_FILE="mcafee_engine-"
LOG_PATH="$LOG_DIR$LOG_FILE$INSTANCE"".log"

do_start () {
    echo "Starting system $DAEMON_NAME daemon"
    mkdir -p ${LOG_DIR}
    start-stop-daemon -v --start --background --pidfile $PIDFILE --make-pidfile --user $DAEMON_USER --chuid $DAEMON_USER --startas /bin/bash -- -c "exec $DAEMON -- $DAEMON_OPTS >> $LOG_PATH 2>&1"
    return $?
}
do_stop () {
    echo "Stopping system $DAEMON_NAME daemon"
    start-stop-daemon --stop --pidfile $PIDFILE --remove-pidfile --retry 10
    return $?
}

case "$1" in

    start|stop)
        do_${1}
        ;;

    restart|reload|force-reload)
        do_stop
        do_start
        ;;

    status)
        status_of_proc "$DAEMON_NAME" "$DAEMON" && exit 0 || exit $?
        ;;

    *)
        echo "Usage: /etc/init.d/$DAEMON_NAME {start|stop|restart|status}"
        exit 1
        ;;

esac
exit 0

