#!/usr/bin/env python3
"""Compose the pinned pod stage, validate A/B and publish 12 weeks of each."""
import argparse
from functools import partial
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(os.environ.get('TOOLCHAIN_DIR', ROOT.parent / 'usdaeco-toolchain')) / 'tools'))
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT))
from usdaeco_check.example import run_example
from usdaeco_plan.cli import register
from usdaeco_plan.example import hook, SIZE, FRAMES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    if not os.environ.get('AECO_DATACENTRE_ROOT'):
        parser.error('AECO_DATACENTRE_ROOT must identify the pinned data-centre checkout')
    register()
    # Bound the preview cost; callers can explicitly select a different quality.
    os.environ.setdefault('HDEMBREE_SAMPLES_TO_CONVERGENCE', '8')
    example = Path(__file__).resolve().parent
    records = []
    manifest = run_example(example, partial(hook, render_records=records),
                           variant='pod', size=SIZE, frames=FRAMES, keywords=[])
    # Both render calls already measured their files. Reuse those records;
    # decoding all 28 images again only to inventory them is unnecessary.
    manifest['renders'] = sorted(records + manifest['renders'], key=lambda item: item['path'])
    manifest['programmes'] = {'A': 'result/layers/out/A/play.usda', 'B': 'result/example.usdc'}
    (example / 'out/manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    if args.publish:
        for name in ('result', 'renders'):
            destination = example / name
            if destination.exists():
                shutil.rmtree(destination)
            shutil.copytree(example / 'out' / name, destination)
        shutil.copyfile(example / 'out/manifest.json', example / 'manifest.json')
        for key in ('A', 'B'):
            shutil.copyfile(example / ('out/' + key + '.gantt.svg'), example / ('renders/' + key + '.gantt.svg'))
    print('== stage: complete (24 weekly frames, two contact sheets and two GIFs)', flush=True)


if __name__ == '__main__':
    main()
