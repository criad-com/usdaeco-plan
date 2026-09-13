# Acceptance evidence

## v0.1.5 configurable study root

The default example keeps its v0.4.8 pod source and existing direct dependency
pins. Additional integration tests use the v0.5.2 full delivery at the fixture
revision recorded in `dependencies.json`.

| Acceptance | Status | Evidence |
|---|---|---|
| Repository gate | PASS | 51 checks, 0 failed, 2 not run; all 8 core and 8 planning validators load |
| Structure | PASS | S01–S29, including generated-schema validation, manifest consistency and sanitized contents |
| Python tests | PASS | 36 passed, no skips, including 12 study-root cases |
| Configurable authoring | PASS | Environment and explicit writer/CLI roots; `/`, `/Studies/plan` and `/Studies/review/phase`; invalid roots rejected |
| Programme layers | PASS | XER and MSPDI agree after normalization; plain Scope ancestors; `defaultPrim` is `Studies` for nested roots and `Programme` for `/` |
| Readers and relationships | PASS | Validation, lookahead, predecessor targets, 4D and normalization follow authored data even with a different environment setting |
| Full-stage hook | PASS | A retains its 3 named findings and B is clean; source census matches the full-stage manifest; Gantt SVGs retain the committed bytes |
| Root tidiness | PASS | Only project, Studies and Renders roots; project catalog retained with no root catalog; suite cameras remain beneath `/Renders/plan` |
| Relocated stock playback | PASS | 552 visibility assertions over both programmes in a copied result with no family plugins or study-root setting |
| Version and schema | PASS | Library, package, runtime and resource metadata equal 0.1.5; build and generated-schema validation pass |
| Artifact preservation | PASS | All 48 committed result, render, manifest and documentation-image files byte-identical to v0.1.4 |
| Fresh default example | PASS | 100.532 s / 480 s; editable layers and normalized crate match committed results; 28 fresh render records and an independent vanilla render |
| Nix | NOT RUN | One offline attempt with four local direct-input overrides failed resolving a temporary-directory symlink before evaluation/build; no retry |

The integration tests use `AECO_PLAN_TEST_STAGE` when supplied; otherwise they
look for the sibling v0.5.2 checkout. Missing integration data is reported as
skipped, never passed. All integration cases ran for this acceptance.

### Deviations for v0.1.5

- The v0.5.2 full delivery is an additional recorded test fixture. The direct
  v0.4.8 pod pin and committed example manifest stay unchanged to preserve the
  default example's bytes.
- Nix evaluation and build are unverified because the single local attempt
  failed during input-path resolution. No lockfile is committed.
- No `STEERING.md` was present in this checkout or its ancestor directories
  when checked before committing.
- GUI interaction was not tested. The relocated stock-USD probe supplies the
  playback evidence, alongside the gate's fresh example renders.

## v0.1.4 public re-pin

Target: usdAecoPlan v0.1.4 against core v0.9.5, axis v0.1.5,
toolchain v0.3.10 and datacentre v0.4.8, variant `pod`. The four tagged
checkouts match the revisions in `dependencies.json`. Supported ranges remain
unchanged. [The publication receipt](public-repin.json) records the comparisons.

| Acceptance | Status | Evidence |
|---|---|---|
| Direct pins | PASS | All 4 requested tags in flake URLs, dependency revisions and example provenance; no commit-hash family refs |
| Patch version | PASS | Library, Python package, runtime and generated resource metadata all equal 0.1.4 |
| Repository gate | PASS | 51 checks, 0 failed, 2 not run; 8 core and 8 planning validators loaded |
| Structure lint | PASS | S01–S29: 29 checks, 0 failed under toolchain v0.3.10, including S05, S22 and S25 |
| Python tests | PASS | 24 passed in 1.34 s from source, without package installation |
| Publication | PASS | Documented build and `run.py --publish`; 107.671 s at two USD threads and 8 samples per pixel |
| Fresh example gate | PASS | 97.555 s / 480 s; 28 non-blank weekly/summary renders plus a fresh stock vanilla render |
| Planning results | PASS | A has 3 named findings, B has 0; both normalized XER/MSPDI pairs agree; each programme has 0 core errors and 2 source warnings |
| Stock playback | PASS | 12,358 prims, 552 visibility assertions; self-contained result is 2,025,800 bytes across 16 files |
| Artifact comparison | PASS | Crate, 13 editable layers, 2 Gantt SVGs and 30 retained images: 46 files byte-identical; all 3 pod source layers and generated schema also byte-identical |
| Provenance-only result diff | PASS | Result README changes only the source tag; manifest changes 10 fields: tags, revisions and the notice hash |
| Public-reference sweep | PASS | 104 tracked files; zero former public-org flake references and zero commit-hash family refs |
| Anonymous public tags | PARTIAL | Toolchain v0.3.10 and core v0.9.5 resolve; axis v0.1.5 and datacentre v0.4.8 request authentication, with HTTP 404 on their public tag pages |
| Nix build | NOT PROVEN | One offline attempt, 8 local overrides; 5 Darwin derivations evaluated; stopped after 180.024 s while building a source dependency, exit 1 |
| Private real-project XER | NOT RUN | Private client data is excluded and was never read |

