#!/pxrpythonsubst
from pathlib import Path
import tempfile
import unittest
from pxr import Sdf, Usd, UsdGeom
from fixtures import clean_stage, links
from usdaeco_plan.derive import derive, lookahead, predecessors
from usdaeco_plan.model import attr


class TestDerive(unittest.TestCase):
    def setUp(self):
        self.stage = clean_stage()

    def test_temporary_window_and_mute_preserves_drivers(self):
        source = self.stage.GetRootLayer().ExportToString()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / '4d.usda'
            result = derive(self.stage, output)
            self.assertEqual(result['targets'], 3)
            self.assertEqual(source, self.stage.GetRootLayer().ExportToString())
            self.stage.GetRootLayer().subLayerPaths = [str(output)]
            imageable = UsdGeom.Imageable(self.stage.GetPrimAtPath('/World/Temp'))
            for day, visible in [(13, False), (14, True), (30, True), (31, False), (32, False)]:
                self.assertEqual(imageable.ComputeVisibility(day), 'inherited' if visible else 'invisible')
            self.assertEqual(imageable.GetVisibilityAttr().Get(), 'inherited')
            self.stage.MuteLayer(str(output))
            self.assertEqual(imageable.GetVisibilityAttr().GetTimeSamples(), [])
            self.stage.GetRootLayer().subLayerPaths = []
            self.assertEqual(source, self.stage.GetRootLayer().ExportToString())

    def test_actual_clock_and_reproducibility(self):
        attr(self.stage.GetPrimAtPath('/Programme'), 'aeco:plan:timeCodesPerDay', 2., Sdf.ValueTypeNames.Double)
        attr(self.stage.GetPrimAtPath('/Programme/Build'), 'aeco:schedule:actualStart', '2027-03-17')
        with tempfile.TemporaryDirectory() as directory:
            one, two = [Path(directory) / n for n in ('one.usda', 'two.usda')]
            result = derive(self.stage, one)
            derive(self.stage, two)
            self.assertEqual(one.read_bytes(), two.read_bytes())
            self.assertEqual(result['transitions']['/World/Work'], [32.])

    def test_derived_unique_predecessors_preserve_multiedges(self):
        links(self.stage, 'Close', ['Inspect', 'Inspect', 'Build'])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'predecessors.usda'
            counts = predecessors(self.stage, output)
            derived = Usd.Stage.Open(str(output))
            self.assertEqual(counts, {'linkInstances': 4, 'uniqueTargets': 3})
            self.assertEqual(derived.GetPrimAtPath('/Programme/Close').GetRelationship('aeco:plan:predecessors').GetTargets(),
                             [Sdf.Path('/Programme/Build'), Sdf.Path('/Programme/Inspect')])
            self.assertEqual(len(self.stage.GetPrimAtPath('/Programme/Close').GetAttribute('aeco:plan:predecessorIds').Get()), 3)

    def test_lookahead_intersection_and_half_open_end(self):
        self.assertEqual(lookahead(self.stage, 2), [])
        self.assertEqual({r['name'] for r in lookahead(self.stage, 1, start='2027-03-15')}, {'Build', 'Install', 'Park'})
        with self.assertRaises(ValueError):
            lookahead(self.stage, 0)


if __name__ == '__main__':
    unittest.main()
