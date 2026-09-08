"""Generic, reusable helper for idempotently setting one element's text inside a nested XML
document - creating any missing ancestor elements along the way, including the document root
itself if the document doesn't exist yet. Pure string-in/string-out, no pyinfra imports: knows
nothing about any particular app's tag/attribute conventions (e.g. FreeCAD's FCParamGroup/
FCText/Name) - that knowledge belongs to the caller (see pyinfra/modules/freecad.py), not here.
Reused across apps the same way keyfile.py's set_key_value is reused by darktable.py/ghostty.py
for flat key=value files.
"""

from dataclasses import dataclass, field
import xml.etree.ElementTree as ET

@dataclass(frozen=True)
class Attribute:
    name: str
    value: str

@dataclass(frozen=True)
class Element:
    tag: str
    attributes: list[Attribute] = field(default_factory=list)

def _query(element: Element) -> str:
    predicates = "".join(f"[@{attr.name}='{attr.value}']" for attr in element.attributes)
    return f"{element.tag}{predicates}"

def _attrib(element: Element) -> dict[str, str]:
    return {attr.name: attr.value for attr in element.attributes}

def _find_or_create_child(parent: ET.Element, element: Element) -> ET.Element:
    child = parent.find(_query(element))
    if child is not None:
        return child
    return ET.SubElement(parent, element.tag, _attrib(element))

def set_element_text(content: str, elements: list[Element], value: str) -> str:
    """Given XML `content` (pass an empty string if the document doesn't exist yet), ensures
    the chain of elements described by `elements` exists - the first entry describes the
    document root itself, each entry after it a child of the previous one, matched or created
    by its tag + attributes - then sets the *last* element's text to `value`. Returns the new
    content; nothing else in the document is touched.
    """
    root_spec = elements[0]
    root = ET.fromstring(content) if content.strip() else ET.Element(root_spec.tag, _attrib(root_spec))

    node = root
    for element in elements[1:]:
        node = _find_or_create_child(node, element)
    node.text = value

    return ET.tostring(root, encoding="unicode", xml_declaration=True)
