# Demo portal accounts and role access

The 28 October 2026 local Nigeria demo deployment has separate Keycloak identities for registration officer, verification officer, programme supervisor, citizen and a reserved administrator account. The accounts are environment-specific and are not automatically installed by this repository or the release kit. Passwords and credentials are distributed separately and must not be committed here.

| Demo identity | Identity realm | Workspace access verified |
| --- | --- | --- |
| ooru.demo.registration | staff | registration officer |
| ooru.demo.verification | staff | verification officer |
| ooru.demo.supervisor | staff | programme supervisor |
| ooru.demo.citizen | beneficiary | citizen |
| ooru.demo.admin | staff | no administrator permissions assigned; configuration role and scope require confirmation |

For the local deployment, staff can initiate sign-in using `https://nigeriag2p.com/registration/login?mode=staff&workspace=1` and the citizen can use `https://nigeriag2p.com/registration/login?mode=beneficiary&workspace=1`. Availability depends on the lab and network. The ordinary staff login currently redirects to a reviewer-only page and may return 403 for persona-only users; use the workspace sign-in link above. The administrator account authenticates but has no assigned workspace or configuration rights.

These identities and roles apply to the demonstration registration workspace, not automatically to native OpenG2P applications or this independent experience kit. Existing lab workspace data is synthetic. Before use in a client environment, agree on the identity provider, permissions, data scope, account provisioning and verification. Do not use a shared demo password for production.

## Separate service accounts

The local demo deployment additionally has distinct identities for PBMS, Odoo Social Registry, beneficiary programme administration, Modern Social Registry, staff portal, approval workflows, master data, partner management, consent management, ODK, Superset, Kafka, Keycloak staff-realm administration and MinIO. The three Odoo accounts inherited their respective existing lab administrator groups and authenticated via Odoo XML-RPC; the MinIO local account has the consoleAdmin policy and its administrative API authentication was verified. These accounts are privileged demo accounts, not production role definitions.

The Modern Registry, approvals, master data, partner, consent, analytics and Kafka identities received their existing service-specific Keycloak client role mappings. The ODK identity has an ODK administrator record. Staff Portal and ODK SSO application access, all other SSO service logins, and the beneficiary native portal have not yet been individually verified. The Keycloak account has staff-realm administration only, not master-realm administration. The original configuration-admin persona remains unassigned. Credentials and the detailed account inventory are held separately; do not commit them here.