All four integration revisions were resolved from their annotated release tags.
Source codeless plugins supply the exact release metadata: the existing build
outputs had older metadata, while their generated schemas were byte-identical.
No dependency checkout was built or changed.

The fresh publication changed all 29 rendered PNG/GIF files through sampling;
mean absolute RGB differences for PNGs range from 0.227891 to 0.492595 on a
0–255 scale. Fresh previews passed the shared render checks. Retaining the
previous preview bytes and their receipts keeps the committed result diff
limited to provenance. This follows the core v0.9.5 CHANGELOG's render treatment;
no upstream geometry or planning behaviour changed.

### Deviations for v0.1.4

- Requested axis and datacentre public tags could not be confirmed anonymously
  on 2026-09-12. The exact requested tags remain pinned; public access to those
  releases and complete online recursive resolution need review before a claim
  that an outsider can build the flake.
- The single `nix flake check --offline --no-write-lock-file` attempt used local
  overrides for the four direct inputs, two nested datacentre inputs and exact
  archives of toolchain's core v0.9.2 fixture and aeco-toolchain v0.4.0. The build
  remained incomplete after 180 seconds and was cancelled; no retry or lockfile.
- Fresh raster outputs were validated, then the 30 committed images were kept
  to avoid sampling-only changes. Geometry, editable layers and Gantt output
  remain exactly the fresh publication's bytes.
- Historical v0.4.2 programme-fixture provenance, earlier release evidence and
  `benchmark.json` remain unchanged. They are committed data/history, not fetched
  flake inputs; changing their recorded origins would misstate the evidence.

## v0.1.3 public names

Target: usdAecoPlan v0.1.3 against core v0.9.2, axis v0.1.2,
toolchain v0.3.8 and datacentre v0.4.5, variant `pod`. Verification uses
archives of those exact tags, independent of advancing dependency checkouts.
The public flake inputs and documentation links now use `criad-com`.

| Acceptance | Status | Evidence |
|---|---|---|
| Repository gate | PASS | 51 checks, 0 failed, 2 not run; all 8 core and 8 planning validators loaded |
| Structure lint | PASS | 29 checks, 0 failed under toolchain v0.3.8, including S05 public names, S22 manifest pins and S25 sanitization |
| Python tests | PASS | 24 passed in 0.89 s from source, without package installation |
| Fresh example | PASS | 103.479 s / 480 s at two USD threads; 12,358 plugin-free prims, 28 non-blank renders, 552 visibility assertions; A retains 3 named findings and B is clean; both XER/MSPDI pairs agree |
| Public references | PASS | All 103 tracked files scanned; 0 references to the former public organization |
| Patch version | PASS | Library, package, runtime and resource-plugin versions all equal 0.1.3; CHANGELOG updated |
| Artifact preservation | PASS | All 47 committed result, render and user-documentation image files byte-identical to v0.1.2; generated schema unchanged |
| Dependency scope | PASS | Only toolchain changes, from v0.3.6 to v0.3.8; other direct pins, historical fixture pins and requirement ranges unchanged |
| Private real-project XER | NOT RUN | Private client data is excluded and was never read |
| Nix | NOT RUN | One offline flake-check attempt with local direct-input overrides failed on the frozen axis release's nested datacentre v0.4.2 input (HTTP 404); evaluation/build not proven |

The example manifest changes only `pins.toolchain.ref` to satisfy S22 and
the shared harness's pin comparison. Its artifact hashes, source provenance
and result inventory are unchanged. No results or renders were republished.

