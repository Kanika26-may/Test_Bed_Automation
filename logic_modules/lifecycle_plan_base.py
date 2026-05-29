import importlib
import importlib.util
import inspect
import os
from dataclasses import dataclass
from types import ModuleType
from typing import Dict, Optional


@dataclass
class LifecyclePlanAdapter:
    base_module_name: str
    module_name: str
    lifecycle_stage: str
    product_code: Optional[str] = None

    def __post_init__(self):
        self._base_module = self._load_base_module(self.base_module_name)

    def _load_base_module(self, module_name: str) -> ModuleType:
        try:
            return importlib.import_module(f"logic_modules.{module_name}")
        except Exception:
            module_path = os.path.join(os.path.dirname(__file__), f"{module_name}.py")
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module_obj = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module_obj)
            return module_obj

    @property
    def epic_map(self):
        return getattr(self._base_module, "EPIC_MAP", {})

    @property
    def epic_map_rider(self):
        return getattr(self._base_module, "EPIC_MAP_RIDER", {})

    def generate_test_cases(
        self,
        epic_counts,
        selected_epics=None,
        epic_counts_rider=None,
        selected_epics_rider=None,
        **kwargs,
    ):
        generator = getattr(self._base_module, "generate_test_cases")
        call_kwargs = {
            "epic_counts": epic_counts,
            "selected_epics": selected_epics,
            "epic_counts_rider": epic_counts_rider,
            "selected_epics_rider": selected_epics_rider,
        }
        if kwargs:
            try:
                sig = inspect.signature(generator)
            except (TypeError, ValueError):
                sig = None
            if sig is not None:
                for key, value in kwargs.items():
                    if value is not None and key in sig.parameters:
                        call_kwargs[key] = value
        return generator(**call_kwargs)


def build_lifecycle_module_exports(base_module_name: str, module_name: str, lifecycle_stage: str, product_code: Optional[str] = None) -> Dict[str, object]:
    adapter = LifecyclePlanAdapter(
        base_module_name=base_module_name,
        module_name=module_name,
        lifecycle_stage=lifecycle_stage,
        product_code=product_code,
    )

    exports = {
        "MODULE_NAME": module_name,
        "LIFECYCLE_STAGE": lifecycle_stage,
        "BASE_MODULE_NAME": base_module_name,
        "EPIC_MAP": adapter.epic_map,
        "EPIC_MAP_RIDER": adapter.epic_map_rider,
        "generate_test_cases": adapter.generate_test_cases,
    }

    if product_code is not None:
        exports["PRODUCT_CODE"] = product_code
    elif hasattr(adapter._base_module, "PRODUCT_CODE"):
        exports["PRODUCT_CODE"] = getattr(adapter._base_module, "PRODUCT_CODE")

    return exports
