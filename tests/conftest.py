import importlib.util
from pathlib import Path
import sys
import types

# Import pure modules without loading the NekroAgent runtime in __init__.py.
root = Path(__file__).resolve().parents[1]
package = types.ModuleType('denia_test')
package.__path__ = [str(root)]
sys.modules['denia_test'] = package

for name in ['generation','request_retry','triggers','prompts']:
    spec=importlib.util.spec_from_file_location('denia_test.'+name,root/(name+'.py'))
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
