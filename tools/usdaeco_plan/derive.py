"""Regenerable graph and stock-USD visibility; work dates remain authoritative."""
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from pxr import Sdf, Usd, UsdGeom
from .validation import activities, programmes, scope, select_programme, value, window


def predecessors(stage, output):
    layer = Sdf.Layer.CreateAnonymous("predecessors.usda")
    derived = Usd.Stage.Open(layer)
    count = instances = 0
    for programme in programmes(stage):
        acts = activities(programme)
        index = {value(a, "aeco:id"): a.GetPath() for a in acts}
        for activity in acts:
            ids = list(value(activity, "aeco:plan:predecessorIds", []))
            lags = list(value(activity, "aeco:plan:lagDays", []))
            kinds = list(value(activity, "aeco:plan:linkType", []))
            if len(ids) != len(lags) or len(ids) != len(kinds) or any(i not in index for i in ids):
                raise ValueError("invalid or unresolved predecessor arrays")
            targets = sorted({index[i] for i in ids})
            derived.OverridePrim(activity.GetPath()).CreateRelationship("aeco:plan:predecessors", custom=False).SetTargets(targets)
            instances += len(ids)
            count += len(targets)
    layer.customLayerData = {"aeco:plan:derived": True}
    layer.Export(str(output))
    return {"linkInstances": instances, "uniqueTargets": count}


def derive(stage, output, *, programme_path=None):
    programme = select_programme(stage, programme_path)
    epoch = date.fromisoformat(value(programme, "aeco:plan:epoch", ""))
    rate = float(value(programme, "aeco:plan:timeCodesPerDay", 1))
    from math import isfinite
    if not isfinite(rate) or rate <= 0:
        raise ValueError("timeCodesPerDay must be positive and finite")
    clock = lambda day: (day - epoch).days * rate
    events, initial, finishes = defaultdict(list), {}, []
    for activity in activities(programme):
        kind = value(activity, "aeco:plan:taskType", "construction")
        work = window(activity)
        if not work:
            raise ValueError("activity lacks a valid planned date window")
        finishes.append(work[1])
        if kind not in {"construction", "installation", "move", "demolition", "removal"}:
            continue
        start = date.fromisoformat(value(activity, "aeco:schedule:actualStart") or work[0].isoformat())
        visible = kind not in {"demolition", "removal"}
        for path in scope(activity):
            prim = stage.GetPrimAtPath(path)
            if not prim or not UsdGeom.Imageable(prim):
                raise ValueError("4D scope must resolve to imageable prims")
            initial[path] = value(prim, "aeco:phase") == "existing"
            events[path].append((clock(start), visible))
    if not events:
        raise ValueError("no scoped building or removal activities")
    first = min(0, min(tc for values in events.values() for tc, _ in values) - rate)
    last = max(clock(date.fromisoformat(value(programme, "aeco:plan:plannedFinish"))),
               max(tc for values in events.values() for tc, _ in values))
    layer = Sdf.Layer.CreateAnonymous("4d.usda")
    result = Usd.Stage.Open(layer)
    transitions = {}
    for path, values in sorted(events.items()):
        visibility = result.OverridePrim(path).CreateAttribute("visibility", Sdf.ValueTypeNames.Token, custom=False)
        visibility.SetMetadata("aecoDerived", True)
        visibility.Set("inherited")  # Default-time views show the complete design.
        current = initial[path]
        visibility.Set("inherited" if current else "invisible", first)
        changes = []
        # Removals precede installations at the same date; intervals are [install, remove).
        for tc, visible in sorted(set(values)):
            if visible != current:
                visibility.Set("inherited" if visible else "invisible", tc)
                changes.append(tc)
                current = visible
        transitions[str(path)] = changes
    # Layer fps must match its composition root; otherwise USD scales sublayer
    # time samples. Calendar-day mapping and playback seconds are distinct clocks.
    layer.startTimeCode, layer.endTimeCode = first, last
    layer.timeCodesPerSecond = stage.GetTimeCodesPerSecond()
    layer.customLayerData = {"aeco:plan:derived": True, "aeco:plan:epoch": epoch.isoformat(),
                             "aeco:plan:timeCodesPerDay": rate}
    layer.Export(str(output))
    return {"targets": len(events), "startTimeCode": first, "endTimeCode": last, "transitions": transitions}


def lookahead(stage, weeks, *, start=None, programme_path=None):
    if weeks <= 0:
        raise ValueError("weeks must be positive")
    programme = select_programme(stage, programme_path)
    first = date.fromisoformat(start or value(programme, "aeco:plan:dataDate") or value(programme, "aeco:plan:epoch"))
    last = first + timedelta(weeks=weeks)
    result = []
    for activity in activities(programme):
        work = window(activity)
        if work and work[0] < last and work[1] >= first:
            result.append({"id": value(activity, "aeco:id"), "name": activity.GetDisplayName(),
                           "path": str(activity.GetPath()), "start": work[0].isoformat(), "finish": work[1].isoformat()})
    return sorted(result, key=lambda row: (row["start"], row["id"]))
