"""Pinned pod example: two schedule issues, three finding categories, 24 frames."""
import json
import os
from pathlib import Path
from pxr import Gf, Sdf, Usd, UsdGeom
from . import xer2usdaeco, mspdi2usdaeco
from .model import bind, write_programme, normalize_layer, id_index, FALLBACKS
from .validation import activities, findings, scope, value
from .derive import derive, predecessors
from .gantt import draw

FRAMES = list(range(0, 78, 7))
SIZE = (800, 500)


def source_counts(stage):
    counts = dict.fromkeys(('elements', 'spaces', 'levels', 'meshes', 'ports'), 0)
    for prim in stage.Traverse():
        name = prim.GetTypeName()
        counts['elements'] += prim.HasAPI('AecoElementAPI')
        counts['spaces'] += name == 'AecoSpace'
        counts['levels'] += name == 'AecoLevel'
        counts['meshes'] += prim.IsA(UsdGeom.Mesh)
        counts['ports'] += name == 'AecoPort'
    return counts


def presentation(base, programme_stage, workspace, output, label):
    """Derived colours and placement; never edit or reparent source referents."""
    layer = Sdf.Layer.CreateAnonymous("presentation.usda")
    stage = Usd.Stage.Open(layer)
    stage.OverridePrim('/Renders/B').SetActive(label == 'B')
    if label == 'A':
        camera = UsdGeom.Camera.Define(stage, '/Renders/A')
        original = UsdGeom.Camera(base.GetPrimAtPath('/Renders/B'))
        camera.SetFromCamera(original.GetCamera())
    index = id_index(base)
    placements = json.loads(Path(workspace).read_text()).get('placements', {})
    # Explicitly restore A's source pose too: the archived A view overlays the B crate.
    for key in ('pod.wc.temp',):
        prim = base.GetPrimAtPath(index[key])
        matrix = UsdGeom.Xformable(prim).GetLocalTransformation()
        if key in placements:
            world = Gf.Vec3d(*placements[key]['pos'])
            parent = UsdGeom.XformCache().GetLocalToWorldTransform(prim.GetParent())
            matrix.SetTranslateOnly(parent.GetInverse().Transform(world))
        override = stage.OverridePrim(prim.GetPath())
        op = override.CreateAttribute('xformOp:transform', Sdf.ValueTypeNames.Matrix4d, custom=False)
        op.Set(matrix)
        op.SetMetadata('aecoDerived', True)
        override.CreateAttribute('xformOpOrder', Sdf.ValueTypeNames.TokenArray, custom=False).Set(['xformOp:transform'])
    colours = {}
    for activity in activities(programme_stage.GetPrimAtPath('/Programme')):
        kind = value(activity, 'aeco:plan:taskType')
        if kind in {'attendance', 'removal', 'logistic'}:
            continue
        for path in scope(activity):
            colours[path] = (0.23, 0.39, 0.60) if kind == 'construction' else (0.13, 0.62, 0.57)
    colours[index['pod.wc.temp']] = (0.93, 0.43, 0.16)
    for path, colour in sorted(colours.items()):
        referent = base.GetPrimAtPath(path)
        if not referent:
            continue
        for prim in Usd.PrimRange(referent):
            if prim.IsA(UsdGeom.Gprim):
                stage.OverridePrim(prim.GetPath()).CreateAttribute('primvars:displayColor', Sdf.ValueTypeNames.Color3fArray).Set([colour])
    layer.customLayerData = {'aeco:plan:derived': True}
    layer.Export(str(output))


def archive_play(stage, output):
    """A portable layer-selection root needs its own stage metadata in USD."""
    play = Sdf.Layer.CreateAnonymous('play.usda')
    play.subLayerPaths = ['4d.usda', 'predecessors.usda', 'presentation.usda', 'programme.usda', '../../../example.usdc']
    play.defaultPrim = stage.GetDefaultPrim().GetName()
    play.startTimeCode, play.endTimeCode = 0, 77
    for name in ('metersPerUnit', 'upAxis', 'timeCodesPerSecond', 'fallbackPrimTypes'):
        play.pseudoRoot.SetInfo(name, stage.GetMetadata(name))
    play.Export(str(output))