The timing profiles, second-layout measurements and image-refresh account
below are historical v0.1.2 evidence; they were not rerun for this patch.
[benchmark.json](benchmark.json) retains its original version and measured pins.

### Deviations for v0.1.3

- Manifest pin metadata was aligned with the required toolchain pin even though
  the manifest contains no public URL; S22 requires equality with dependencies.json.
- The preserved axis pin contains an unresolved nested input. Nix was attempted
  once; changing another pin or its source is outside this patch's scope.

## v0.1.2 baseline

Target: usdAecoPlan v0.1.2 against core v0.9.2, axis v0.1.2,
toolchain v0.3.6 and datacentre v0.4.5, variant `pod`. Checks use fresh
archives of those exact tags, independently of advancing dependency checkouts.

| Acceptance | Status | Evidence |
|---|---|---|
| Programme A | PASS | 3 named findings: AccessAfterEnclosure (error, 4 occurrences), WorkspaceOccupied (error, 1), EnclosureBeforeInspection (warn, 2) |
| Programme B | PASS | 0 planning findings |
| XER ≡ MSPDI | PASS | A and B normalized driver layers byte-identical; 10 activities each; A 9 links, B 10 |
| 4D stock-USD frame count | PASS | 23 targets × 12 weeks × 2 programmes = 552 visibility assertions in a plugin-free process |
| Weekly renders | PASS | 24 PNGs, 2 contact sheets, 2 GIFs; Gantt SVG for each programme |
| Published result | PASS | Self-contained B crate and portable A overlay stack; 12,358 prims in the B crate; complete result directory 2,025,800 bytes |
| Core validation | PASS | 8 core validators loaded; each programme has 0 errors, 2 source proxy-classification warnings |
| Private real-project XER | NOT RUN | The file is private client data and is never read for this work |
| Python tests | PASS | 24 passed; seeded defects for all 8 planning rules |
| Repository gate | PASS | 51 checks, 0 failed, 2 not run; fresh runner 97.762 s / 480 s at two USD threads |
| Structure lint | PASS | 29 checks, 0 failed, including generated-schema validation, term sweep and S29 |
| Second directory layout | PASS | 29/0 lint, 10 S29 asset paths; 8 core validators loaded; relocated source composes 12,358 prims with 0 errors; shared example comparison passes |
| Runner budget | PASS | `budgetSeconds: 480`; the shared harness executes and times the complete example |
| Nix | NOT RUN | One offline flake-check attempt failed while resolving an unavailable upstream release reference; evaluation/build not proven |

The source census comes from `dc.manifest.json`, checked against composed prims:
2,977 elements, 35 spaces, two levels, 3,012 meshes and 6,238 ports.
The source's own converter/core pins are preserved as published; these runtime
checks do not claim to have regenerated that release.

## Timing and profiling

Run `env -u PYTHONPATH "$PYTHON" tools/benchmark_example.py` with the pinned
dependencies configured as in the README. Each run copies source into a new
root, excluding all old results, renders, source aliases and output caches.
The two runs are sequential; the machine can have unrelated concurrent load.
`PXR_WORK_THREAD_LIMIT` controls USD workers, not the number of concurrent
family examples. Add `--profile` for cProfile files and summarized hot spots.
The benchmark verifies exact findings, USDA and Gantt bytes and normalized
crate contents before accepting each timing.

| Final fresh runner | Wall time | Budget |
|---|---:|---:|
| One USD thread, unprofiled | 155.499 s | 480 s |
| Two USD threads, unprofiled | 99.200 s | 480 s |

Both runs produced 28 raster artifacts and two Gantt SVGs. Findings, the 13
USDA layers and both Gantt SVGs matched the committed bytes; both crates were
also byte-identical, beyond the required normalized comparison. The budget is
3.09 times the slower final measurement, leaving 324.501 seconds of headroom.

The complete one-thread profile after the sample/stage changes took
227.347 seconds. Renderer subprocess calls, including the result probes,
accounted for 80.375 seconds; 139 image decodes accounted for 140.549 seconds
(cumulative times overlap). Re-reading all 28 image records after the shared
harness returned cost about 29 seconds. The final runner instead combines the
two render calls' already measured records, eliminating those extra decodes.
Both contact sheets and GIFs already used the saved weekly PNGs; no additional
render pass was needed for them.

