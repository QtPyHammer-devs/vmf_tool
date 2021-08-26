import re

from . import common


# regex patterns
pattern_named_object = re.compile(r"(\w+)\s*?\{\s*?([^\{\}]*)\}\s*?")
# ^ name, contents = match.groups()
# NOTE: starts at the "youngest generation" (those without children)
pattern_key_value_pair = re.compile(r'(?<=")([^"]*)(?=")\s(?=")([^"]*)(?=")')
# ^ key, value = match.groups()
# TODO: warnings for `{`, `}` or `"` in key-value-pair
pattern_all_whitespace = re.compile(r"^\s*$")
# NOTE: ignoring comments, the last parser caught those


def as_namespace(vmf_text: str) -> common.Namespace:
    """.vmf text -> Namespace"""
    # TODO: line number when reporting errors
    child_tier = dict()  # final namespace is assembled innermost object first
    while pattern_all_whitespace.match(vmf_text) is not None:
        # TODO: invalid data will loop forever!  catch this and located the invalid text!
        current_tier = dict()
        # ^ {(match.name, match.start, match.end): Namespace(match.contents)}
        for match in pattern_named_object.finditer(vmf_text):
            print(f"{match = }")
            name, contents = match.groups()
            print(name, "{", contents, "}", sep="\n")
            namespace = common.Namespace(pattern_key_value_pair.findall(contents))
            # TODO: ensure all key value pairs are collected
            start, end = match.span()
            namespace.update([child_tier[(s, e)] for s, e in child_tier if start < s < e <= end])
            # TODO: remove children from the pool when their parents collect them
            current_tier[(start, end)] = (name, namespace)
            # replace self with whitespace, so parents may be parsed
            vmf_text[start:end] = "".join([(" "if c != "\n" else "\n") for c in vmf_text[start:end]])
        # TODO: ensure no child is left behind
        child_tier = current_tier.copy()
    return common.Namespace(current_tier.values())


def as_vmf(namespace: common.Namespace, depth: int = 0) -> str:
    """Namespace / dict --> .vmf text"""
    out = list()
    indent = "\t" * depth
    # TODO: convert non-dict/list/Namespace values to strings for writing
    for key, value in namespace.items():
        if key == "_line":
            continue  # ignore line numbers
        # BRANCH A: Key-Value Pair
        elif isinstance(value, str):
            out.append(f'{indent}"{key}" "{value}"\n')
        # BRANCH B-1: Singular Namespace
        elif isinstance(value, (dict, common.Namespace)):
            out.append(f"{indent}{key}\n{indent}" + "{\n")
            out.append(value.as_string(depth + 1))
        # BRANCH B-2: Plural Namespaces (maybe)
        elif isinstance(value, list):
            for child in value:
                # BRANCH C: Non-plural, duplicate key
                if isinstance(child, str):
                    # e.g. brush entity "solid" type key-value pair + solid Namespace(s)
                    out.append(f'{indent}"{key}" "{child}"\n')
                elif isinstance(child, (dict, common.Namespace)):
                    # BRANCH D: Confirmed Plural: Recurse
                    if len([k for k in child if k != "_line"]) > 0:  # ignoring line numbers
                        out.append(f"{indent}{key}\n{indent}" + "{\n")
                        out.append(child.as_string(depth + 1))
        else:
            # all elements must be strings before converting!
            raise RuntimeError(f"Found a non-string: {value}")
    if depth > 0:  # close BRANCH B-2 for parent
        out.append("\t" * (depth - 1) + "}\n")
    return "".join(out)