def hook(stage, out, *, render_a=True, render_records=None):
    from usdaeco_check.validation import run
    from usdaeco_render import render
    inputs = out.parent / 'inputs'
    source = Path(os.environ['AECO_DATACENTRE_ROOT']) / 'dist/pod'
    counts = source_counts(stage)
    manifest_counts = json.loads((source / 'dc.manifest.json').read_text())['counts']
    if counts != {key: manifest_counts[key] for key in counts}:
        raise ValueError('source census differs from pinned dc.manifest.json')
    result = [{'name': 'SourceCounts', 'counts': counts}]
    # Reuse the harness's composed building. A's opinions are removed before B
    # is imported, so neither programme inherits the other's placement or dates.
    root = stage.GetRootLayer()
    source_layers = list(root.subLayerPaths)
    stage.SetMetadata('fallbackPrimTypes', {**dict(stage.GetMetadata('fallbackPrimTypes')), **FALLBACKS})
    for key in ('A', 'B'):
        print('== stage: programme ' + key, flush=True)
        folder = out / key
        folder.mkdir()
        for module, extension, name in [(xer2usdaeco, 'xer', 'programme.usda'), (mspdi2usdaeco, 'xml', 'mspdi.usda')]:
            programme = module.parse(inputs / (key + '.' + extension), programme_id=key)
            bind(programme, inputs / (key + '.scope.json'), inputs / (key + '.workspace.json'))
            write_programme(programme, folder / name, stage=stage)
        if normalize_layer(folder / 'programme.usda') != normalize_layer(folder / 'mspdi.usda'):
            raise ValueError('XER and MSPDI normalized driver layers differ')
        root.subLayerPaths = [key + '/programme.usda', *source_layers]
        graph = predecessors(stage, folder / 'predecessors.usda')
        fourd = derive(stage, folder / '4d.usda')
        presentation(stage, stage, inputs / (key + '.workspace.json'), folder / 'presentation.usda', key)
        root.subLayerPaths[:0] = [key + '/' + n for n in ('4d.usda', 'predecessors.usda', 'presentation.usda')]
        stage.SetStartTimeCode(0)
        stage.SetEndTimeCode(77)
        root.Save()
        found = findings(stage)
        registered = run(stage, ['UsdAecoPlanValidators'])
        if sorted(e.GetName() for e in registered) != sorted(f['name'] for f in found):
            raise ValueError('registered validation and finding report disagree')
        result.extend({**f, 'programme': key} for f in found)
        expected_names = ['AccessAfterEnclosure', 'EnclosureBeforeInspection', 'WorkspaceOccupied'] if key == 'A' else []
        if sorted(f['name'] for f in found) != expected_names:
            raise ValueError('unexpected planning finding categories')
        result.append({'name': 'ProgrammeEvidence', 'programme': key, 'activities': len(programme.activities),
                       **graph, 'normalizedEqual': True, 'visibilityTargets': fourd['targets']})
        (folder / 'visibility.json').write_text(json.dumps(fourd, indent=2, sort_keys=True) + '\n')
        draw(stage.GetPrimAtPath('/Programme'), out / (key + '.gantt.svg'), key)
        if key == 'A' and render_a:
            print('== stage: render programme A, 12 weeks', flush=True)
            # The renderer derives the sheet/GIF from these saved frames.
            records = render(root.realPath, output=out / 'renders', size=SIZE, frames=FRAMES, views=['A'])
            if render_records is not None:
                render_records.extend(records)
        # The archived view overlays the shared self-contained crate, with no
        # dependency on the original source paths. B's opinions are fully replaced.
        archive_play(stage, folder / 'play.usda')
        if key == 'A':
            root.subLayerPaths = source_layers
    return result
