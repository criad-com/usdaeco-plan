# Demo data-centre planning example

The `pod` variant at v0.4.5 supplies the building. Committed inputs contain
programme A (as issued) and B (resequenced) in P6 XER and MSPDI XML, plus scope
and workspace bindings. The source files were emitted by the pinned generator
in a disposable copy; this example never writes to a dependency checkout.

From the repository root, configure the environment in the root README and run:

```sh
env -u PYTHONPATH "$PYTHON" examples/datacentre/run.py
env -u PYTHONPATH "$PYTHON" examples/datacentre/run.py --publish
```

Ordinary runs write `out/`. Publication updates `result/`, `renders/` and
`manifest.json` only after expected findings agree. Expected counts were read
from the pinned `dc.manifest.json`; the runner checks that census on every run.

A has AccessAfterEnclosure, WorkspaceOccupied and EnclosureBeforeInspection
(two errors and one warning). B has zero planning findings. Detailed affected
paths and occurrence counts are retained in `expected/findings.json`.
Each programme controls 23 elements over 12 sampled weeks; both source formats
produce byte-identical normalized driver layers.

Open from this directory, with stock USD and no source checkouts:

```sh
usdview result/example.usdc
usdview result/layers/out/A/play.usda
```

`result/example.usdc` is B flattened with all referenced source data.
A's `play.usda` overlays all A programme, predecessor, visibility and presentation
opinions on that same crate. The full `result/` directory is relocatable.
`result/layers/out/B/play.usda` is an equivalent explicit B layer stack.
Use time codes 0–77, stepping by seven to see weeks 1–12. Week 3 delivers the
amber pod; A blocks the corridor until week 9, while B parks it in the office
and removes it before week 6. Default-time mode shows the whole design.

`renders/A.*.png` and `B.*.png` contain one frame per week. `A.sheet.png` and
`B.sheet.png` are contact sheets in chronological order; GIFs are bounded
previews and may coalesce unchanged adjacent frames. The authoritative frame
inventory is the 24 PNGs. `A.gantt.svg` and `B.gantt.svg` are drawn from the
composed prims. `result/vanilla.png` is rendered in an isolated plugin-free process.

The manifest declares `budgetSeconds: 480` for the complete fresh runner. The
default Embree quality is 8 samples per pixel, with ambient occlusion disabled.
The two programmes reuse the composed building stage; A's opinions are removed
before importing B. Each weekly PNG is rendered once, then the shared toolchain
derives its programme's contact sheet and GIF from those files. See the
[acceptance evidence](../../docs/acceptance.md) for timings, profiling and the
precise image changes in this release.

Pinned runs create an ignored `inputs/source` alias to the supplied data release.
Archived layers reference the self-contained crate and each other, so the
published result remains usable without that alias or any source checkout.

The presentation colours and temporary-position transform are derived views.
The core spatial hierarchy and source layers are untouched. The stored
programme layers contain no visibility samples or derived predecessor targets.
See [the use case](../../docs/usecase.md) for model decisions and limits.
