#!/pxrpythonsubst
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pxr import Sdf, Usd
from usdaeco_plan import xer2usdaeco as xer, mspdi2usdaeco as msp
from usdaeco_plan.model import bind, write_programme, normalize_layer

INPUTS = Path(__file__).resolve().parents[1] / 'examples/datacentre/inputs'


class TestImport(unittest.TestCase):
    def test_equivalence_A_and_B(self):
        for key in ('A', 'B'):
            programmes = [module.parse(INPUTS / (key + '.' + ext), programme_id=key)
                          for module, ext in [(xer, 'xer'), (msp, 'xml')]]
            for programme in programmes:
                bind(programme, INPUTS / (key + '.scope.json'), INPUTS / (key + '.workspace.json'))
            self.assertEqual(write_programme(programmes[0], normalized=True),
                             write_programme(programmes[1], normalized=True))
            with tempfile.TemporaryDirectory() as directory:
                paths = [Path(directory) / (str(i) + '.usda') for i in range(2)]
                for programme, path in zip(programmes, paths):
                    write_programme(programme, path)
                self.assertEqual(normalize_layer(paths[0]), normalize_layer(paths[1]))

    def test_xer_multiedges_calendar_and_order(self):
        source = (INPUTS / 'A.xer').read_text().replace('Elapsed days\t24\t168', 'Eight hours\t8\t40')
        source = source.replace('%E', '%R\t10\t1\t2\t1\tPR_FF\t4\n%R\t11\t1\t2\t1\tPR_SF\t-8\n%R\t12\t1\t2\t1\tPR_SS\t0\n%E')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'test.xer'
            path.write_text(source)
            programme = xer.parse(path)
        links = next(a for a in programme.activities if a.key == 'act.pod.park').links
        self.assertEqual(links, [('act.pod.deliver', 0, 'SS'), ('act.pod.deliver', .5, 'FF'),
                                 ('act.pod.deliver', -1, 'SF'), ('act.pod.deliver', 0, 'SS')])
        layer = Sdf.Layer.CreateAnonymous()
        layer.ImportFromString(write_programme(programme))
        stage = Usd.Stage.Open(layer)
        prim = next(p for p in stage.Traverse() if p.GetDisplayName() == 'Pod parked awaiting relocation')
        self.assertEqual(len(prim.GetAttribute('aeco:plan:predecessorIds').Get()), 4)
        self.assertFalse(prim.GetRelationship('aeco:plan:predecessors').HasAuthoredTargets())

    def test_mspdi_all_link_types_negative_and_duplicate_lags(self):
        tree = ET.parse(INPUTS / 'A.xml')
        root = tree.getroot()
        ns = '{' + msp.NS + '}'
        root.find(ns + 'MinutesPerDay').text = '480'
        task = next(t for t in root.findall(ns + 'Tasks/' + ns + 'Task') if msp.child(t, 'UID') == '2')
        for old in task.findall(ns + 'PredecessorLink'):
            task.remove(old)
        for kind, lag in [(0, 2400), (1, 0), (2, -4800), (3, 9600), (0, 2400)]:
            edge = ET.SubElement(task, ns + 'PredecessorLink')
            for name, value in [('PredecessorUID', '1'), ('Type', str(kind)), ('LinkLag', str(lag))]:
                ET.SubElement(edge, ns + name).text = value
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'A.xml'
            tree.write(path)
            programme = msp.parse(path)
        links = next(a for a in programme.activities if a.key == 'act.pod.park').links
        self.assertEqual([(lag, kind) for _, lag, kind in links], [(.5, 'FF'), (0, 'FS'), (-1, 'SF'), (2, 'SS'), (.5, 'FF')])

    def test_milestone_progress_and_baseline(self):
        tree = ET.parse(INPUTS / 'A.xml')
        ns = '{' + msp.NS + '}'
        task = next(t for t in tree.getroot().findall(ns + 'Tasks/' + ns + 'Task') if msp.child(t, 'UID') == '1')
        for name, value in [('Milestone', '1'), ('ActualStart', '2027-03-16T08:00:00'), ('ActualFinish', '2027-03-16T17:00:00')]:
            ET.SubElement(task, ns + name).text = value
        task.find(ns + 'PercentComplete').text = '100'
        baseline = ET.SubElement(task, ns + 'Baseline')
        for name, value in [('Number', '0'), ('Start', '2027-03-14'), ('Finish', '2027-03-14')]:
            ET.SubElement(baseline, ns + name).text = value
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'A.xml'
            tree.write(path)
            activity = next(a for a in msp.parse(path).activities if a.key == 'act.pod.deliver')
        self.assertTrue(activity.milestone)
        self.assertEqual(activity.percent, 100)
        self.assertEqual(activity.dates['actualStart'], '2027-03-16')
        self.assertEqual(activity.dates['baselineFinish'], '2027-03-14')

    def test_rejects_unknown_predecessor_and_calendar(self):
        for before, after in [('PR_SS\t0', 'PR_BAD\t0'), ('Elapsed days\t24', 'Elapsed days\t-1')]:
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'A.xer'
                path.write_text((INPUTS / 'A.xer').read_text().replace(before, after))
                with self.assertRaises(ValueError):
                    xer.parse(path)


if __name__ == '__main__':
    unittest.main()
