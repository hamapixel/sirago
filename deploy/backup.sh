#!/bin/sh
set -eu
umask 077
mkdir -p /backups
# First dump after startup, then every 24 hours. A failed dump is retried.
while true; do
  stamp=$(date -u +%Y%m%dT%H%M%SZ)
  tmp="/backups/sirago-$stamp.dump.partial"
  dest="/backups/sirago-$stamp.dump"
  if pg_dump --format=custom --no-owner --no-privileges --file="$tmp" && pg_restore --list "$tmp" >/dev/null; then
    mv "$tmp" "$dest"
    find /backups -type f -name 'sirago-*.dump' -mtime +14 -exec rm -f {} +
    echo "Backup OK: $stamp"
    sleep 86400
  else
    rm -f "$tmp"
    echo "Backup failed: $stamp" >&2
    sleep 300
  fi
done
