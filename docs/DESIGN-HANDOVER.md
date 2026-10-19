# NigeriaG2P UX/UI and interactive design baseline

Prepared by Sathvick Infotech Private Limited · 19 October 2026 · v1.0

## Start here

Open `designs/NigeriaG2P-Master-UX-UI-Prototype.figcraft` in FigCraft for the editable master.
Use its Present/Play control and choose **00 · NigeriaG2P service map**.
Select a service, then use its task actions. **Journey index** exposes every named state.
Each module also has its own prototype starting point. **All services / Service map** returns to the master navigation.

For Figma, import `designs/NigeriaG2P-Master-UX-UI-Prototype.fig` from Figma's file browser. Inspect text, components, the Prototype panel and flow starting points, then test the example journeys below. Figma import/playback has **not** been independently verified here. These are actual FigCraft-generated `.fig` exports, not renamed images or SVGs. Their layer trees and prototype destinations were checked by reopening them in FigCraft; that is not equivalent to validating them in Figma.

`designs/NG2P-*.figcraft` and `.fig` are the 26 application-area files for smaller handovers. Each contains its own service entry, foundations, screens and task index. Cross-application transitions are included in the master only. The standalone files return to their own local service map.

Open `Prototype-Preview.html` to inspect an offline browser companion using the same screen images and clickable destinations. It is supplementary; the editable design deliverables are under `designs/`.

## Contents

- **240 task/state screens** across **26 application areas**.
- **28 master pages**, including the service map and foundations; **27 prototype flow starts**.
- **8 reusable native components**, linked button instances, semantic colour styles and typography styles.
- Desktop 1440 × 1040 layouts; mobile 390 × 844 field and public-portal layouts.
- **1537 clickable controls** in the master. Text and button backgrounds share destinations in the native files; raw interaction counts therefore exceed the count of visible controls.
- `handover/Screen-Register.csv`: every designed screen, responsible role, route, source and caveat.
- `handover/Interaction-Register.csv`: named source/action/destination mapping.
- `handover/Source-Manifest.json`: hashes of local files used as reference.
- `handover/Validation-Report.json`: exact checks and remaining limitations.
- `previews/`: all application screen previews. `source/`: editable command scripts and structured screen specification.

## Screen naming

`NG2P-{MODULE}-{###} / {Task} / {Viewport} / {State}`

Example: `NG2P-MBR-004 / Correct household details / D1440 / correct-household-details`.

Frame IDs are stable within this design baseline. D1440 means desktop; M390 means mobile.
Each application page contains task frames in reading order and a separate journey index.
Components use `NG2P/Button/Primary`, `NG2P/Input/Default` and related semantic names.

## Application coverage

- **AUTH — Identity and access:** 7 screens; Proposed shared UX.
- **HOME — Service and persona workspaces:** 6 screens; Source-led redesign.
- **MBR — Beneficiary repository:** 17 screens; Source-led redesign.
- **REG — Modern social registry:** 8 screens; Native reference redesign.
- **RADM — Social registry administration:** 5 screens; Proposed native reference.
- **PBMS — Programme management:** 15 screens; Source-led / proposed native UX.
- **AWE — Approval workflows:** 8 screens; Native reference redesign.
- **SPAR — Payment account registry:** 9 screens; Proposed private-API UX.
- **BRG — G2P Bridge payments:** 13 screens; Source-led / proposed private UX.
- **FLD — Last-mile delivery:** 10 screens; Source-led demonstration.
- **PAR — Partner and agent management:** 11 screens; Source-led / proposed native UX.
- **CON — Consent management:** 7 screens; Proposed native reference.
- **GRM — Grievance resolution:** 11 screens; Source-led demonstration.
- **KMS — Knowledge management:** 21 screens; Source-led redesign.
- **CMS — Public content management:** 11 screens; Source-led demonstration.
- **PORT — Beneficiary and public portal:** 13 screens; Source-led demonstration.
- **ANL — Operational and knowledge analytics:** 11 screens; Source-led redesign.
- **GEO — Geographic record insights:** 5 screens; Source-led redesign.
- **ODK — Field data collection administration:** 6 screens; Proposed native reference.
- **MDM — Master data administration:** 6 screens; Proposed native reference.
- **IAM — Staff access administration:** 7 screens; Proposed native reference.
- **SUP — Superset reporting:** 6 screens; Source-led / native reference.
- **PADMIN — Portal programme administration:** 5 screens; Native reference redesign.
- **SIM — Payment and partner simulations:** 9 screens; Source-led demonstration.
- **OPS — Supporting service consoles:** 9 screens; Proposed console reference.
- **UAT — Readiness and acceptance evidence:** 4 screens; Source-led redesign.

