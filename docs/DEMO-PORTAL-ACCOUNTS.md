# Demo portal and service accounts

The Nigeria demonstration deployment has separate test identities. Accounts are environment-specific and are not created automatically by this repository or release kit. Credentials are held separately; never commit passwords here. These accounts include privileged service administration and are for the synthetic-data demonstration environment.

## Staff Portal and Staff Access Administration

- Staff Portal: `ooru.demo.staffportal` at https://staff-portal.nigeriag2p.com — live sign-in and landing screen verified on 28 October 2026.
- Staff Access Administration: `ooru.demo.keycloak` at https://iam-staff-ui.nigeriag2p.com — live sign-in and Applications screen verified on 28 October 2026. The account has the IAM staff UI application administrator role and staff-realm administration. This is distinct from the Keycloak master administration console, which is not publicly available.
- The separate `ooru.demo.admin` persona account has no configuration-admin workspace assigned.

The deployment's staff realm now contains the `iam-staff-ui` permission client and `IAM_ADMIN` client role, mapped to the staff-administration test account. The IAM API maps this role to the existing IAM application's permissions. This deployment-specific identity change is not applied by the kit installer and must be reproduced and validated independently in any other environment.

## Verified access

On 28 October 2026, public Odoo authentication succeeded for PBMS, Odoo Social Registry and beneficiary programme administration. Browser sign-in reached the service screens for Modern Social Registry, Staff Portal, approval workflows, master data, partner management, consent management, ODK Central, Superset and beneficiary self-service. Registration officer, verification officer, supervisor and citizen workspace identities were separately verified. These are sign-in and landing-screen checks; they do not certify every operation or authorization boundary.

The Kafka identity authenticates to Keycloak but its public console URL returns 404. The MinIO identity authenticates to its administrative API locally but its public console URL returns 404. The Keycloak master administration console is not publicly available. The ordinary registration staff login now sends persona-only accounts to their workspace; the reviewer page remains restricted. The deployment-specific patch is in `integration/nigeria-lab`. Availability depends on the lab and network.

The three Odoo service accounts inherit their existing lab administrator groups; MinIO has the consoleAdmin policy. Service roles are not automatically native OpenG2P permissions in other environments. Use synthetic records only, and establish appropriate role scope and separate credentials before any production use.