The earlier 100-sample baseline was stopped after 172.429 seconds with four
completed frames; it is an incomplete diagnostic, not a full-run timing or
a measured timeout. Its profile spent 162.911 seconds in renderer subprocess
calls. Final timing evidence is recorded separately in [benchmark.json](benchmark.json).

The 480-second budget accommodates the full 227.347-second profiled run with
more than a twofold allowance. It is below the toolchain's 900-second cap.
The budget covers `run.py`; the harness's independent result and vanilla
checks retain their separate limits. No full parallel family-suite runtime
is claimed by this repository's measurements.

## Relocation verification

The second layout places the plan repository under `projects/visual/planning`,
core under `libraries/common/semantics`, toolchain under `kit`, and the data
release under `published/facility` in a separate temporary root. No sibling
directory names are available. Exact tagged dependency sources are copied;
the core validator import is checked against that copy and all eight registry
entries must load. S01–S29 pass on the complete final repository copy.

The fresh two-thread outputs are also copied into this layout, and the runtime
`inputs/source` alias is retargeted to the relocated release. The composed
source root has 12,358 prims and zero composition errors. The shared
`check_example(execute=False)` verifies those outputs against the committed
result, including all 28 non-blank images and an independent plugin-free
vanilla render. This comparison reuses the measured run's outputs; it is not
an additional fresh-run timing.

## Artifact preservation

Relative to v0.1.1, expected findings, all 13 USDA files under
`examples/datacentre/result/layers/`, `result/README.md`, `result/example.usdc`
and both Gantt SVGs remain byte-identical. The two fresh thread configurations
also compare generated findings and layers to those committed bytes.

The only changed image setting is Embree samples per pixel, from the default
100 to 8. Ambient occlusion remains disabled; cameras, dimensions, purposes,
colours, geometry and dates are unchanged. The exact refreshed image files are:

- `examples/datacentre/renders/A.{0,7,14,21,28,35,42,49,56,63,70,77}.png`
- `examples/datacentre/renders/B.{0,7,14,21,28,35,42,49,56,63,70,77}.png`
- `examples/datacentre/renders/A.sheet.png` and `B.sheet.png`
- `examples/datacentre/renders/A.gif` and `B.gif`
- `examples/datacentre/result/vanilla.png`
- `usdAecoPlan/userDoc/usdAecoPlanExample.png` (the same A contact sheet)

The sheets and GIFs are derived from the new frames; the GIF encoder retains
its existing preview-size cap. Manifest hashes and byte totals are refreshed
for those images. The runner and gate default to 8 samples while honouring an
explicit quality override; the benchmark always selects the default.

## Deviations

- The contract's inspection finding is a warning. The three named A findings
  therefore comprise two errors and one warning. Access also includes the late
  inspection's required access; all four affected activity/region pairs are retained.
- Programme plannedStart/plannedFinish properties are added to make range checks
  meaningful. If source finish is absent, the bound is an explicitly labelled
  activity envelope, not independent proof of a project deadline.
- The prescribed programme/activity subclasses reuse AecoGroupBase for record
  identity and collections. This is an explicit record exception to the core's
  closed group-subclass rule. No spatial structure or product-kind type is added.
- Schedule and workspace properties keep their contracted namespaces, declared
  alongside `plan`. The package uses the requested `kind` tier; its dates remain
  on records.
- A uses a portable layer-selection root over the same flattened B crate, keeping
  the result self-contained without duplicating the building or introducing a
  revision variant. B's temporary-position change is presentation only; source
  containment and identity remain unchanged.
- Nix was attempted once with offline mode and local direct-input overrides.
  The nested `axis/datacentre` reference to v0.4.2 was unavailable during input
  resolution; the cached resolver diagnostic reported HTTP 404. Evaluation
  and build remain unproven; no second attempt was made.
- Dates are at calendar-day precision. CPM, intraday timing, calendar exceptions,
  external predecessor reconciliation and schedule-format export are out of scope.
- GUI interaction was not tested. Relocated stock-USD composition, visibility
  assertions and plugin-free Embree rendering provide the playback evidence.

## Remaining work

Review and merge the branch, publish v0.1.3, rerun the full family train gate,
and resolve the public Nix input graph. No private-data import or GUI-only
claim is required for this release.
