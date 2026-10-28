# Staff sign-in redirect patch for the Nigeria demonstration portal

This patch applies to the separately deployed Nigeria lab registration application, not the experience kit in this repository. The original `registration_app.py` used by the lab had SHA-256 `5038a8de937fc00ea9e972ef8208fc7cecae3e21812b6a41b340ecb81c0b0e5b`. It is provided as an integration patch because the lab application and companion kit have separate sources and release processes.

Staff users with the registration, verification or supervisor persona roles were routed after normal login to `/registration/staff`, which requires the separate `iqs-intake-reviewer` role and returned 403. The patch keeps reviewers on that protected page and routes other staff to `/registration/workspace`. Workspace authorization and reviewer-only API checks are unchanged; unassigned identities still have no workspace access. Explicit destination flags remain unchanged.

From a matching lab source directory, review then run `git apply --check /path/to/staff-login-redirect.patch` and `git apply /path/to/staff-login-redirect.patch`; apply and test in staging before deploying. Do not apply to an unreviewed version. On the Nigeria demo, nine isolated workspace tests passed. Live login checks using temporary registration, verification and supervisor accounts reached their workspace with HTTP 200, while their reviewer page remained HTTP 403. The existing reviewer still reached the reviewer page. Temporary accounts were deleted after the test.

This change addresses the post-login redirect only; it does not claim to fix a separate error on the Modern Social Registry household detail page. Investigate that service's authorization and master-data requests independently.
