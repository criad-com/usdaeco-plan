"""Small clean programme used before each seeded-defect mutation."""
from pxr import Usd, UsdGeom, Sdf
from usdaeco_plan.model import attr, members, identity, FALLBACKS


def clean_stage():
    stage = Usd.Stage.CreateInMemory()
    world = stage.DefinePrim('/World', 'Xform')
    stage.SetDefaultPrim(world)
    UsdGeom.SetStageMetersPerUnit(stage, 1)
    UsdGeom.SetStageUpAxis(stage, 'Z')
    stage.SetMetadata('fallbackPrimTypes', FALLBACKS)
    for name in ('Work', 'Ceiling', 'Temp'):
        prim = stage.DefinePrim('/World/' + name, 'Xform')
        prim.ApplyAPI('AecoElementAPI')
        attr(prim, 'aeco:id', identity('fixture', name))
        attr(prim, 'aeco:phase', 'temporary' if name == 'Temp' else 'proposed', Sdf.ValueTypeNames.Token)
    for name in ('Void', 'Office', 'Corridor'):
        stage.DefinePrim('/World/' + name, 'Xform')
    programme = stage.DefinePrim('/Programme', 'AecoProgramme')
    attr(programme, 'aeco:id', identity('fixture', 'programme'))
    for name, val in [('epoch', '2027-03-01'), ('plannedStart', '2027-03-01'), ('plannedFinish', '2027-05-24')]:
        attr(programme, 'aeco:plan:' + name, val)
    attr(programme, 'aeco:plan:timeCodesPerDay', 1, Sdf.ValueTypeNames.Double)
    rows = [('Build', 'installation', '03-15', '03-28', 'Work'),
            ('Inspect', 'attendance', '03-29', '03-30', 'Void'),
            ('Close', 'construction', '04-05', '04-11', 'Ceiling'),
            ('Install', 'installation', '03-15', '03-15', 'Temp'),
            ('Park', 'logistic', '03-15', '04-01', 'Temp'),
            ('Remove', 'removal', '04-01', '04-01', 'Temp')]
    for name, kind, start, finish, target in rows:
        prim = stage.DefinePrim('/Programme/' + name, 'AecoActivity')
        prim.ApplyAPI('AecoScheduleAPI')
        prim.ApplyAPI('AecoWorkspaceAPI')
        prim.SetDisplayName(name)
        attr(prim, 'aeco:id', identity('fixture', name))
        attr(prim, 'aeco:plan:taskType', kind, Sdf.ValueTypeNames.Token)
        attr(prim, 'aeco:schedule:plannedStart', '2027-' + start)
        attr(prim, 'aeco:schedule:plannedFinish', '2027-' + finish)
        members(prim, [Sdf.Path('/World/' + target)])
    for name in ('Build', 'Inspect'):
        stage.GetPrimAtPath('/Programme/' + name).CreateRelationship('aeco:workspace:requiresAccess').SetTargets(['/World/Void'])
    close = stage.GetPrimAtPath('/Programme/Close')
    close.CreateRelationship('aeco:workspace:encloses').SetTargets(['/World/Void'])
    close.CreateRelationship('aeco:workspace:accessVia').SetTargets(['/World/Corridor'])
    links(stage, 'Close', ['Inspect'])
    links(stage, 'Inspect', ['Build'])
    stage.GetPrimAtPath('/Programme/Park').CreateRelationship('aeco:workspace:occupies').SetTargets(['/World/Office'])
    members(programme, [Sdf.Path('/World/' + n) for n in ('Work', 'Ceiling', 'Temp', 'Void')])
    return stage


def links(stage, name, predecessors):
    prim = stage.GetPrimAtPath('/Programme/' + name)
    attr(prim, 'aeco:plan:predecessorIds', [identity('fixture', p) for p in predecessors], Sdf.ValueTypeNames.StringArray)
    attr(prim, 'aeco:plan:lagDays', [0.] * len(predecessors), Sdf.ValueTypeNames.DoubleArray)
    attr(prim, 'aeco:plan:linkType', ['FS'] * len(predecessors), Sdf.ValueTypeNames.TokenArray)
