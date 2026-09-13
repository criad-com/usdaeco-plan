# Changelog

## 0.1.5

- Add `AECO_STUDY_ROOT` (default `/`), the import CLI's `--study-root` option
  and the writer's `study_root` argument. Programme layers author plain Scope
  ancestors and set their default prim to the namespace's top-level prim.
- Discover programmes from data for presentation, Gantt output and stock-USD
  playback, matching the existing validator and 4D traversal. Resolve derived
  predecessors and unresolved import aliases within the selected study.
- Discover programme cameras beneath `/Renders`, including suite namespaces;
  use the selected data-centre stage's manifest for source-census checks.
- Test `/Studies/plan` and a deeper custom root on the v0.5.2 full delivery,
  both importers and CLIs, workspace findings, the retained project catalog,
  and 552 relocated plugin-free visibility checks. Preserve the committed
  default example, renders and direct dependency pins.

## 0.1.4

- public re-pin: usdaeco-toolchain v0.3.10, usdaeco-core v0.9.5,
  usdaeco-axis v0.1.5, usdaeco-datacentre v0.4.8. Record all four checked
  revisions beside release tags; retain supported requirement ranges.
- Republish the planning example with the pinned toolchain and source release.
  The crate, 13 layers and both Gantt files remain byte-identical. Retain the
  30 committed images after fresh render checks; sampling changes image bytes.
- Record incomplete Nix build verification and unsuccessful anonymous public
  access to the requested axis and datacentre tags in the acceptance evidence.

## 0.1.3

- public names → github.com/criad-com: update flake inputs and documentation links.
- Pin toolchain v0.3.8 and align the example manifest's toolchain pin for S22;
  retain all other pins and requirement ranges. No results or renders republished.

## 0.1.2

- Declare a 480-second example budget and use the shared harness directly;
  remove the gate's private timeout workaround. Pin toolchain v0.3.6 with S29.
- Default preview renders to 8 samples per pixel, reuse the composed building
  across programmes, and count source prims in one traversal. Contact sheets
  and GIFs continue to use the saved weekly frames; reuse returned render
  metadata instead of decoding all 28 images again for the manifest.
- Add fresh one-/two-thread benchmarking with profiles and artifact comparisons.
- Refresh the 24 weekly PNGs, two contact sheets, two GIFs, vanilla PNG and
  user-documentation contact sheet for the new sample setting. Findings, all
  13 USDA layers, both Gantt SVGs and the committed crate remain byte-identical.

## 0.1.1

- Re-pin to train aeco-0.7.0: core v0.9.2, axis v0.1.2, toolchain v0.3.5
  and datacentre v0.4.5; retain requirement ranges and historical programme fixtures.

- Refresh example pin provenance only; the pod source, crate and 13 authored
  layers remain byte-identical. Retain the committed renders.

## 0.1.0

- Add programme, activity and milestone records with schedule and workspace APIs.
- Import P6 XER and MSPDI through deterministic drivers with ordered multiedges.
- Register eight planning validators with seeded-defect tests.
- Derive unique predecessor relationships, stock-USD 4D visibility and lookahead.
- Publish the pinned pod example, both programme issues, 24 weekly frames,
  contact sheets, GIFs, Gantt SVGs and a relocatable self-contained result.
- Add explicit programme date bounds and document source-envelope limitations.
