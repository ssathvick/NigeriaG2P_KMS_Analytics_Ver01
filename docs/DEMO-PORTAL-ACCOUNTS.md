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
