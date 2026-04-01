#!/usr/bin/env bash

PIDFILE="/opt/sophos-spl/plugins/av/chroot/var/threat_detector.pid"
MIN_UPTIME_MINUTES=5

if [ ! -r "$PIDFILE" ]; then
  echo "PID file not readable: $PIDFILE"
  exit 2
fi

PID="$(tr -d '[:space:]' < "$PIDFILE")"

if ! ps -p "$PID" >/dev/null 2>&1; then
  echo "Sophos threat detector PID $PID not running/visible"
  exit 2
fi

UPTIME_SECONDS=$(ps -o etimes= -p "$PID" | tr -d ' ')

if [ -z "$UPTIME_SECONDS" ]; then
  echo "Failed to read uptime"
  exit 2
fi

UPTIME_HOURS=$(( UPTIME_SECONDS / 3600 ))
UPTIME_MINUTES=$(( (UPTIME_SECONDS % 3600) / 60 ))

echo "Sophos uptime: ${UPTIME_HOURS}h ${UPTIME_MINUTES}m"

TOTAL_MINUTES=$(( UPTIME_SECONDS / 60 ))

if [ "$TOTAL_MINUTES" -lt "$MIN_UPTIME_MINUTES" ]; then
  echo "Sophos restarted recently (< ${MIN_UPTIME_MINUTES} minutes)"
  exit 1
fi

exit 0
