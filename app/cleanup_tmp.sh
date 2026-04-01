#!/bin/bash

# Directory to search
SEARCH_DIR="/tmp"

# Ensure the directory exists
if [[ ! -d "$SEARCH_DIR" ]]; then
    echo "Directory $SEARCH_DIR does not exist."
    exit 1
fi

# Find and delete directories starting with a number and older than 240 minutes
find "$SEARCH_DIR" -mindepth 1 -maxdepth 1 -type d -name '[0-9]*' -mmin +240 -print0 | while IFS= read -d $'\0' dir; do
    echo "Deleting directory: $dir"
    rm -rf "$dir"
done

echo "Cleanup complete."
chown mvs:mvs /var/log/monit.log*
