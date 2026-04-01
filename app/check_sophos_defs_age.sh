#!/usr/bin/env bash

MAX_AGE_SECONDS=$((24*3600))


NOW=$(date +%s)
#MTIME=$(stat -c %Y "$FILE" 2>/dev/null)

LATEST=$(ls -t /opt/sophos-spl/plugins/av/chroot/susi/update_source/vdl/*.ide | head -1)
DEFS_AGE=$(stat -c %Y "$LATEST" 2>/dev/null)
AGE=$(( NOW - DEFS_AGE))

#echo "Sophos defs age: $((AGE/3600))h $((AGE%3600/60))m"

# Human-readable timestamp
LAST_UPDATE=$(date -d "@$DEFS_AGE" "+%Y-%m-%d %H:%M:%S %Z")

echo "Sophos definitions last updated: $LAST_UPDATE"

if [ "$AGE" -gt "$MAX_AGE_SECONDS" ]; then
  echo "Definitions are stale (>${MAX_AGE_SECONDS}s)"
  exit 1
fi

exit 0
