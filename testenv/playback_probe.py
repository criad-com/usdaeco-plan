"""Run with -I and no family plugins; all assertions inspect copied artifacts."""
from datetime import date
import json
from pathlib import Path
import sys
from pxr import Usd, UsdGeom


def probe(root, inputs):
    result = {}
    for key in ('A', 'B'):
        entry = root / ('layers/out/A/play.usda' if key == 'A' else 'example.usdc')
        stage = Usd.Stage.Open(str(entry))
        assert stage and not stage.GetCompositionErrors()
        assert stage.GetStartTimeCode() == 0 and stage.GetEndTimeCode() == 77
        programme = stage.GetPrimAtPath('/Programme')
        assert programme.GetTypeName() == 'AecoProgramme'
        assert programme.IsA(UsdGeom.Scope)
        epoch = date.fromisoformat(programme.GetAttribute('aeco:plan:epoch').Get())
        rows, fields, table = [], None, None
        # Read the public XER fixture independently of the importer and deriver.
        for line in (inputs / (key + '.xer')).read_text().splitlines():
            cells = line.split('\t')
            if cells[0] == '%T':
                table = cells[1]
            elif cells[0] == '%F':
                fields = cells[1:]
            elif cells[0] == '%R' and table == 'TASK':
                rows.append(dict(zip(fields, cells[1:])))
        scopes = json.loads((inputs / (key + '.scope.json')).read_text())
        events = {}
        for row in rows:
            kind = row['dc_task_type']
            if kind not in {'construction', 'installation', 'move', 'removal', 'demolition'}:
                continue
            day = (date.fromisoformat(row['target_start_date'].split()[0]) - epoch).days
            for source_id in scopes[row['task_code']]:
                events.setdefault(source_id, []).append((day, kind not in {'removal', 'demolition'}))
        index = {p.GetAttribute('aeco:props:DC_Identity:Id').Get(): p for p in stage.Traverse()
                 if p.GetAttribute('aeco:props:DC_Identity:Id').Get()}
        checks, masks = 0, {}
        for source_id, sequence in sorted(events.items()):
            prim = index[source_id]
            image = UsdGeom.Imageable(prim)
            mask = []
            for day in range(0, 78, 7):
                expected = False
                for start, visible in sorted(sequence):
                    if day >= start:
                        expected = visible
                actual = image.ComputeVisibility(day) == 'inherited'
                assert actual == expected, (key, source_id, day, actual, expected)
                mask.append(int(actual))
                checks += 1
            masks[source_id] = mask
        result[key] = {'targets': len(events), 'weeks': 12, 'checks': checks,
                       'temporaryPod': masks['pod.wc.temp'], 'firstFix': masks['tray.void.ocorr.1'],
                       'corridorCeiling': masks['clg.ocorr.1'], 'finalPod': masks['pod.wc']}
    return result


if __name__ == '__main__':
    print(json.dumps(probe(Path(sys.argv[1]), Path(sys.argv[2])), sort_keys=True))
