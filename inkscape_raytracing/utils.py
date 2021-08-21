import itertools
import re
from typing import TypeVar, Iterator, Tuple

import inkex

rgx_float = r"[-+]?(\d+([.,]\d*)?|[.,]\d+)([eE][-+]?\d+)?"
rgx_name = "[a-z,_]*"
optics_pattern = re.compile(
    f"optics *: *(?P<material>{rgx_name})(: *(?P<num>{rgx_float}))?",
    re.IGNORECASE | re.MULTILINE,
)


def get_optics_fields(string_: str):
    fields = re.finditer(optics_pattern, string_.lower())
    return fields


def get_description(element: inkex.BaseElement) -> str:
    for child in element.getchildren():
        if child.tag == inkex.addNS("desc", "svg"):
            if child.text is None:
                return ""
            else:
                return str(child.text)
    return ""


def clear_description(desc: str) -> str:
    """Removes text corresponding to an optical property"""

    new_desc = re.sub(optics_pattern, "", desc)
    return new_desc


T = TypeVar("T")


def pairwise(iterable: Iterator[T]) -> Iterator[Tuple[T, T]]:
    """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)
