# Release 1.0.0-rc1

Sathvick Infotech Private Limited · 19 October 2026

First guided client-deployment candidate, based on the earlier OpenG2P Experience Kit and NigeriaG2P knowledge/analytics implementation.

Included: prebuilt configurable persona frontend, shared navigation and public contextual-help assets, protected KMS lifecycle/history, public/staff visibility, optional review dates, separate local accounts, optional OIDC/gateway integration, knowledge governance/search/open/feedback analytics, configurable read-only PostgreSQL or HTTPS aggregate collectors, CSV export, local persistence, health checks, backups/restoration, Compose scripts, a single-instance Helm chart, offline-image preparation instructions and source/dependency manifests.

The launcher and native help integrate alongside OpenG2P. Native form redesigns, the Figma screens, Nigeria-specific simulated registration/payment/field/grievance workflows, AI drafting, national translations and a full Superset migration are not installed by this kit. No beneficiary records, payment dispatch logic, lab databases, credentials or administrative OpenG2P configuration are shipped.

First startup imports 54 reference guides as unpublished staff drafts. No seed is an approved agency procedure. Existing seed slugs are not overwritten on restart. Publishing requires an independent review. An older live publication remains visible while a draft is edited; archive it if immediate withdrawal is needed.

Knowledge is stored in SQLite with one application instance. Multi-replica/HA KMS and PostgreSQL migration are outside this release. The PostgreSQL adapters concern **read-only source reporting**, not KMS storage. Backend profile compatibility must be checked against the client's installed tables/columns. Newer OpenG2P releases can use an approved aggregate view or the HTTPS metrics contract.

See VALIDATION.json for exact checks and unverified boundaries. Docker build/startup and isolated integration/restore checks passed under WSL2; client staging must confirm storage, ingress, actual SSO and schemas, help embeddings and acceptance. No production readiness, capacity, commercial scope change or client UAT approval is implied by this release candidate.
