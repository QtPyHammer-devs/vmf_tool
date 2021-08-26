import re

from . import common


# regex patterns
named_object = r"(\w+)\s*?\{\s*?([^\{\}]*)\}\s*?"
# ^ name, contents = match.groups()
# NOTE: starts at the "youngest generation" (those without children)
key_value_pair = r'(?<=")([^"]*)(?=")\s(?=")([^"]*)(?=")'
# ^ key, value = match.groups()

pattern_named_object = re.compile(named_object)
pattern_key_value_pair = re.compile(key_value_pair)
# TODO: warnings for `{`, `}` or `"` in key-value-pair


def as_namespace(vmf_text: str) -> common.Namespace:
    """.vmf text -> Namespace"""
    # TODO: line number when reporting errors
    child_tier = dict()  # last tier
    current_tier = dict()
    # ^ {(match.name, match.start(), match.end()): Namespace(match.contents)}
    for match in pattern_named_object.finditer(vmf_text):
        print(f"{match = }")
        name, contents = match.groups()
        print(name, "{", contents, "}", sep="\n")
        namespace = common.Namespace({k: v for k, v in pattern_key_value_pair.findall(contents)})
        # NOTE: dict assembling oneliner handles duplicate keys poorly
        # TODO: identify children from last iteration and assimilate into namespace
        current_tier[(name, match.start(), match.end())] = namespace
        # TODO: convert block contents to namespace (recursively [via common.Scope?])
        # TODO: out_namespace[block.group("name")] = as_namespace(block.contents)
        vmf_text = vmf_text[:match.start()] + vmf_text[match.end():]
        # remove self, so parents may be parsed
        # NOTE: might have to do some match location tracking to indetify parental lineage
        # still, could do a while loop above this to match every named_object
    return common.Namespace({n: current_tier[(n, s, e)] for n, s, e in current_tier})
