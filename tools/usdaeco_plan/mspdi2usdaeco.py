"""MSPDI front end: standard-library XML and OutlineLevel work breakdown."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from .model import Activity, Programme, finite, iso

NS = "http://schemas.microsoft.com/project"


def child(node, name, default=""):
    found = node.find("{" + NS + "}" + name)
    return (found.text or "").strip() if found is not None else default


def parse(path, *, programme_id=None):
    root = ET.parse(path).getroot()
    if root.tag != "{" + NS + "}Project":
        raise ValueError("expected an MSPDI Project document")
    minutes = finite(child(root, "MinutesPerDay", "480"), "MinutesPerDay")
    if minutes <= 0:
        raise ValueError("MinutesPerDay must be positive")
    rows = root.findall("{" + NS + "}Tasks/{" + NS + "}Task")
    activities, by_uid, pending, stack, names = [], {}, [], [], {}
    summary_start = summary_finish = ""
    for row in rows:
        if child(row, "IsNull") == "1":
            continue
        uid = child(row, "UID")
        level = int(child(row, "OutlineLevel", "0"))
        if level == 0:
            summary_start, summary_finish = child(row, "Start"), child(row, "Finish")
            continue
        while stack and stack[-1][0] >= level:
            stack.pop()
        if level != (stack[-1][0] + 1 if stack else 1):
            raise ValueError("OutlineLevel skips a parent")
        extended = {child(e, "FieldID"): child(e, "Value") for e in row.findall("{" + NS + "}ExtendedAttribute")}
        if child(row, "Summary") == "1":
            part = child(row, "WBS").split(".")[-1] or child(row, "Name") or uid
            stack.append((level, part))
            names[tuple(p for _, p in stack)] = child(row, "Name")
            continue
        key = extended.get("188743734") or uid
        if uid in by_uid:
            raise ValueError("duplicate MSPDI task UID")
        by_uid[uid] = key
        dates = {"plannedStart": iso(child(row, "Start")), "plannedFinish": iso(child(row, "Finish")),
                 "actualStart": iso(child(row, "ActualStart")), "actualFinish": iso(child(row, "ActualFinish"))}
        baselines = row.findall("{" + NS + "}Baseline")
        baseline = next((b for b in baselines if child(b, "Number", "0") == "0"), None)
        if baseline is not None:
            dates.update(baselineStart=iso(child(baseline, "Start")), baselineFinish=iso(child(baseline, "Finish")))
        activity = Activity(key, child(row, "Name"), tuple(p for _, p in stack),
                            extended.get("188743737") or "construction", child(row, "Milestone") == "1",
                            dates, finite(child(row, "PercentComplete", "0"), "percentComplete"),
                            scope=json.loads(extended.get("188743731") or "[]"))
        activities.append(activity)
        pending.append((activity, row.findall("{" + NS + "}PredecessorLink")))
    for activity, links in pending:
        for edge in links:
            uid, code = child(edge, "PredecessorUID"), child(edge, "Type", "1")
            if uid not in by_uid or code not in {"0", "1", "2", "3"}:
                raise ValueError("unresolved MSPDI predecessor or unknown Type")
            # LinkLag is tenths of minutes; preserve every row, including repeats.
            lag = finite(child(edge, "LinkLag", "0"), "LinkLag") / (10 * minutes)
            activity.links.append((by_uid[uid], lag, {"0": "FF", "1": "FS", "2": "SF", "3": "SS"}[code]))
    starts = [a.dates["plannedStart"] for a in activities if a.dates["plannedStart"]]
    finishes = [a.dates["plannedFinish"] for a in activities if a.dates["plannedFinish"]]
    start = iso(child(root, "StartDate") or summary_start) or min(starts, default="")
    finish_source = child(root, "FinishDate") or summary_finish
    finish = iso(finish_source) or max(finishes, default="")
    programme = Programme(programme_id or Path(path).stem, child(root, "Name"), start, start, finish,
                          "mspdi", iso(child(root, "StatusDate")), activities=activities, wbs_names=names,
                          boundary_source="source" if finish_source else "activityEnvelope")
    programme.validate()
    return programme


def main(argv=None):
    from .cli import import_main
    return import_main("mspdi", argv)


if __name__ == "__main__":
    raise SystemExit(main())
