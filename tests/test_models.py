"""Tests for Ultimate Lists models and sorting."""

from __future__ import annotations

import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "custom_components" / "ultimate_lists"

sys.modules.setdefault("custom_components", types.ModuleType("custom_components"))
package_module = sys.modules.setdefault(
    "custom_components.ultimate_lists", types.ModuleType("custom_components.ultimate_lists")
)
package_module.__path__ = [str(PACKAGE_ROOT)]


def _load_module(module_name: str, filename: str):
    spec = spec_from_file_location(module_name, PACKAGE_ROOT / filename)
    module = module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_load_module("custom_components.ultimate_lists.const", "const.py")
models = _load_module("custom_components.ultimate_lists.models", "models.py")

UltimateList = models.UltimateList
list_from_dict = models.list_from_dict
list_to_dict = models.list_to_dict
make_item = models.make_item
make_list = models.make_list
make_section = models.make_section
sort_items_for_display = models.sort_items_for_display


class UltimateListsModelTests(unittest.TestCase):
    """Model-level tests that can run without Home Assistant installed."""

    def test_round_trip_serialization(self) -> None:
        grocery = make_list("Grocery")
        grocery.locked = True
        grocery.list_order = 4
        produce = make_section("Produce", section_type="room", sort_order=0)
        grocery.sections.append(produce)
        grocery.items.append(make_item("Apples", section_id=produce.id, sort_order=0))
        grocery.items.append(make_item("Milk", sort_order=1))

        restored = list_from_dict(list_to_dict(grocery))

        self.assertEqual(restored.title, "Grocery")
        self.assertEqual(len(restored.sections), 1)
        self.assertEqual(len(restored.items), 2)
        self.assertEqual(restored.items[0].text, "Apples")
        self.assertTrue(restored.locked)
        self.assertEqual(restored.list_order, 4)

    def test_unchecked_items_sort_to_top(self) -> None:
        grocery = UltimateList(id="list-1", title="Grocery", sort_mode="unchecked_first")
        apples = make_item("Apples", sort_order=0)
        bread = make_item("Bread", sort_order=1)
        carrots = make_item("Carrots", sort_order=2, important=True)
        bread.checked = True
        grocery.items = [bread, apples, carrots]

        ordered = sort_items_for_display(grocery)

        self.assertEqual([item.text for item in ordered], ["Carrots", "Apples", "Bread"])

    def test_manual_sort_mode_preserves_sort_order(self) -> None:
        checklist = UltimateList(id="list-2", title="Checklist", sort_mode="manual")
        checklist.items = [
            make_item("Third", sort_order=2),
            make_item("First", sort_order=0),
            make_item("Second", sort_order=1),
        ]

        ordered = sort_items_for_display(checklist)

        self.assertEqual([item.text for item in ordered], ["First", "Second", "Third"])


if __name__ == "__main__":
    unittest.main()
