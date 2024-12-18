# Changelog

## Version 1.1
- Fixed container metrics not showing up in prometheus
- Fixed etc process from running on worker nodes
- Fixed etcd snapshots failing for double quotes in cron
- Fixed uninstall script not updating permissions correctly
- Fixed timeservers not being synced
- Fixed slow network performance within pods on bare-metal when using bynet
- Added customization for nginx ingress
- Added nginx ingress restriction to only listen to https port
- Added option to specify FQDN and TLS certificate
- Added password based authentication to Kibana/Grafana page
- Added variable for docker internal registry mount
- Added ingress exposure on port 443
- Ingress is now TLS-enabled
