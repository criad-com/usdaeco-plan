"""Study namespaces on the pinned full data centre and through public tools."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
from pxr import Sdf, Usd, UsdGeom

from usdaeco_plan import mspdi2usdaeco, xer2usdaeco
from usdaeco_plan.cli import main
from usdaeco_plan.derive import derive, lookahead, predecessors
from usdaeco_plan.example import hook
from usdaeco_plan.model import bind, normalize_layer, study_root_path, write_programme
from usdaeco_plan.validation import activities, findings, select_programme

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / 'examples/datacentre/inputs'


@pytest.fixture(scope='module')
def full_source():
    path = Path(os.environ.get('AECO_PLAN_TEST_STAGE', ROOT.parent /
                'usdaeco-datacentre-0.5.2/dist/full/dc.usda')).resolve()
    if not path.is_file():
        pytest.skip('set AECO_PLAN_TEST_STAGE to the pinned v0.5.2 dist/full/dc.usda')
    return path


def compose(source, *layers):
    stage = Usd.Stage.CreateInMemory()
    stage.GetRootLayer().subLayerPaths = [str(p) for p in layers] + [str(source)]
    assert not stage.GetCompositionErrors()
    return stage


@pytest.mark.parametrize('invalid', ['', 'Studies/plan', '/Studies.plan', '/Studies{issue=A}', '/Studies/../plan'])
def test_invalid_study_root(invalid):
    with pytest.raises(ValueError, match='absolute prim path'):
        study_root_path(invalid)


def test_explicit_root_overrides_environment(tmp_path, monkeypatch):
    monkeypatch.setenv('AECO_STUDY_ROOT', '/Studies/environment')
    programme = xer2usdaeco.parse(INPUTS / 'B.xer')
    bind(programme, INPUTS / 'B.scope.json')
    for root, expected in [(None, '/Studies/environment/Programme'), ('/', '/Programme')]:
        path = tmp_path / ('environment.usda' if root is None else 'legacy.usda')
        write_programme(programme, path, study_root=root)
        stage = Usd.Stage.Open(str(path))
        assert str(select_programme(stage).GetPath()) == expected
        assert stage.GetDefaultPrim().GetPath() == Sdf.Path(expected).GetPrefixes()[0]
        missing = select_programme(stage).GetRelationship('collection:members:includes').GetTargets()
        # Missing aliases stay visible as dangling targets in the same study namespace.
        assert missing and all(p.HasPrefix(Sdf.Path(expected).GetParentPath().AppendChild('Unresolved')) for p in missing)


@pytest.mark.parametrize('root', ['/', '/Studies/plan', '/Studies/review/phase'])
def test_import_validation_and_4d_on_full_source(full_source, tmp_path, monkeypatch, root):
    source = Usd.Stage.Open(str(full_source))
    source_before = source.GetRootLayer().ExportToString()
    project = source.GetDefaultPrim().GetPath()
    catalog = project.AppendChild('_TypeCatalog')
    assert source.GetPrimAtPath(catalog).IsAbstract()
    monkeypatch.setenv('AECO_STUDY_ROOT', root)
    programme_path = Sdf.Path(root).AppendChild('Programme')
    for key in ('A', 'B'):
        outputs = []
        for module, extension in [(xer2usdaeco, 'xer'), (mspdi2usdaeco, 'xml')]:
            programme = module.parse(INPUTS / f'{key}.{extension}', programme_id=key)
            bind(programme, INPUTS / f'{key}.scope.json', INPUTS / f'{key}.workspace.json')
            output = tmp_path / f'{key}.{extension}.usda'
            write_programme(programme, output, stage=source)
            outputs.append(output)
        assert normalize_layer(outputs[0]) == normalize_layer(outputs[1])
        driver = Usd.Stage.Open(str(outputs[0]))
        assert driver.GetDefaultPrim().GetPath() == programme_path.GetPrefixes()[0]
        for path in Sdf.Path(root).GetPrefixes():
            assert driver.GetPrimAtPath(path).GetTypeName() == 'Scope'
        stage = compose(full_source, outputs[0])
        assert select_programme(stage).GetPath() == programme_path
        assert not stage.GetPrimAtPath('/_TypeCatalog')
        assert stage.GetPrimAtPath(catalog).IsAbstract()
        assert {p.GetPath() for p in stage.GetPseudoRoot().GetAllChildren()} == {project, programme_path.GetPrefixes()[0]}
        expected = {'AccessAfterEnclosure', 'EnclosureBeforeInspection', 'WorkspaceOccupied'} if key == 'A' else set()
        actual = findings(stage)
        assert {f['name'] for f in actual} == expected
        assert all(Sdf.Path(p).HasPrefix(project) or Sdf.Path(p).HasPrefix(programme_path)
                   for f in actual for p in f['paths'])
        for activity in activities(select_programme(stage)):
            for relationship in activity.GetRelationships():
                assert all(stage.GetPrimAtPath(p) for p in relationship.GetTargets())
        # Readers follow the authored data even when the setting changes later.
        with monkeypatch.context() as reader_env:
            reader_env.setenv('AECO_STUDY_ROOT', '/Studies/unrelated')
            rows = lookahead(stage, 12)
            assert rows and all(Sdf.Path(row['path']).HasPrefix(programme_path) for row in rows)
            graph_path, fourd_path = tmp_path / 'predecessors.usda', tmp_path / '4d.usda'
            graph = predecessors(stage, graph_path)
            assert graph['linkInstances'] == (9 if key == 'A' else 10)
            graph_layer = Sdf.Layer.FindOrOpen(str(graph_path))
            graph_layer.Reload()
            for activity in activities(select_programme(stage)):
                rel = graph_layer.GetRelationshipAtPath(activity.GetPath().AppendProperty('aeco:plan:predecessors'))
                assert rel is not None
                assert all(p.HasPrefix(programme_path) and stage.GetPrimAtPath(p) for p in rel.targetPathList.explicitItems)
            result = derive(stage, fourd_path)
            assert result['targets'] == 23
            assert all(Sdf.Path(p).HasPrefix(project) for p in result['transitions'])
    assert source.GetRootLayer().ExportToString() == source_before


@pytest.mark.parametrize('command,extension', [('xer', 'xer'), ('mspdi', 'xml')])
def test_cli_roundtrip_discovers_root(full_source, tmp_path, monkeypatch, capsys, command, extension):
    driver = tmp_path / 'programme.usda'
    monkeypatch.setenv('AECO_STUDY_ROOT', '/Studies/ignored')
    assert main([command, str(INPUTS / f'B.{extension}'), '--out', str(driver),
                 '--programme-id', 'B', '--stage', str(full_source),
                 '--scope', str(INPUTS / 'B.scope.json'), '--workspace', str(INPUTS / 'B.workspace.json'),
                 '--study-root', '/Studies/cli']) == 0
    stage = compose(full_source, driver)
    assert str(select_programme(stage).GetPath()) == '/Studies/cli/Programme'
    composed = tmp_path / 'composed.usda'
    stage.GetRootLayer().Export(str(composed))
    capsys.readouterr()
    assert main(['lookahead', '12', str(composed)]) == 0
    rows = json.loads(capsys.readouterr().out)
    assert rows and all(row['path'].startswith('/Studies/cli/Programme/') for row in rows)
    assert main(['validate', str(composed)]) == 0
    assert json.loads(capsys.readouterr().out) == []
    assert main(['derive', str(composed), '--out', str(tmp_path / '4d.usda')]) == 0
    assert json.loads(capsys.readouterr().out)['targets'] == 23
    normalized = tmp_path / 'normalized.usda'
    assert main(['normalize', str(driver), '--out', str(normalized)]) == 0
    assert str(select_programme(Usd.Stage.Open(str(normalized))).GetPath()) == '/Studies/cli/Programme'


def test_hook_and_relocated_stock_playback(full_source, tmp_path, monkeypatch):
    monkeypatch.setenv('AECO_STUDY_ROOT', '/Studies/plan')
    monkeypatch.setenv('AECO_DATACENTRE_STAGE', str(full_source))
    kit = Path(os.environ.get('TOOLCHAIN_DIR', ROOT.parent / 'usdaeco-toolchain'))
    monkeypatch.syspath_prepend(str(kit / 'tools'))
    result = tmp_path / 'result'
    out = result / 'layers/out'
    out.mkdir(parents=True)
    inputs = out.parent / 'inputs'
    shutil.copytree(INPUTS, inputs, ignore=shutil.ignore_patterns('source'))
    # Suite input cameras have their own namespace outside Studies.
    cameras = Usd.Stage.CreateInMemory()
    cameras.DefinePrim('/Renders/plan', 'Scope')
    camera_source = Sdf.Layer.FindOrOpen(str(INPUTS / 'cameras.usda'))
    Sdf.CopySpec(camera_source, '/Renders/B', cameras.GetRootLayer(), '/Renders/plan/B')
    cameras.GetRootLayer().Export(str(inputs / 'cameras.usda'))
    source = Usd.Stage.Open(str(full_source))
    stage = Usd.Stage.CreateNew(str(out / 'example.usda'))
    stage.GetRootLayer().subLayerPaths = ['../inputs/cameras.usda', str(full_source)]
    stage.SetDefaultPrim(stage.GetPrimAtPath(source.GetDefaultPrim().GetPath()))
    for key in ('upAxis', 'metersPerUnit', 'fallbackPrimTypes', 'timeCodesPerSecond'):
        stage.SetMetadata(key, source.GetMetadata(key))
    evidence = hook(stage, out, render_a=False)
    assert {f['name'] for f in evidence if f.get('programme') == 'A' and 'severity' in f} == {
        'AccessAfterEnclosure', 'EnclosureBeforeInspection', 'WorkspaceOccupied'}
    assert not [f for f in evidence if f.get('programme') == 'B' and 'severity' in f]
    assert stage.GetPrimAtPath('/Studies').GetTypeName() == 'Scope'
    assert select_programme(stage).GetPath() == Sdf.Path('/Studies/plan/Programme')
    assert {p.GetName() for p in stage.GetPseudoRoot().GetAllChildren()} == {
        source.GetDefaultPrim().GetName(), 'Studies', 'Renders'}
    assert {str(p.GetPath()) for p in stage.Traverse() if p.IsA(UsdGeom.Camera)} == {'/Renders/plan/B'}
    assert not stage.GetPrimAtPath('/_TypeCatalog')
    for key in ('A', 'B'):
        assert (out / f'{key}.gantt.svg').read_bytes() == (ROOT / f'examples/datacentre/renders/{key}.gantt.svg').read_bytes()
        assert Sdf.Layer.FindOrOpen(str(out / key / 'programme.usda')).defaultPrim == 'Studies'
    stage.Export(str(result / 'example.usdc'))
    # Only the self-contained crate and portable A stack are used by the probe.
    relocated = tmp_path / 'relocated/result'
    shutil.copytree(result, relocated)
    environment = {k: v for k, v in os.environ.items() if k not in {
        'PYTHONPATH', 'PXR_PLUGINPATH_NAME', 'PXR_AR_DEFAULT_SEARCH_PATH', 'AECO_STUDY_ROOT'}}
    probe = subprocess.run([sys.executable, '-I', str(ROOT / 'testenv/playback_probe.py'),
                            str(relocated), str(inputs)], env=environment, capture_output=True, text=True)
    assert probe.returncode == 0, probe.stderr
    assert sum(row['checks'] for row in json.loads(probe.stdout).values()) == 552
