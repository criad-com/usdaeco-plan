"""Format-neutral programme records and deterministic USD driver authoring."""
from dataclasses import dataclass, field, replace
from datetime import date
import hashlib
import json
import math
from pathlib import Path
import uuid

from pxr import Sdf, Tf, Usd, UsdGeom, Vt

TASK_TYPES = {"construction", "demolition", "installation", "removal", "move",
              "logistic", "maintenance", "operation", "attendance", "notDefined"}
DATE_FIELDS = ("plannedStart", "plannedFinish", "baselineStart", "baselineFinish",
               "actualStart", "actualFinish")
WORKSPACE_FIELDS = ("requiresAccess", "encloses", "occupies", "accessVia")
FALLBACKS = {name: Vt.TokenArray(["Scope"]) for name in
             ("AecoProgramme", "AecoActivity", "AecoMilestone")}


def iso(value):
    """Store date precision; source calendars own intraday scheduling."""
    if not value:
        return ""
    return date.fromisoformat(value.strip().split("T")[0].split(" ")[0]).isoformat()


def finite(value, label):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(label + " must be finite")
    return number


def identifier(key):
    result = Tf.MakeValidIdentifier(key)
    return result if result == key else result + "_" + hashlib.sha256(key.encode()).hexdigest()[:10]


def identity(programme, key):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "aeco-plan/" + programme + "/" + key))


@dataclass
class Activity:
    key: str
    name: str
    wbs: tuple[str, ...] = ()
    task_type: str = "construction"
    milestone: bool = False
    dates: dict = field(default_factory=dict)
    percent: float = 0
    links: list[tuple[str, float, str]] = field(default_factory=list)
    scope: list[str] = field(default_factory=list)
    workspace: dict = field(default_factory=dict)


@dataclass
class Programme:
    key: str
    name: str
    epoch: str
    start: str
    finish: str
    source: str
    data_date: str = ""
    time_codes_per_day: float = 1
    activities: list[Activity] = field(default_factory=list)
    wbs_names: dict[tuple[str, ...], str] = field(default_factory=dict)
    boundary_source: str = "source"

    def validate(self):
        if not self.key or not self.activities:
            raise ValueError("programme identity and activities are required")
        keys = [a.key for a in self.activities]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate activity identity")
        if finite(self.time_codes_per_day, "timeCodesPerDay") <= 0:
            raise ValueError("timeCodesPerDay must be positive")
        for value in (self.epoch, self.start, self.finish, self.data_date):
            iso(value)
        for activity in self.activities:
            if activity.task_type not in TASK_TYPES:
                raise ValueError("unknown taskType: " + activity.task_type)
            if not 0 <= finite(activity.percent, "percentComplete") <= 100:
                raise ValueError("percentComplete outside zero to one hundred")
            for value in activity.dates.values():
                iso(value)
            for predecessor, lag, kind in activity.links:
                if predecessor not in keys or kind not in {"FS", "SS", "FF", "SF"}:
                    raise ValueError("unresolved predecessor or unknown link type")
                finite(lag, "lagDays")


def bind(programme, scope=None, workspace=None):
    """Attach source identity references before resolving them against a stage."""
    scopes = json.loads(Path(scope).read_text()) if scope else {}
    spaces = json.loads(Path(workspace).read_text()).get("activities", {}) if workspace else {}
    keys = {a.key for a in programme.activities}
    if (set(scopes) | set(spaces)) - keys:
        raise ValueError("binding names an unknown activity")
    for activity in programme.activities:
        activity.scope = list(scopes.get(activity.key, activity.scope))
        activity.workspace = spaces.get(activity.key, activity.workspace)
        if set(activity.workspace) - set(WORKSPACE_FIELDS):
            raise ValueError("unknown workspace relationship")
    return programme


def attr(prim, name, value, type_name=Sdf.ValueTypeNames.String):
    return prim.CreateAttribute(name, type_name, custom=False).Set(value)


def members(prim, paths):
    collection = Usd.CollectionAPI.Apply(prim, "members")
    collection.CreateExpansionRuleAttr().Set("explicitOnly")
    collection.CreateIncludesRel().SetTargets(sorted(set(paths)))


def id_index(stage):
    """The only semantic identity is aeco:id; source keys are import aliases."""
    result = {}
    for prim in stage.Traverse():
        for name in ("aeco:id", "aeco:props:source:id", "aeco:props:DC_Identity:Id"):
            value = prim.GetAttribute(name).Get()
            if value:
                if value in result and result[value] != prim.GetPath():
                    raise ValueError("ambiguous scope identity")
                result[value] = prim.GetPath()
    return result


