# Acceptance evidence

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
