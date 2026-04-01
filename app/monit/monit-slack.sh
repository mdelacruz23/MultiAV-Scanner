#!/bin/bash

WEBHOOK_URL="insert webhook here"
HOSTNAME=$(hostname)
TIME=$(date -u +"%Y-%m-%d %H:%M:%S UTC")

MESSAGE="🚨 *Monit Alert*: \`clamav-daemon\` failed on *${HOSTNAME}* at *${TIME}*.
Action taken: Removed \`/var/log/clamav/clamav.log\` and restarted the service."

curl -X POST -H 'Content-type: application/json' --data "{\"text\":\"${MESSAGE}\"}" "$WEBHOOK_URL"
