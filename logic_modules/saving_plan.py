import importlib.util
import os

BASE_MODULE_PATH = os.path.join(os.path.dirname(__file__), "term_plan.py")
_spec = importlib.util.spec_from_file_location("base_term_plan", BASE_MODULE_PATH)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

for _name in dir(_module):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_module, _name)

MODULE_NAME = "Saving Plan"
