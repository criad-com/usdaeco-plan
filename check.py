#!/usr/bin/env python3
"""Run pinned acceptance checks and print N checks, M failed, K not run."""
from collections import Counter
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
CORE = Path(os.environ.get('CORE_DIR', ROOT.parent / 'usdaeco-core')).resolve()
KIT = Path(os.environ.get('TOOLCHAIN_DIR', ROOT.parent / 'usdaeco-toolchain')).resolve()
CORE_PLUGIN = Path(os.environ.get('CORE_PLUGIN_DIR', CORE / 'out/plugins/usdAeco/resources')).resolve()
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT), str(KIT / 'tools')]
from usdaeco_check import Report, registry_probe, can_apply, plugin_requires, validate_examples, link_check
from usdaeco_check.structure import check_structure
from usdaeco_check.example import check_example
from usdaeco_check.validation import run


def main():
    # Use the example's preview quality for the independent vanilla probes too.
    os.environ.setdefault('HDEMBREE_SAMPLES_TO_CONVERGENCE', '8')
    report = Report()
    from pxr import Plug, Sdf, Usd, UsdValidation
    print('== stage: load core and plan plugins', flush=True)
    report.add(plugin_requires([CORE_PLUGIN, ROOT / 'usdAecoPlan']))
    Plug.Registry().RegisterPlugins(str(CORE / 'usdAecoValidators'))
    Plug.Registry().RegisterPlugins(str(ROOT / 'usdAecoPlanValidators'))
    # Deliberately do not repair sys.path: the caller must make core importable.
    try:
        importlib.import_module('usdAecoValidators')
    except ImportError:
        report.check('core validators loaded', False, 'usdAecoValidators is not importable; set PYTHONPATH to the core checkout and this repository')
        return report.finish()
    registry = UsdValidation.ValidationRegistry()
    core_metadata = registry.GetValidatorMetadataForKeyword('UsdAecoValidators')
    plan_metadata = registry.GetValidatorMetadataForKeyword('UsdAecoPlanValidators')
    report.check('core validators loaded', len(core_metadata) == 8 and all(registry.GetOrLoadValidatorByName(m.name) for m in core_metadata), '8 required registrations')
    report.check('planning validator listing', len(plan_metadata) == 8 and all(registry.GetOrLoadValidatorByName(m.name) for m in plan_metadata), '8 required registrations')
    report.add(registry_probe(['AecoScheduleAPI', 'AecoWorkspaceAPI'], ['AecoProgramme', 'AecoActivity', 'AecoMilestone']))
    report.add(can_apply([(name, api, allowed) for api in ('AecoScheduleAPI', 'AecoWorkspaceAPI')
                          for name, allowed in [('AecoActivity', True), ('AecoMilestone', True), ('Xform', False), ('AecoProgramme', False)]]))
    definition = Usd.SchemaRegistry().FindConcretePrimDefinition('AecoActivity')
    report.check('derived predecessor metadata', definition.GetPropertyMetadata('aeco:plan:predecessors', 'aecoDerived') is True)
    seed = Usd.Stage.CreateInMemory()
    for name in ('One', 'Two'):
        p = seed.DefinePrim('/' + name, 'Xform')
        p.ApplyAPI('AecoElementAPI')
        p.GetAttribute('aeco:id').Set('67c6d506-9e6c-5488-af06-e1194ff7cfee')
    report.check('core duplicate-identity defect caught', any(e.GetName() == 'duplicateId' for e in run(seed, ['UsdAecoValidators'])))
    print('== stage: structure', flush=True)
    for result in check_structure(ROOT, deps=[CORE_PLUGIN]):
        report.add(result)
    report.add(validate_examples(ROOT / 'usdAecoPlan/examples', validators=[lambda s: run(s, ['UsdAecoValidators', 'UsdAecoPlanValidators'])]))
    print('== stage: pinned example', flush=True)
    example = ROOT / 'examples/datacentre'
    if not report.run('example harness', check_example, example):
        return report.finish()
    evidence = json.loads((example / 'out/findings.json').read_text())
    for key, wanted in [('A', {'AccessAfterEnclosure': 'error', 'WorkspaceOccupied': 'error', 'EnclosureBeforeInspection': 'warn'}), ('B', {})]:
        actual = {r['name']: r['severity'] for r in evidence if r.get('programme') == key and 'severity' in r}
        report.check('programme ' + key + ' findings', actual == wanted, json.dumps(actual, sort_keys=True))
        stage = Usd.Stage.Open(str(example / ('result/layers/out/A/play.usda' if key == 'A' else 'result/example.usdc')))
        core_errors = run(stage, ['UsdAecoValidators'])
        report.check('programme ' + key + ' core validation', all(e.GetType() != UsdValidation.ValidationErrorType.Error for e in core_errors),
                     str(len(core_errors)) + ' source warnings, 0 errors' if all(e.GetType() != UsdValidation.ValidationErrorType.Error for e in core_errors) else 'core errors found')
    from usdaeco_plan.model import normalize_layer
    for key in ('A', 'B'):
        folder = example / 'out' / key
        report.check('XER equals MSPDI ' + key, normalize_layer(folder / 'programme.usda') == normalize_layer(folder / 'mspdi.usda'), 'byte-identical normalized layer text')
        report.check('Gantt prim-derived SVG ' + key, (example / ('out/' + key + '.gantt.svg')).read_bytes() == (example / ('renders/' + key + '.gantt.svg')).read_bytes())
    print('== stage: relocated stock-USD playback', flush=True)
    environment = {k: v for k, v in os.environ.items() if k not in ('PYTHONPATH', 'PXR_PLUGINPATH_NAME', 'PXR_AR_DEFAULT_SEARCH_PATH')}
    with tempfile.TemporaryDirectory(prefix='plan-playback-') as directory:
        target = Path(directory) / 'result'
        shutil.copytree(example / 'result', target)
        completed = subprocess.run([sys.executable, '-I', str(ROOT / 'testenv/playback_probe.py'), str(target), str(example / 'inputs')],
                                   env=environment, capture_output=True, text=True)
    report.check('stock USD visibility frame-count', completed.returncode == 0, completed.stdout.strip() if completed.returncode == 0 else completed.stderr[-1200:])
    (ROOT / 'out').mkdir(exist_ok=True)
    if completed.returncode == 0:
        (ROOT / 'out/playback.json').write_text(completed.stdout)
    expected_renders = {f'{key}.{frame}.png' for key in ('A', 'B') for frame in range(0, 78, 7)}
    expected_renders |= {key + suffix for key in ('A', 'B') for suffix in ('.sheet.png', '.gif')}
    committed_renders = {p.name for p in (example / 'renders').iterdir() if p.suffix in ('.png', '.gif')}
    fresh_renders = [Path(r['path']).name for r in json.loads((example / 'out/manifest.json').read_text())['renders']]
    report.check('weekly render inventory', committed_renders == set(fresh_renders) == expected_renders
                 and len(fresh_renders) == 28, '24 PNG frames, 2 contact sheets, 2 GIFs in committed and fresh inventories')
    report.add(link_check(ROOT / 'docs'))
    report.not_run('private real-project XER', 'Private client data is excluded and was never read.')
    report.not_run('Nix dependency evaluation', 'One offline attempt recorded in docs/acceptance.md; unresolved inputs are not a pass.')
    return report.finish()


if __name__ == '__main__':
    raise SystemExit(main())
