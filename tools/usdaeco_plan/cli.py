"""Import XER/MSPDI, normalize layers, derive 4D and query a lookahead."""
import argparse
import json
import os
from pathlib import Path
from pxr import Plug, Usd
from .model import bind, normalize_layer, write_programme


def register():
    root = Path(__file__).resolve().parents[2]
    core = Path(os.environ.get("CORE_PLUGIN_DIR", root.parent / "usdaeco-core/out/plugins/usdAeco/resources"))
    Plug.Registry().RegisterPlugins(str(core))
    Plug.Registry().RegisterPlugins(str(root / "usdAecoPlan"))
    Plug.Registry().RegisterPlugins(str(root / "usdAecoPlanValidators"))


def import_main(format_name, argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--programme-id")
    parser.add_argument("--project-id")
    parser.add_argument("--stage", type=Path)
    parser.add_argument("--scope", type=Path)
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--normalize", action="store_true")
    args = parser.parse_args(argv)
    register()
    from . import xer2usdaeco, mspdi2usdaeco
    options = {"programme_id": args.programme_id}
    if format_name == "xer":
        options["project_id"] = args.project_id
    programme = (xer2usdaeco if format_name == "xer" else mspdi2usdaeco).parse(args.input, **options)
    bind(programme, args.scope, args.workspace)
    stage = Usd.Stage.Open(str(args.stage)) if args.stage else None
    write_programme(programme, args.out, stage=stage, normalized=args.normalize)
    print(json.dumps({"activities": len(programme.activities), "links": sum(len(a.links) for a in programme.activities)}))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("xer", "mspdi"):
        sub.add_parser(name, add_help=False)
    d = sub.add_parser("derive")
    d.add_argument("stage")
    d.add_argument("--out", default="4d.usda")
    d.add_argument("--programme")
    l = sub.add_parser("lookahead")
    l.add_argument("weeks", type=int)
    l.add_argument("stage")
    l.add_argument("--start")
    l.add_argument("--programme")
    n = sub.add_parser("normalize")
    n.add_argument("layer")
    n.add_argument("--out", required=True)
    v = sub.add_parser("validate")
    v.add_argument("stage")
    args, rest = parser.parse_known_args(argv)
    if args.command in ("xer", "mspdi"):
        return import_main(args.command, rest)
    if rest:
        parser.error("unrecognized arguments: " + " ".join(rest))
    register()
    from .derive import derive, lookahead, predecessors
    if args.command == "normalize":
        normalize_layer(args.layer, args.out)
        return 0
    stage = Usd.Stage.Open(args.stage)
    if args.command == "derive":
        result = derive(stage, args.out, programme_path=args.programme)
        result.update(predecessors(stage, Path(args.out).with_name("predecessors.usda")))
    elif args.command == "lookahead":
        result = lookahead(stage, args.weeks, start=args.start, programme_path=args.programme)
    else:
        from .validation import findings
        result = findings(stage)
    print(json.dumps(result, indent=2))
    return int(args.command == "validate" and any(r["severity"] == "error" for r in result))


if __name__ == "__main__":
    raise SystemExit(main())
