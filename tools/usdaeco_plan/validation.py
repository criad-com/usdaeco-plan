"""Cross-prim planning checks over authored drivers, independent of derived views."""
from datetime import date
import math
from pxr import Sdf, Usd

WARNINGS = {"EnclosureBeforeInspection", "UnscheduledElement", "TemporaryWithoutRemoval"}


def value(prim, name, default=None):
    result = prim.GetAttribute(name).Get()
    return default if result is None else result


def targets(prim, name):
    return set(prim.GetRelationship(name).GetTargets())


def programmes(stage):
    return [p for p in stage.Traverse() if p.GetTypeName() == "AecoProgramme"]


def select_programme(stage, path=None):
    """Find a programme in the composed data, independent of authoring settings."""
    choices = [p for p in programmes(stage) if path is None or p.GetPath() == Sdf.Path(path)]
    if len(choices) != 1:
        raise ValueError("select exactly one programme")
    return choices[0]


def activities(programme):
    return [p for p in Usd.PrimRange(programme)
            if p.GetTypeName() in {"AecoActivity", "AecoMilestone"} and p.HasAPI("AecoScheduleAPI")]


def scope(prim):
    collection = Usd.CollectionAPI(prim, "members")
    if not collection:
        return set()
    return set(Usd.CollectionAPI.ComputeIncludedPaths(collection.ComputeMembershipQuery(), prim.GetStage()))


def window(prim):
    try:
        start = date.fromisoformat(value(prim, "aeco:schedule:plannedStart", ""))
        finish = date.fromisoformat(value(prim, "aeco:schedule:plannedFinish", ""))
        return (start, finish) if start <= finish else None
    except ValueError:
        return None


def overlap(a, b):
    return a and b and max(a[0], b[0]) <= min(a[1], b[1])


def _access(stage, programme, acts):
    hits = []
    for closer in acts:
        closed = targets(closer, "aeco:workspace:encloses")
        when = window(closer)
        for worker in acts:
            shared = closed & targets(worker, "aeco:workspace:requiresAccess")
            work = window(worker)
            if worker != closer and shared and when and work and work[1] > when[0]:
                hits.append(([worker.GetPath(), closer.GetPath(), *sorted(shared)],
                             "Required access extends after enclosure starts."))
    return hits


def _workspace(stage, programme, acts):
    hits = []
    for occupier in acts:
        occupied = targets(occupier, "aeco:workspace:occupies")
        for worker in acts:
            access = targets(worker, "aeco:workspace:requiresAccess") | targets(worker, "aeco:workspace:accessVia")
            shared = occupied & access
            if worker != occupier and shared and overlap(window(worker), window(occupier)):
                hits.append(([worker.GetPath(), occupier.GetPath(), *sorted(shared)],
                             "Required workspace overlaps an occupancy interval."))
    return hits


def _inspection(stage, programme, acts):
    hits = []
    for closer in acts:
        predecessors = set(value(closer, "aeco:plan:predecessorIds", []))
        for region in sorted(targets(closer, "aeco:workspace:encloses")):
            inspections = [a for a in acts if value(a, "aeco:plan:taskType") == "attendance" and region in scope(a)]
            qualifying = [a for a in inspections if value(a, "aeco:id") in predecessors
                          and window(a) and window(closer) and window(a)[1] <= window(closer)[0]]
            if not qualifying:
                hits.append(([closer.GetPath(), region, *[a.GetPath() for a in inspections]],
                             "Enclosure lacks a completed inspection predecessor over this region."))
    return hits


def _cycle(stage, programme, acts):
    by_id = {value(a, "aeco:id"): a for a in acts}
    graph = {key: set(value(a, "aeco:plan:predecessorIds", [])) & by_id.keys() for key, a in by_id.items()}
    # Iterative DFS handles large work breakdowns without Python recursion limits.
    color, cycles = {}, set()
    for origin in graph:
        if color.get(origin):
            continue
        stack, active = [(origin, iter(graph[origin]))], [origin]
        color[origin] = 1
        while stack:
            node, edges = stack[-1]
            child = next(edges, None)
            if child is None:
                color[node] = 2
                stack.pop()
                active.pop()
            elif color.get(child) == 1:
                cycles.update(active[active.index(child):])
            elif not color.get(child):
                color[child] = 1
                stack.append((child, iter(graph[child])))
                active.append(child)
    return [([by_id[k].GetPath() for k in sorted(cycles)], "Predecessor ids contain a directed cycle.")] if cycles else []


def _dangling(stage, programme, acts):
    hits = []
    for prim in [programme, *acts]:
        names = ["collection:members:includes", "collection:members:excludes"]
        names += ["aeco:workspace:" + n for n in ("requiresAccess", "encloses", "occupies", "accessVia")]
        for name in names:
            for path in sorted(targets(prim, name)):
                if path.IsPropertyPath() and path.name.startswith("collection:"):
                    valid = bool(stage.GetPropertyAtPath(path))
                else:
                    valid = bool(path.IsPrimPath() and stage.GetPrimAtPath(path))
                if not valid:
                    hits.append(([prim.GetPath(), path], "Scope or workspace target does not resolve: " + name))
    return hits


def _unscheduled(stage, programme, acts):
    scheduled = set().union(*(scope(a) for a in acts)) if acts else set()
    return [([path], "Programme member has no scheduled activity.") for path in sorted(scope(programme) - scheduled)
            if stage.GetPrimAtPath(path).HasAPI("AecoElementAPI")]


def _temporary(stage, programme, acts):
    removed = set().union(*(scope(a) for a in acts if value(a, "aeco:plan:taskType") == "removal" and window(a)))
    return [([path], "Temporary programme member lacks a dated removal activity.") for path in sorted(scope(programme) - removed)
            if value(stage.GetPrimAtPath(path), "aeco:phase") == "temporary"]


def _dates(stage, programme, acts):
    try:
        start = date.fromisoformat(value(programme, "aeco:plan:plannedStart", ""))
        finish = date.fromisoformat(value(programme, "aeco:plan:plannedFinish", ""))
        epoch = date.fromisoformat(value(programme, "aeco:plan:epoch", ""))
        rate = value(programme, "aeco:plan:timeCodesPerDay", 1)
        if start > finish or not math.isfinite(rate) or rate <= 0:
            raise ValueError("invalid programme range or clock")
    except (TypeError, ValueError):
        return [([programme.GetPath()], "Programme requires valid date bounds, epoch and a positive finite clock rate.")]
    hits = []
    for activity in acts:
        work = window(activity)
        if not work or work[0] < start or work[1] > finish:
            hits.append(([activity.GetPath()], "Planned dates are missing, reversed, invalid or outside programme bounds."))
    return hits


RULES = {"AccessAfterEnclosure": _access, "WorkspaceOccupied": _workspace,
         "EnclosureBeforeInspection": _inspection, "PredecessorCycle": _cycle,
         "DanglingScope": _dangling, "UnscheduledElement": _unscheduled,
         "TemporaryWithoutRemoval": _temporary, "DatesOutsideProgramme": _dates}


def findings(stage, rule=None):
    """One finding per rule and programme, retaining every affected site/pair."""
    result = []
    for programme in programmes(stage):
        acts = activities(programme)
        for name in [rule] if rule else RULES:
            hits = RULES[name](stage, programme, acts)
            if hits:
                result.append({"name": name, "severity": "warn" if name in WARNINGS else "error",
                               "programme": str(programme.GetPath()),
                               "paths": sorted({str(p) for paths, _ in hits for p in paths}),
                               "message": hits[0][1], "occurrences": len(hits)})
    return result
