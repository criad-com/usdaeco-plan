#!/pxrpythonsubst
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]

SCRIPT = r'''
from pathlib import Path
import sys, tempfile
from pxr import UsdGeom, Sdf
root = Path(sys.argv[1])
sys.path[:0] = [str(root / 'tools'), str(root / 'testenv')]
from usdaeco_plan.cli import register
register()
from usdaeco_plan.example import presentation
from usdaeco_plan.model import attr, members
from fixtures import clean_stage
stage = clean_stage()
attr(stage.GetPrimAtPath('/World/Temp'), 'aeco:props:DC_Identity:Id', 'pod.wc.temp')
for name in ('Work', 'Ceiling', 'Temp', 'ExtraOne', 'ExtraTwo', 'ExtraThree'):
    prim = stage.DefinePrim('/World/' + name, 'Xform')
    UsdGeom.Cube.Define(stage, prim.GetPath().AppendChild('Body'))
members(stage.GetPrimAtPath('/Programme/Build'), [Sdf.Path('/World/' + n) for n in ('Work', 'ExtraOne', 'ExtraTwo', 'ExtraThree')])
with tempfile.TemporaryDirectory() as directory:
    output = Path(directory) / 'presentation.usda'
    workspace = Path(directory) / 'workspace.json'
    workspace.write_text('{"placements": {}}')
    presentation(stage, stage, workspace, output, 'B')
    print(output.read_text(), end='')
'''


class TestPresentation(unittest.TestCase):
    def test_authored_layer_order_is_independent_of_hash_seed(self):
        outputs = []
        for seed in ('11', '37'):
            environment = {k: v for k, v in os.environ.items() if k != 'PYTHONPATH'}
            environment['PYTHONHASHSEED'] = seed
            result = subprocess.run([sys.executable, '-c', SCRIPT, str(ROOT)], env=environment,
                                    text=True, capture_output=True, check=True)
            outputs.append(result.stdout)
        self.assertIn('ExtraThree', outputs[0])
        self.assertEqual(outputs[0], outputs[1])


if __name__ == '__main__':
    unittest.main()
