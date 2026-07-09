# Security

Threat model covers credential attacks, token leakage, tenant data exposure, raw image exfiltration, unsafe model output, and admin misuse. Controls include password hashing, JWT expiry, refresh rotation schema, RBAC-ready routes, tenant-scoped queries, structured audit events, no raw image logging, CORS hardening, input validation, ORM access, and scan workflows.

## Incident response

Triage, contain tokens/storage keys, preserve audit logs, notify affected users, rotate secrets, rollback unsafe models, and publish post-incident corrective actions.
