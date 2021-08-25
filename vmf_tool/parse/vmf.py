import re

from . import common


# regex patterns
named_object = r"(?P<name>[_a-zA-Z][_a-zA-Z0-9])?\n?\{\n?(?P<contents>.*)\}\s?\n?"
quoted_string = r'(?<=")[^"]*(?=")'

pattern_named_object = re.compile(named_object)
pattern_quoted_string = re.compile(quoted_string)
# NOTE: a key-value pair consists of 2 quoted strings
# -- usually: `\t"key" "value"\n`
# many variations can occur:
# * newline in key
# * newline in value
# * CRLF line ending
# * different spacing & indentation
# * invalid character in value `{`, `}` or `"`
# ^ warnings for this last case would be great
# -- key could be checked against a list of keywords, but we'd like to catch everything


def as_namespace(vmf_text: str) -> common.Namespace:
    """.vmf text -> Namespace"""
    out_namespace = common.Namespace()
    # TODO: line count when reporting errors
    for block in pattern_named_object.findall(vmf_text):
        ...
        # TODO: convert block contents to namespace (recursively [via common.Scope?])
        # TODO: out_namespace[block.name] = as_namespace(block.contents)
    return out_namespace
