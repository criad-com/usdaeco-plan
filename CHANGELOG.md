# Changelog

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
