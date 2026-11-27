#!/bin/sh
# Generate literal allowlist entries only from validated configuration, never request headers.
set -eu
: "${DJANGO_ALLOWED_HOSTS:?Explicit public hosts required}"
tmp="$(mktemp /etc/nginx/sirago-hosts.XXXXXX)"
trap 'rm -f "$tmp"' EXIT HUP INT TERM
printf '%s\n' "$DJANGO_ALLOWED_HOSTS" | awk '
BEGIN { FS=","; count=0 }
NR != 1 { exit 1 }
{
    for (i=1; i<=NF; i++) {
        h=$i
        gsub(/^[ \t]+|[ \t]+$/, "", h)
        h=tolower(h)
        if (length(h)>253 || h !~ /^[a-z0-9-]+(\.[a-z0-9-]+)+$/) exit 1
        n=split(h, labels, ".")
        if (length(labels[n])<2 || length(labels[n])>63 || labels[n] !~ /^[a-z]+$/) exit 1
        for (j=1; j<=n; j++) {
            if (length(labels[j])>63 || labels[j] !~ /^[a-z0-9]([a-z0-9-]*[a-z0-9])?$/) exit 1
        }
        if (!seen[h]++) { print h; count++ }
    }
}
END { if (!count) exit 1 }
' > "$tmp" || { echo "Invalid gateway host allowlist" >&2; exit 1; }
vhosts="$(mktemp /etc/nginx/sirago-vhosts.XXXXXX)"
health="$(mktemp /etc/nginx/sirago-health.XXXXXX)"
trap 'rm -f "$tmp" "$vhosts" "$health"' EXIT HUP INT TERM
while IFS= read -r configured_domain; do
    printf 'server {\n    listen 8080;\n    server_name %s;\n    include /etc/nginx/sirago-site.conf;\n}\n' "$configured_domain"
done < "$tmp" > "$vhosts"
head -n 1 "$tmp" > "$health"
chmod 0644 "$vhosts" "$health"
mv "$vhosts" /etc/nginx/sirago-vhosts.conf
mv "$health" /etc/nginx/sirago-health-host
rm -f "$tmp"
nginx -t
trap - EXIT HUP INT TERM

# No command during the build-time configuration check; exec nginx at runtime.
if [ "$#" -gt 0 ]; then exec "$@"; fi
