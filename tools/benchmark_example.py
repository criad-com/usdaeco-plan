#!/usr/bin/env python3
"""Time fresh example runs at one and two USD threads, with optional profiling."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import pstats
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--threads', type=int, nargs='+', default=[1, 2])
    parser.add_argument('--profile', action='store_true')
    parser.add_argument('--output', type=Path, default=ROOT / 'out/benchmark.json')
    parser.add_argument('--work-root', type=Path, help='retain fresh copies for inspection')
    args = parser.parse_args()
    if any(n not in (1, 2) for n in args.threads):
        parser.error('thread limits must be 1 or 2')
    environment = {k: v for k, v in os.environ.items() if k != 'PYTHONPATH'}
    for variable, sibling in [('TOOLCHAIN_DIR', 'usdaeco-toolchain'),
                              ('CORE_DIR', 'usdaeco-core'),
                              ('AECO_DATACENTRE_ROOT', 'usdaeco-datacentre')]:
        environment[variable] = str(Path(environment.get(variable, ROOT.parent / sibling)).resolve())
    environment['CORE_PLUGIN_DIR'] = str(Path(environment.get(
        'CORE_PLUGIN_DIR', Path(environment['CORE_DIR']) / 'out/plugins/usdAeco/resources')).resolve())
    pins = json.loads((ROOT / 'dependencies.json').read_text())['repos']
    for variable, key in [('CORE_DIR', 'core'), ('TOOLCHAIN_DIR', 'toolchain'),
                          ('AECO_DATACENTRE_ROOT', 'datacentre')]:
        metadata = json.loads((Path(environment[variable]) / 'library.json').read_text())
        if 'v' + metadata['version'] != pins[key]['ref']:
            parser.error(key + ' checkout does not match dependencies.json')
    sys.path.insert(0, str(Path(environment['TOOLCHAIN_DIR']) / 'tools'))
    from usdaeco_check.example_result import normalized_layer
    # Measure the published default, independently of interactive render overrides.
    environment.pop('HDEMBREE_SAMPLES_TO_CONVERGENCE', None)
    environment.pop('AECO_DATACENTRE_STAGE', None)
    budget = json.loads((ROOT / 'examples/datacentre/manifest.json').read_text())['budgetSeconds']
    args.output = args.output.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    records = []
    with tempfile.TemporaryDirectory(prefix='plan-benchmark-') as temporary:
        work = args.work_root.resolve() if args.work_root else Path(temporary)
        for threads in args.threads:
            target = work / str(threads) / 'plan'
            print(f'== stage: fresh example, {threads} USD thread(s)', flush=True)
            # Copy source only: no old frames, result crate, layers or output cache.
            shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns(
                '.git', 'out', 'result', 'result-*', 'renders', 'source',
                '__pycache__', '.pytest_cache', '*.egg-info', 'STEERING.md'))
            child = dict(environment, PXR_WORK_THREAD_LIMIT=str(threads))
            child['PXR_PLUGINPATH_NAME'] = os.pathsep.join([
                child['CORE_PLUGIN_DIR'], str(target / 'usdAecoPlan'),
                str(target / 'usdAecoPlanValidators')])
            profile = args.output.with_suffix(f'.{threads}.prof')
            command = [sys.executable]
            if args.profile:
                command += ['-m', 'cProfile', '-o', str(profile)]
            command += ['examples/datacentre/run.py']
            start = time.perf_counter()
            with args.output.with_suffix(f'.{threads}.log').open('w') as log:
                subprocess.run(command, cwd=target, env=child, stdout=log,
                               stderr=subprocess.STDOUT, timeout=budget, check=True)
            elapsed = time.perf_counter() - start
            example = target / 'examples/datacentre'
            manifest = json.loads((example / 'out/manifest.json').read_text())
            if manifest['source']['mode'] != 'pinned' or manifest['budgetSeconds'] != budget:
                raise ValueError('benchmark must reproduce the declared pinned example')
            if len(manifest['renders']) != 28:
                raise ValueError('fresh manifest must inventory both complete render sequences')
            committed = ROOT / 'examples/datacentre'
            unchanged = ['findings.json']
            if (example / 'out/findings.json').read_bytes() != (committed / 'expected/findings.json').read_bytes():
                raise ValueError('fresh findings changed')
            for path in sorted((committed / 'result').rglob('*')):
                if not path.is_file() or path.suffix in ('.png', '.usdc'):
                    continue
                relative = path.relative_to(committed)
                if path.read_bytes() != (example / 'out' / relative).read_bytes():
                    raise ValueError('fresh result changed: ' + relative.as_posix())
                unchanged.append(relative.as_posix())
            crate = Path('result/example.usdc')
            if normalized_layer(committed / crate) != normalized_layer(example / 'out' / crate):
                raise ValueError('fresh normalized crate changed')
            for key in ('A', 'B'):
                if (example / 'out' / (key + '.gantt.svg')).read_bytes() != (committed / 'renders' / (key + '.gantt.svg')).read_bytes():
                    raise ValueError('fresh Gantt changed: ' + key)
                unchanged.append('renders/' + key + '.gantt.svg')
            record = dict(threads=threads, seconds=round(elapsed, 3), profiled=args.profile,
                          renderSamples=8, budgetSeconds=budget, withinBudget=elapsed <= budget,
                          byteIdenticalFiles=unchanged, normalizedCrateEqual=True,
                          crateBytesEqual=(committed / crate).read_bytes() == (example / 'out' / crate).read_bytes(),
                          findingsSha256=manifest['actual_findings_sha256'],
                          resultFiles=manifest['result']['files'],
                          renderCount=len(manifest['renders']))
            record['ganttSha256'] = {key: hashlib.sha256((example / 'out' / (key + '.gantt.svg')).read_bytes()).hexdigest()
                                    for key in ('A', 'B')}
            if args.profile:
                stats = pstats.Stats(str(profile))
                record['profile'] = [dict(file=Path(file).name, function=function, calls=nc,
                                          ownSeconds=round(tt, 3), cumulativeSeconds=round(ct, 3))
                                     for (file, line, function), (cc, nc, tt, ct, callers)
                                     in sorted(stats.stats.items(), key=lambda item: item[1][3], reverse=True)[:20]]
            records.append(record)
            args.output.write_text(json.dumps(records, indent=2, sort_keys=True) + '\n')
            print(f'== stage: measured {elapsed:.3f}s / budget {budget}s', flush=True)
    return int(any(not record['withinBudget'] for record in records))


if __name__ == '__main__':
    raise SystemExit(main())
