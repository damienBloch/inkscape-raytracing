import itertools
import re
from typing import TypeVar, Iterator, Tuple

import inkex

rgx_float = "[0-9]+(?:.[0-9])*"
rgx_name = "[a-z,_]*"
optics_pattern = re.compile(
    f"optics *: *(?P<material>{rgx_name})(?:: *(?P<num>{rgx_float}))?")


def get_optics_fields(string_: str):
    fields = re.finditer(optics_pattern, string_.lower())
    return fields


def get_description(element: inkex.BaseElement) -> str:
    if isinstance(element, inkex.Use):
        return get_description(element.href)
    else:
        for child in element.getchildren():
            if child.tag == inkex.addNS('desc', 'svg'):
                if child.text is None:
                    return ''
                else:
                    return str(child.text)
        return ''


def set_description(element: inkex.BaseElement, text: str) -> None:
    has_desc = any((child.tag == inkex.addNS('desc', 'svg')
                    for child in element.getchildren()))
    if not has_desc:
        element.add(inkex.Desc())
    for child in element.getchildren():
        if child.tag == inkex.addNS('desc', 'svg'):
            child.text = text


def clear_description(desc: str) -> str:
    """Removes text corresponding to an optical property"""

    # This will return the string converted to lower case and should be
    # changed to keep the case untouched
    new_desc = desc.lower()
    new_desc = re.sub(optics_pattern, '', new_desc)
    return new_desc


T = TypeVar('T')


def pairwise(iterable: Iterator[T]) -> Iterator[Tuple[T, T]]:
    """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)
