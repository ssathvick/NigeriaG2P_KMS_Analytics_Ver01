# Client installation and integration

Sathvick Infotech Private Limited · Release 1.0.0-rc1 · 19 October 2026

## What installs

This is an independently deployed companion: a configurable React task/persona launcher, shared navigation/contextual-help assets, knowledge editing/review/publication/history, local accounts or OIDC SSO, and an authenticated analytics dashboard with a scheduled read-only collector. It does not install or replace OpenG2P, move beneficiary databases, grant OpenG2P permissions, or convert Figma screens into functioning native applications.

The client can run it on a separate approved VM beside OpenG2P, or in Kubernetes using the supplied single-instance chart. It uses its own persistent SQLite database. Do not scale it beyond one application instance or use a network filesystem for SQLite. High availability and PostgreSQL-backed KMS are not included in this release. The collector can read approved client PostgreSQL sources, but that does not change the KMS storage engine.

## Prerequisites

- Linux Docker Engine with Compose v2.24+, or Windows Docker Desktop running Linux containers with Compose v2.24+, or Docker Engine inside WSL2 Ubuntu-22.04.
- Permission to use Docker on the target host; an unused loopback port 18110 and persistent local storage.
- Internet access for the first image build, unless an image TAR was prepared on another machine using the offline instructions.
- For remote users: a client-managed HTTPS hostname, certificate and reverse proxy or ingress.
- For operational analytics: approved source connectivity and dedicated read-only database accounts, or an approved HTTPS aggregate endpoint.

The frontend bundle is prebuilt. Client users do not need Node.js or host Python for Docker installation. The supplied resource values are starting settings, not a verified production capacity promise.

## Quick install

1. Extract the ZIP into a writable folder on the client server.
2. **Windows Docker Desktop:** start Docker Desktop, then double-click `Start.cmd`. **WSL2 Ubuntu-22.04:** start Docker Engine in that distribution and double-click `Start-WSL.cmd`.
3. **Linux:** open a terminal in the folder and run `bash install.sh` as the approved Docker operator. The script does not install Docker or silently request sudo.
4. Complete the setup prompts: display name, public URL, installed OpenG2P links and authentication. For local accounts, choose distinct author/editor, reviewer and publisher usernames and passwords. The publisher account can also view/export analytics. No administrator password is supplied in the ZIP.
5. Open `http://127.0.0.1:18110/experience/` on that server for localhost mode. For HTTPS mode, open the configured HTTPS URL after configuring the proxy. Secure cookies intentionally do not work over the localhost HTTP URL when HTTPS mode was selected.
6. Sign in, review a draft, submit it, sign in as the independent reviewer, approve it, then publish with the publisher account. Seed guides are drafts and staff-only by default.

An existing `.env` makes the installer retain settings and restart the existing release. It does not reset passwords, delete data or overwrite the client database. To change a password, use Account after local sign-in. For an operator reset:

```sh
docker compose exec experience python tools/account.py editor --roles knowledge-editor
```

This prompts for a new password and revokes old sessions for that local account. It does not change an OpenG2P account. Do not remove `.env` as a password-reset method: bootstrap hashes only create missing accounts; they never overwrite existing users.

## HTTPS reverse proxy

Keep the application port bound to loopback. Use the client's existing Nginx/ingress certificate and hostname. Set `public_base_url` to `https://experience.CLIENT-DOMAIN/experience` before startup. An example location to add inside the client's HTTPS server block:

```nginx
location /experience/ {
    proxy_pass http://127.0.0.1:18110;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto https;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_connect_timeout 10s;
    proxy_read_timeout 65s;
}
```

The URI is preserved. Do not add a trailing slash to `proxy_pass` in this example. If the proxy runs in a different container or on a different node, loopback does not address the application host; have the client operator provide an explicitly approved private route. Do not automatically expose `0.0.0.0` or remove existing network policies. This kit does not issue certificates or modify the client's web server automatically.

## OpenG2P links and native contextual help

Launcher URLs are set in `config/deployment.json`. Only enabled services appear. Persona buttons organise navigation; native applications retain their own authentication and authorisation. No registration, enrolment, payment or approval request is submitted to OpenG2P by the launcher.

The wizard creates `config/EMBED-SNIPPET.html`. Add its tags to the approved layout/template or asset extension of each target application, excluding login screens. Keep the documented script order. Permit the configured experience origin in that application's CSP `script-src`, `style-src` and `connect-src`. `allowed_origins` contains exact HTTPS application origins, not wildcards.

Prefer explicit screen attributes:

```html
<main data-km-module="intake" data-km-stage="Household details" data-km-persona="officer">
```

The module and stage must match approved published guidance. Alternatively add host/path rules under `screen_mappings`. Test tabs, modals and SPA route changes. Generic native presets are starting points, not a compatibility guarantee. Unknown screens show missing guidance rather than guessed instructions.

Cross-origin embedded help deliberately requests only public guidance without credentials. Staff-only guidance stays protected; open the knowledge library in a separate authenticated tab to read it. This release does not share staff cookies or tokens between domains. An authenticated cross-domain staff-help adapter is a separate integration, not enabled by permissive CORS.

Replacing native Registry/PBMS forms requires version-specific application code or Odoo add-ons. The kit does not overwrite those applications. The Figma design baseline and simulated Nigeria lab workflows are separate deliverables.