def write_programme(programme, output=None, *, stage=None, normalized=False):
    """Author drivers only. Normalization removes format provenance and title.

    Dates, WBS, scope, identity, progress and every ordered link instance remain.
    A caller supplies the same programme key for matching exports.
    """
    programme.validate()
    result = Usd.Stage.CreateInMemory()
    result.SetMetadata("fallbackPrimTypes", FALLBACKS)
    UsdGeom.SetStageMetersPerUnit(result, 1)
    UsdGeom.SetStageUpAxis(result, UsdGeom.Tokens.z)
    root = result.DefinePrim("/Programme", "AecoProgramme")
    result.SetDefaultPrim(root)
    root.SetDisplayName(programme.key if normalized else programme.name)
    attr(root, "aeco:id", identity(programme.key, "programme"))
    values = {"epoch": programme.epoch, "timeCodesPerDay": programme.time_codes_per_day,
              "plannedStart": programme.start, "plannedFinish": programme.finish,
              "dataDate": programme.data_date, "source": "" if normalized else programme.source}
    for name, value in values.items():
        attr(root, "aeco:plan:" + name, value,
             Sdf.ValueTypeNames.Double if isinstance(value, (int, float)) else Sdf.ValueTypeNames.String)
    root.SetCustomDataByKey("aeco:plan:boundarySource", programme.boundary_source)
    index = id_index(stage) if stage else {}

    def resolve(key):
        if key in index:
            return index[key]
        if key.startswith("/") and Sdf.Path.IsValidPathString(key):
            return Sdf.Path(key)
        # Keep missing references visible to DanglingScope; never drop them.
        return Sdf.Path("/Unresolved/" + identifier(key))

    all_scope = []
    for activity in sorted(programme.activities, key=lambda a: (a.wbs, a.key)):
        parent = root.GetPath()
        for i, part in enumerate(activity.wbs):
            chain = activity.wbs[:i + 1]
            parent = parent.AppendChild(identifier(part))
            wbs = result.DefinePrim(parent, "AecoActivity")
            attr(wbs, "aeco:id", identity(programme.key, "wbs/" + "/".join(chain)))
            attr(wbs, "aeco:plan:wbsCode", ".".join(chain))
            attr(wbs, "aeco:plan:taskType", "notDefined", Sdf.ValueTypeNames.Token)
            wbs.SetDisplayName(programme.wbs_names.get(chain, part))
        prim = result.DefinePrim(parent.AppendChild(identifier(activity.key)),
                                 "AecoMilestone" if activity.milestone else "AecoActivity")
        prim.SetDisplayName(activity.name)
        attr(prim, "aeco:id", identity(programme.key, activity.key))
        attr(prim, "aeco:plan:wbsCode", ".".join((*activity.wbs, activity.key)))
        attr(prim, "aeco:plan:taskType", activity.task_type, Sdf.ValueTypeNames.Token)
        prim.ApplyAPI("AecoScheduleAPI")
        prim.ApplyAPI("AecoWorkspaceAPI")
        for name in DATE_FIELDS:
            attr(prim, "aeco:schedule:" + name, iso(activity.dates.get(name, "")))
        attr(prim, "aeco:schedule:percentComplete", activity.percent, Sdf.ValueTypeNames.Double)
        attr(prim, "aeco:plan:predecessorIds", [identity(programme.key, p) for p, _, _ in activity.links], Sdf.ValueTypeNames.StringArray)
        attr(prim, "aeco:plan:lagDays", [lag for _, lag, _ in activity.links], Sdf.ValueTypeNames.DoubleArray)
        attr(prim, "aeco:plan:linkType", [kind for _, _, kind in activity.links], Sdf.ValueTypeNames.TokenArray)
        paths = [resolve(key) for key in activity.scope]
        members(prim, paths)
        all_scope.extend(paths)
        for name in WORKSPACE_FIELDS:
            prim.CreateRelationship("aeco:workspace:" + name, custom=False).SetTargets(
                sorted(set(resolve(key) for key in activity.workspace.get(name, []))))
    members(root, all_scope)
    text = result.GetRootLayer().ExportToString()
    if output:
        Path(output).write_text(text)
    return text


def normalize_layer(source, output=None):
    """Canonical layer text; only source provenance and programme displayName vary."""
    layer = Sdf.Layer.OpenAsAnonymous(str(source))
    stage = Usd.Stage.Open(layer)
    for prim in stage.Traverse():
        if prim.GetTypeName() == "AecoProgramme":
            attr(prim, "aeco:plan:source", "")
            prim.SetDisplayName(prim.GetAttribute("aeco:id").Get())
    text = layer.ExportToString()
    if output:
        Path(output).write_text(text)
    return text
