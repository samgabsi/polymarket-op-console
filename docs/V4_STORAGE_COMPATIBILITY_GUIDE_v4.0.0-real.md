# V4 Storage Compatibility Guide — v4.0.0-real

## Local Runtime Namespaces

Known runtime namespaces include v2 audit records, v3 workflow runs, datasets, freshness records, tasks, guided workspace records, cockpit records, and v4 platform diagnostics/plugin manifests.

## Release ZIP Policy

Release ZIPs must exclude runtime records, runtime exports, logs, screenshots, local credentials, `.env` with real values, database files with user data, cache folders, venvs, node modules, and operating system junk files.

## Compatibility Notes

- v3.5 dataset manifests are local runtime records.
- v3.6 freshness records are local runtime records.
- v3.7 task records are local runtime records.
- v3.8 workspace records are local runtime records.
- v3.9 cockpit records are local runtime records.
- v4.0 platform diagnostics and plugin manifests are local runtime records.

## Migration Policy

v4.0 provides documentation and summaries only. It does not automatically delete user data, destructively migrate runtime stores, mutate live trading state, approve orders, submit orders, or cancel orders.