## Review these journeys

1. MBR: work queue → household → correction → submit → independent checklist → approval confirmation → synchronisation. Branch into validation errors, return with reason and sync conflict.
2. KMS: library → search → guidance → feedback; editorial queue → draft → optional AI suggestion → save → independent review → publication confirmation → version history → archive → restore. Include reviewer return and version conflict.
3. PBMS/Bridge: approved NSR import → eligibility → enrolment → benefit calculation → batch review; dispatch acceptance → bank response → statement → reconciliation, mismatch, callback retry, reversal and duplicate protection. Only fictional local Example Bank evidence is represented.
4. Field: assignment → capture → device queue → synchronisation → conflict or success, with mock mismatch and expired certification states.
5. Portal/GRM: programme discovery → details → existing support/application prototype → validation/submission/tracking; grievance → acknowledgement/escalation/resolution.
6. Analytics: overview → filters → current operations / knowledge usage → source freshness → stale/failed source → aggregate export or denied role.

## What this baseline represents

The designs are a consistent source-led redesign and a reviewable interaction baseline, not a pixel-perfect capture of every installed product. Local templates, React persona code, the service catalogue and project operational notes were read. No live sign-ins, private native screens or current production deployment were audited during this build.

Private SPAR/Bridge interfaces and uninspected native administration screens are explicitly **proposed reference designs**. Supporting-service screens are overview references, not exhaustive replacements for MinIO, Kafka, Keycloak, ODK, Superset or other upstream consoles. API-only services do not imply an existing UI. Consequently, this package must not be described as a verified complete inventory of every upstream screen. Reconcile the register with Ooru before final acceptance.

The interactive prototypes use click navigation and state transitions. Text fields, uploads, searches, role changes, approvals, exports and backend outcomes are illustrated; this is not a functional application or permission test. Fields and vector/text layers are editable in the design document. The eight components and styles provide a starter design system, not a full production component library. Fixed desktop/mobile frames are provided, not every responsive breakpoint or a full translation set.

## Required project distinctions

- Registration/application screens are prototypes; the core Phase-1 CCT flow starts from approved NSR data.
- Independent verification and publishing roles remain separate from authors/makers.
- A PBMS process marked complete or a Bridge-accepted instruction is not confirmed production settlement.
- The portal backend is separate and does not automatically join PBMS 3 applications.
- Field identity/GPS, intake channels, CCT rules and agent certification are sandbox demonstrations pending policy/device approval.
- Analytics filter scopes, UTC timestamps, stale-source states and export permissions must remain explicit. Opens are not unique readers; contextual-help usage and settled-payment analytics are not claimed.
- Public language options are English, Hausa, Yoruba and Igbo; the design labels and sample content are English. Translations and accessibility testing are pending.
- No scope, price, hours, UAT acceptance, production readiness or commercial variation is approved by this package. The earlier proposal and KMS quantity baseline are unchanged.

## Acceptance and remaining work

1. Import the master `.fig` in Figma and verify layer editability, fonts, components, links and all 27 starting points. FigCraft warns that `.fig` export is experimental. Plugin metadata is omitted from this export, so keep the CSV/JSON registers and `.figcraft` source with the handover.
2. Ooru should confirm private native screens, actual roles, canonical workflows, error codes and permitted channels against the register.
3. Government/PMO should approve SOPs, field/consent wording, eligibility, payment authority, grievance SLAs and translations.
4. Reconcile any missing upstream states and breakpoints; review the proposed redesign against the installed products rather than assuming exact parity.
5. Test keyboard use, screen-reader names, contrast, focus order, mobile devices and real integration behaviours in implementation.

## Validation performed

All 27 `.fig` exports reopened through FigCraft's importer with matching structural counts. The master retained semantic source/action/destination mappings. All 240 task/state screens are reachable from its service map through actions and task indexes. No direct screen children extend outside their frames. Screen previews were rendered by the installed FigCraft engine. This does not prove Figma compatibility or live system behaviour.

## References

- FigCraft CLI: https://github.com/storytold/figcraft/blob/main/docs/cli.md
- FigCraft export compatibility: https://github.com/storytold/figcraft/blob/main/docs/file-format-parity.md
- Figma import guide: https://help.figma.com/hc/en-us/articles/360040027794-Guide-to-imports-in-Figma-Design

Browser companion checks confirmed the KMS draft/review/publication flow, mobile sync-conflict recovery, analytics failed-source recovery and the MBR-to-modern-registry transition. All 26 application contact sheets were visually inspected.
