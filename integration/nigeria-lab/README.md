# Staff sign-in redirect patch for the Nigeria demonstration portal

This patch applies to the separately deployed Nigeria lab registration application, not the experience kit in this repository. The original `registration_app.py` used by the lab had SHA-256 `5038a8de937fc00ea9e972ef8208fc7cecae3e21812b6a41b340ecb81c0b0e5b`. It is provided as an integration patch because the lab application and companion kit have separate sources and release processes.

Staff users with the registration, verification or supervisor persona roles were routed after normal login to `/registration/staff`, which requires the separate `iqs-intake-reviewer` role and returned 403. The patch keeps reviewers on that protected page and routes other staff to `/registration/workspace`. Workspace authorization and reviewer-only API checks are unchanged; unassigned identities still have no workspace access. Explicit destination flags remain unchanged.

From a matching lab source directory, review then run `git apply --check /path/to/staff-login-redirect.patch` and `git apply /path/to/staff-login-redirect.patch`; apply and test in staging before deploying. Do not apply to an unreviewed version. On the Nigeria demo, nine isolated workspace tests passed. Live login checks using temporary registration, verification and supervisor accounts reached their workspace with HTTP 200, while their reviewer page remained HTTP 403. The existing reviewer still reached the reviewer page. Temporary accounts were deleted after the test.

This change addresses the post-login redirect only; it does not claim to fix a separate error on the Modern Social Registry household detail page. Investigate that service's authorization and master-data requests independently.

## Household geography lookup repair

On the Nigeria demo, household details showed HTTP 400 because the installed registry widget expects each geography level inside `widget-data-source.params.level_id`, while the lab metadata stored it only at the top level. The options also lacked value and label mappings. `fix_geo_widget_params.py` repairs only matching master-data geography widgets in `g2p_register_sections`, saves a restricted metadata backup, and applies optimistic checks in one transaction. It requires `labdb.py`, Kubernetes and authorised lab database access; review and test against a backup before running in any other environment. The script is idempotent. No household records are changed.

On 28 October 2026 this updated four widgets in the household and individual location sections. A synthetic household detail then loaded without the initial 400; the State selector displayed names and selecting Lagos loaded Ikeja and Surulere. The test selection was cancelled. The demo LGA catalogue remains limited; this is not a complete Nigeria geography dataset. The lab's localization procedure must also retain `params.level_id`, `valueKey=level_value_id` and `labelKey=level_value_mnemonic` when it rebuilds widget metadata.
