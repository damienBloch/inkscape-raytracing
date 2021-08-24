import re

rgx_float = r"[-+]?(\d+([.,]\d*)?|[.,]\d+)([eE][-+]?\d+)?"
rgx_name = "[a-z,_]*"
optics_pattern = re.compile(
    f"optics *: *(?P<material>{rgx_name})(: *(?P<num>{rgx_float}))?",
    re.IGNORECASE | re.MULTILINE,
)


def get_optics_fields(string_: str):
    fields = re.finditer(optics_pattern, string_)
    return fields


def clear_description(desc: str) -> str:
    """Removes text corresponding to an optical property"""

    new_desc = re.sub(optics_pattern, "", desc)
    return new_desc