## OIDC / Keycloak

Choose `oidc` in setup and supply the issuer, confidential client ID and secret. Register the exact redirect URI shown: `PUBLIC_BASE_URL/auth/callback`. Use Authorization Code flow. Authlib validates the OIDC response and uses PKCE. Configure the IdP to include the chosen roles claim **in the ID token**; the default claim path is `realm_access.roles`. The identity provider must include `iss` and `sub`. The login route does not infer permissions from a browser persona.

Map external roles explicitly under `auth.claim_to_roles`. Internal roles are `knowledge-editor`, `knowledge-reviewer`, `knowledge-publisher`, `knowledge-reader`, `analytics-viewer`, `analytics-exporter`, `registration-officer`, `verification-officer` and `programme-supervisor`. Unmapped claims grant no internal role. Staff audience mappings are configured under `audience_roles`.

App sessions expire after one hour; IdP role changes are reflected at the next application sign-in. Sign out clears the application session; it does not perform global IdP logout. Local accounts remain in the kit database if authentication is switched, but cannot log in while OIDC mode is selected.

Existing trusted gateways can use mode `gateway`, strip all inbound `X-Experience-*` headers and inject verified subject/name/roles plus the private matching gateway secret. Keep backend access private. A gateway-mode direct login page cannot authenticate a user. Gateway setup is an operator configuration option, not part of the local-account wizard.

## Analytics connections

Knowledge governance, guide page opens, nonempty search result counts and helpfulness votes work against this kit's own data. Search text, beneficiary records, bank details and identity tokens are not collected. A pseudonymous session digest is retained for deduplication/rate limiting. Raw events are retained for 90 days and daily usage aggregates for 366 days. Opens are page loads, not unique readers. The collector performs retention cleanup even when no backend source is configured.

Backend collectors default to every 900 seconds. A source older than 1800 seconds is stale. A failed refresh retains the last valid values and displays a failure; missing data is not zero. Source metrics have their own scope and are not added across overlapping systems.

Setup can configure read-only PostgreSQL profiles for `registry-1.2`, `pbms-3`, `awe` and `bridge-3`. These query the schemas described in `collector.py`, based on the Nigeria implementation. **The client must verify these exact tables/columns against its installed release.** A profile label is not certification for all releases. No database names, usernames or passwords are assumed. Client-owned roles should have SELECT on only the required tables/views; do not use administrative credentials. Connections enforce `sslmode=verify-full`; copy a client CA into `config/certs/` and give its container path if necessary. Compose mounts the config directory read-only.

For different schemas, use an approved aggregate view with columns `metric TEXT, label TEXT, value NUMERIC`:

```json
{"id":"registry","enabled":true,"adapter":"postgres","profile":"approved-view","schema":"reporting","view":"experience_metrics","dsn_env":"SOURCE_REGISTRY_DSN"}
```

For an existing authenticated HTTPS aggregate API:

```json
{"id":"registry","enabled":true,"adapter":"https-json","url":"https://API-HOST/approved/experience-metrics","allowed_hosts":["API-HOST"],"token_env":"REGISTRY_METRICS_TOKEN"}
```

Expected API response:

```json
{"metrics":[{"metric":"household_records","label":"Households","value":123}]}
```

Only numeric aggregates with approved labels belong in this endpoint. Do not place names, bank references, case identifiers or query text in labels. The kit validates shape, finite nonnegative numbers and bounds, not the business meaning of an approved label. It refuses HTTP, redirects, extra response fields and responses above 1 MiB. Store tokens/DSNs only in `config/connectors.env`, never in JSON, JavaScript or source control. Restart both application and collector after changing JSON source definitions; recreate the collector after changing its environment secrets. Source tables are never migrated by this kit.

The analytics UI and aggregate CSV are supplied. Superset is not installed or reconfigured automatically. The existing Superset workspace remains separate. Confirmed settlement, cross-domain contextual-help usage and causal task-effectiveness metrics are not included.

## Health checks and troubleshooting

```sh
docker compose ps
docker compose exec -T experience python tools/healthcheck.py
docker compose exec -T collector python collector.py
docker compose logs --tail=80 experience collector
```

The one-off collector exits nonzero if an enabled source fails; its logs do not print raw connection exceptions. In the scheduled loop, source failures remain visible in analytics and are retried. Check TLS, CA paths, DNS/network policy, SELECT permissions and table versions before modifying a profile.

No launcher links: configure installed URLs and enable those services. Empty library: starter guides are drafts; complete independent review/publication. Private guide missing in embedded help: use the authenticated library as documented above. Login loops after HTTPS setup: use the configured HTTPS URL and confirm forwarded URI/cookie paths. Binding failure: resolve the port conflict with the operator; scripts do not take over a running service.

## Acceptance before production

Build/startup, isolated HTTP/TLS integrations and restore have passed under WSL2. Repeat startup and deployment acceptance in client staging; those checks do not establish compatibility with the actual client instance. Check links and native permissions, SSO roles, staff/public separation, independent review, draft-versus-live visibility, archive/restore, source reconciliation, stale/failure displays, CSV permissions, mobile help and backup/restore. Publish only approved local SOPs. Test client translations and accessibility in their environment. Record installed image digests, OpenG2P versions, configuration version and acceptance owners.
