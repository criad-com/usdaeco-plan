"""P6 XER tables to programme drivers; ordered multiedges are lossless."""
from pathlib import Path
from .model import Activity, Programme, finite, iso


def tables(path):
    result, current, fields = {}, None, None
    data = Path(path).read_bytes()
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = data.decode("cp1252")
    for line in text.splitlines():
        cells = line.split("\t")
        if cells[0] == "%T":
            current, fields = cells[1], None
            result.setdefault(current, [])
        elif cells[0] == "%F":
            fields = cells[1:]
        elif cells[0] == "%R":
            if current is None or fields is None or len(cells) - 1 != len(fields):
                raise ValueError("malformed XER table row")
            result[current].append(dict(zip(fields, cells[1:])))
    return result


def parse(path, *, programme_id=None, project_id=None):
    data = tables(path)
    projects = [p for p in data.get("PROJECT", []) if p.get("project_flag", "Y") == "Y"
                and (project_id is None or p["proj_id"] == str(project_id))]
    if len(projects) != 1:
        raise ValueError("select exactly one XER project with --project-id")
    project = projects[0]
    rows = [t for t in data.get("TASK", []) if t["proj_id"] == project["proj_id"]]
    task_ids = {t["task_id"]: t["task_code"] for t in rows}
    if len(task_ids) != len(rows):
        raise ValueError("duplicate XER task id")
    wbs = {w["wbs_id"]: w for w in data.get("PROJWBS", []) if w["proj_id"] == project["proj_id"]}
    calendars = {c["clndr_id"]: finite(c.get("day_hr_cnt") or 8, "calendar day hours")
                 for c in data.get("CALENDAR", [])}
    chains, names = {}, {}
    for key in wbs:
        chain, seen, node = [], set(), key
        while node in wbs:
            if node in seen:
                raise ValueError("WBS cycle")
            seen.add(node)
            chain.insert(0, wbs[node]["wbs_short_name"])
            node = wbs[node].get("parent_wbs_id")
        chains[key] = tuple(chain)
        names[tuple(chain)] = wbs[key].get("wbs_name") or chain[-1]
    date_map = {"plannedStart": "target_start_date", "plannedFinish": "target_end_date",
                "actualStart": "act_start_date", "actualFinish": "act_end_date",
                "baselineStart": "baseline_start_date", "baselineFinish": "baseline_end_date"}
    activities = []
    for row in rows:
        if row["wbs_id"] not in chains:
            raise ValueError("task references missing WBS")
        hours = calendars.get(row.get("clndr_id", project.get("clndr_id")), 8)
        if hours <= 0:
            raise ValueError("calendar day hours must be positive")
        links = []
        for edge in data.get("TASKPRED", []):
            if edge["task_id"] != row["task_id"]:
                continue
            if edge["pred_task_id"] not in task_ids:
                raise ValueError("external or missing XER predecessor; supply a complete project")
            kind = edge["pred_type"].removeprefix("PR_")
            links.append((task_ids[edge["pred_task_id"]], finite(edge.get("lag_hr_cnt") or 0, "lag hours") / hours, kind))
        activities.append(Activity(row["task_code"], row.get("task_name", ""), chains[row["wbs_id"]],
                                   row.get("dc_task_type") or "construction",
                                   row.get("task_type") in {"TT_Mile", "TT_StartMile", "TT_FinMile"},
                                   {name: iso(row.get(field)) for name, field in date_map.items()},
                                   finite(row.get("phys_complete_pct") or 0, "percentComplete"), links))
    starts = [a.dates["plannedStart"] for a in activities if a.dates["plannedStart"]]
    finishes = [a.dates["plannedFinish"] for a in activities if a.dates["plannedFinish"]]
    start = iso(project.get("plan_start_date")) or min(starts, default="")
    finish = iso(project.get("plan_end_date")) or max(finishes, default="")
    programme = Programme(programme_id or project["proj_short_name"], project["proj_short_name"],
                          start, start, finish, "p6 xer", iso(project.get("last_recalc_date")),
                          activities=activities, wbs_names=names,
                          boundary_source="source" if project.get("plan_end_date") else "activityEnvelope")
    programme.validate()
    return programme


def main(argv=None):
    from .cli import import_main
    return import_main("xer", argv)


if __name__ == "__main__":
    raise SystemExit(main())
