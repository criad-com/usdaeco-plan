#!/pxrpythonsubst
from pathlib import Path
import unittest
from pxr import Plug, Sdf, UsdValidation
from usdaeco_plan.model import attr, members
from usdaeco_plan.validation import findings
from fixtures import clean_stage, links

ROOT = Path(__file__).resolve().parents[1]


class TestValidators(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Plug.Registry().RegisterPlugins(str(ROOT / 'usdAecoPlanValidators'))
        cls.registry = UsdValidation.ValidationRegistry()

    def setUp(self):
        self.stage = clean_stage()
        self.assertEqual(findings(self.stage), [])

    def caught(self, rule, severity=UsdValidation.ValidationErrorType.Error):
        validator = self.registry.GetOrLoadValidatorByName('usdAecoPlanValidators:' + rule + 'Checker')
        self.assertTrue(validator)
        errors = UsdValidation.ValidationContext([validator]).Validate(self.stage)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].GetName(), rule)
        self.assertEqual(errors[0].GetType(), severity)
        self.assertTrue(errors[0].GetSites())

    def test_AccessAfterEnclosure(self):
        close = self.stage.GetPrimAtPath('/Programme/Close')
        attr(close, 'aeco:schedule:plannedStart', '2027-03-20')
        self.assertLess(close.GetAttribute('aeco:schedule:plannedStart').Get(),
                        self.stage.GetPrimAtPath('/Programme/Build').GetAttribute('aeco:schedule:plannedFinish').Get())
        self.caught('AccessAfterEnclosure')

    def test_WorkspaceOccupied(self):
        park = self.stage.GetPrimAtPath('/Programme/Park')
        park.GetRelationship('aeco:workspace:occupies').SetTargets(['/World/Corridor'])
        attr(park, 'aeco:schedule:plannedFinish', '2027-04-10')
        self.assertEqual(park.GetRelationship('aeco:workspace:occupies').GetTargets(), [Sdf.Path('/World/Corridor')])
        self.caught('WorkspaceOccupied')

    def test_EnclosureBeforeInspection(self):
        links(self.stage, 'Close', [])
        self.assertEqual(list(self.stage.GetPrimAtPath('/Programme/Close').GetAttribute('aeco:plan:predecessorIds').Get()), [])
        self.caught('EnclosureBeforeInspection', UsdValidation.ValidationErrorType.Warn)

    def test_PredecessorCycle(self):
        links(self.stage, 'Build', ['Close'])
        self.assertTrue(self.stage.GetPrimAtPath('/Programme/Build').GetAttribute('aeco:plan:predecessorIds').Get())
        self.caught('PredecessorCycle')

    def test_DanglingScope(self):
        self.stage.GetPrimAtPath('/Programme/Build').GetRelationship('collection:members:includes').AddTarget('/Missing')
        self.assertFalse(self.stage.GetPrimAtPath('/Missing'))
        self.caught('DanglingScope')

    def test_UnscheduledElement(self):
        extra = self.stage.DefinePrim('/World/Extra', 'Xform')
        extra.ApplyAPI('AecoElementAPI')
        self.stage.GetPrimAtPath('/Programme').GetRelationship('collection:members:includes').AddTarget(extra.GetPath())
        self.assertFalse(any(extra.GetPath() in p.GetRelationship('collection:members:includes').GetTargets()
                             for p in self.stage.GetPrimAtPath('/Programme').GetChildren()))
        self.caught('UnscheduledElement', UsdValidation.ValidationErrorType.Warn)

    def test_TemporaryWithoutRemoval(self):
        remove = self.stage.GetPrimAtPath('/Programme/Remove')
        members(remove, [])
        self.assertEqual(remove.GetRelationship('collection:members:includes').GetTargets(), [])
        self.caught('TemporaryWithoutRemoval', UsdValidation.ValidationErrorType.Warn)

    def test_DatesOutsideProgramme(self):
        build = self.stage.GetPrimAtPath('/Programme/Build')
        attr(build, 'aeco:schedule:plannedStart', '2027-02-28')
        self.assertLess(build.GetAttribute('aeco:schedule:plannedStart').Get(), '2027-03-01')
        self.caught('DatesOutsideProgramme')

    def test_malformed_dates_are_not_silent(self):
        attr(self.stage.GetPrimAtPath('/Programme/Build'), 'aeco:schedule:plannedFinish', 'unknown')
        self.caught('DatesOutsideProgramme')

    def test_inclusive_workspace_boundary(self):
        park = self.stage.GetPrimAtPath('/Programme/Park')
        park.GetRelationship('aeco:workspace:occupies').SetTargets(['/World/Corridor'])
        attr(park, 'aeco:schedule:plannedFinish', '2027-04-05')
        self.caught('WorkspaceOccupied')

    def test_future_inspection_predecessor_is_insufficient(self):
        inspect = self.stage.GetPrimAtPath('/Programme/Inspect')
        attr(inspect, 'aeco:schedule:plannedStart', '2027-04-12')
        attr(inspect, 'aeco:schedule:plannedFinish', '2027-04-13')
        self.caught('EnclosureBeforeInspection', UsdValidation.ValidationErrorType.Warn)


if __name__ == '__main__':
    unittest.main()
