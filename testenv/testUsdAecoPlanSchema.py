#!/pxrpythonsubst
from pathlib import Path
import unittest
from pxr import Plug, Usd

ROOT = Path(__file__).resolve().parents[1]


class TestSchema(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from usdaeco_plan.cli import register
        register()
        Plug.Registry().RegisterPlugins(str(ROOT / 'usdAecoPlan'))

    def test_registry(self):
        registry = Usd.SchemaRegistry()
        for name in ('AecoProgramme', 'AecoActivity', 'AecoMilestone'):
            self.assertIsNotNone(registry.FindConcretePrimDefinition(name))
        for name in ('AecoScheduleAPI', 'AecoWorkspaceAPI'):
            self.assertIsNotNone(registry.FindAppliedAPIPrimDefinition(name))

    def test_refusal(self):
        stage = Usd.Stage.CreateInMemory()
        for schema in ('AecoScheduleAPI', 'AecoWorkspaceAPI'):
            for typename, allowed in [('AecoActivity', True), ('AecoMilestone', True),
                                      ('AecoProgramme', False), ('Xform', False), ('Material', False)]:
                self.assertEqual(bool(stage.DefinePrim('/P', typename).CanApplyAPI(schema)), allowed)

    def test_core_members_and_derived(self):
        stage = Usd.Stage.CreateInMemory()
        for name in ('AecoProgramme', 'AecoActivity', 'AecoMilestone'):
            prim = stage.DefinePrim('/' + name, name)
            self.assertTrue(Usd.CollectionAPI(prim, 'members'))
            self.assertEqual(prim.GetAttribute('collection:members:expansionRule').Get(), 'explicitOnly')
        definition = Usd.SchemaRegistry().FindConcretePrimDefinition('AecoActivity')
        self.assertIs(definition.GetPropertyMetadata('aeco:plan:predecessors', 'aecoDerived'), True)


if __name__ == '__main__':
    unittest.main()
