"""Unit tests for xmlfile.py's set_element_text - a pure function, so these need no mocking at
all (no `host`, no pyinfra involved): just XML content in, XML content out.
"""

import unittest
import xml.etree.ElementTree as ET

from xmlfile import Attribute, Element, set_element_text

FCPARAMS_ROOT = [
    Element("FCParameters"),
    Element("FCParamGroup", [Attribute("Name", "Root")]),
    Element("FCParamGroup", [Attribute("Name", "BaseApp")]),
    Element("FCParamGroup", [Attribute("Name", "Preferences")]),
    Element("FCParamGroup", [Attribute("Name", "General")]),
]

def _leaf_text(content: str, elements: list[Element]) -> str | None:
    node = ET.fromstring(content)
    for element in elements[1:]:
        predicates = "".join(f"[@{attr.name}='{attr.value}']" for attr in element.attributes)
        found = node.find(f"{element.tag}{predicates}")
        assert found is not None
        node = found
    return node.text

class TestSetElementText(unittest.TestCase):
    def test_creates_the_document_root_and_full_group_chain_when_content_is_empty(self):
        # Arrange
        elements = [*FCPARAMS_ROOT, Element("FCText", [Attribute("Name", "AutoloadModule")])]

        # Act
        content = set_element_text("", elements, "PartDesignWorkbench")

        # Assert
        self.assertTrue(content.startswith("<?xml"))
        self.assertEqual(_leaf_text(content, elements), "PartDesignWorkbench")

    def test_reuses_existing_groups_and_preserves_sibling_leaves(self):
        # Arrange
        elements_a = [*FCPARAMS_ROOT, Element("FCText", [Attribute("Name", "AutoloadModule")])]
        elements_b = [*FCPARAMS_ROOT, Element("FCText", [Attribute("Name", "FileExportFilter")])]
        content = set_element_text("", elements_a, "PartDesignWorkbench")

        # Act
        content = set_element_text(content, elements_b, "3D Manufacturing Format (*.3mf)")

        # Assert
        self.assertEqual(_leaf_text(content, elements_a), "PartDesignWorkbench")
        self.assertEqual(_leaf_text(content, elements_b), "3D Manufacturing Format (*.3mf)")
        # Only one "General" group should exist - not a duplicate created by the second call.
        root = ET.fromstring(content)
        general_groups = root.findall(".//FCParamGroup[@Name='General']")
        self.assertEqual(len(general_groups), 1)

    def test_overwrites_an_existing_different_value_without_touching_siblings(self):
        # Arrange
        elements_a = [*FCPARAMS_ROOT, Element("FCText", [Attribute("Name", "AutoloadModule")])]
        elements_b = [*FCPARAMS_ROOT, Element("FCText", [Attribute("Name", "FileExportFilter")])]
        content = set_element_text("", elements_a, "SketcherWorkbench")
        content = set_element_text(content, elements_b, "3D Manufacturing Format (*.3mf)")

        # Act
        content = set_element_text(content, elements_a, "PartDesignWorkbench")

        # Assert
        self.assertEqual(_leaf_text(content, elements_a), "PartDesignWorkbench")
        self.assertEqual(_leaf_text(content, elements_b), "3D Manufacturing Format (*.3mf)")

    def test_reuses_a_populated_existing_document_untouched_elsewhere(self):
        # Arrange
        existing = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<FCParameters><FCParamGroup Name=\"Tux\"><FCParamGroup Name=\"NavigationIndicator\">"
            '<FCBool Name="Compact" Value="0"/></FCParamGroup></FCParamGroup></FCParameters>'
        )
        elements = [*FCPARAMS_ROOT, Element("FCText", [Attribute("Name", "AutoloadModule")])]

        # Act
        content = set_element_text(existing, elements, "PartDesignWorkbench")

        # Assert
        self.assertEqual(_leaf_text(content, elements), "PartDesignWorkbench")
        root = ET.fromstring(content)
        compact = root.find(".//FCParamGroup[@Name='Tux']/FCParamGroup[@Name='NavigationIndicator']/FCBool[@Name='Compact']")
        self.assertIsNotNone(compact)
        self.assertEqual(compact.get("Value"), "0") # pyright: ignore[reportOptionalMemberAccess]

    def test_value_with_quotes_and_backslashes_round_trips_correctly(self):
        # Arrange
        elements = [*FCPARAMS_ROOT, Element("FCText", [Attribute("Name", "FileExportFilter")])]
        tricky_value = """it's a "test" with a \\ backslash"""

        # Act
        content = set_element_text("", elements, tricky_value)

        # Assert
        self.assertEqual(_leaf_text(content, elements), tricky_value)

    def test_creates_an_element_with_no_attributes(self):
        # Arrange
        elements = [Element("FCParameters"), Element("FCText")]

        # Act
        content = set_element_text("", elements, "hello")

        # Assert
        root = ET.fromstring(content)
        leaf = root.find("FCText")
        self.assertIsNotNone(leaf)
        self.assertEqual(leaf.text, "hello") # pyright: ignore[reportOptionalMemberAccess]

if __name__ == "__main__":
    unittest.main()
