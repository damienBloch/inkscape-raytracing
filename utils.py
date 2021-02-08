import itertools
import re
from typing import TypeVar, Iterator, Tuple

import inkex

T = TypeVar('T')


def pairwise(iterable: Iterator[T]) -> Iterator[Tuple[T, T]]:
    """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


def get_description(element: inkex.BaseElement) -> str:
    for child in element.getchildren():
        if child.tag == inkex.addNS('desc', 'svg'):
            return child.text
    return ''


def get_optics_fields(string_: str):
    pattern = "optics *: *(?P<material>[a-z,_]*)(?:: *(?P<num>[0-9]+(?:.[0-9])?))?"
    fields = re.finditer(pattern, string_.lower())
    return fields


def clear_description(desc: str) -> str:
    """Removes text corresponding to an optical property"""

    new_desc = desc
    for rgx_match in get_optics_fields(desc):
        new_desc = re.sub(rgx_match, '', new_desc)
    return new_desc
