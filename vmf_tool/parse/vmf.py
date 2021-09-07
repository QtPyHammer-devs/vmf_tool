import re

from . import common


# regex patterns
pattern_named_object = re.compile(r"(\w+)\s*?\{\s*?([^\{\}]*)\}\s*?")
# ^ name, key_value_pairs = match.groups()
pattern_key_value_pair = re.compile(r'(?<=")([^"]*)"\s"([^"]*)(?=")')
# ^ key, value = match.groups()
# TODO: warnings for `{`, `}` or `"` in key-value-pair
pattern_all_whitespace = re.compile(r"^\s*$")
# NOTE: ignoring comments, the last parser caught those


# TODO: test deeply and fix
def as_namespace(vmf_text: str) -> common.Namespace:
    """.vmf text -> Namespace"""
    # NOTE: recurses through nested named_objects backwards
    # TODO: record line numbers
    child_tier = dict()
    while pattern_all_whitespace.match(vmf_text) is None:
        # TODO: invalid data will loop forever!  catch this and located the invalid text!
        current_tier = dict()
        # ^ {(match.start, match.end): (match.name, Namespace(match.contents))}
        for match in pattern_named_object.finditer(vmf_text):
            # TODO: ensure the closing curly brace was at the same indentation
            # -- need to ensure it wasn't in a key or value
            # -- also need to check for incomplete files
            name, key_value_pairs = match.groups()
            namespace = common.Namespace(pattern_key_value_pair.findall(key_value_pairs))
            # TODO: ensure the whole contents are parsed
            start, end = match.span()
            for child_start, child_end in child_tier.copy():
                if start < child_start < child_end <= end:
                    child_name, child = child_tier.pop((child_start, child_end))
                    namespace[child_name] = child
            current_tier[(start, end)] = (name, namespace)
            # remove self from vmf_text, so the next iteration may be read
            vmf_text = "".join([vmf_text[:start],
                                *[(" "if c != "\n" else c) for c in vmf_text[start:end]],
                                vmf_text[end:]])
        # NOTE: not all "children" have parents
        # not all orphans have siblings
        # childlessness =/= being a child
        current_tier.update(child_tier)  # if a child's parents cannot be found, it is assumed to be top-level
        child_tier = current_tier.copy()
    return common.Namespace(current_tier.values())


def as_vmf(namespace: common.Namespace, depth: int = 0) -> str:
    """Namespace or dict --> .vmf text"""
    # NOTE: all bottom level objects should be strings!
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
            out.append(as_vmf(value, depth + 1))
        # BRANCH B-2: Plural Namespaces (maybe)
        elif isinstance(value, list):
            for child in value:
                # BRANCH C: Non-plural, duplicate key
                if isinstance(child, str):
                    out.append(f'{indent}"{key}" "{child}"\n')
                elif isinstance(child, (dict, common.Namespace)):
                    # BRANCH D: Confirmed Plural: Recurse
                    out.append(f"{indent}{key}\n{indent}" + "{\n")
                    out.append(as_vmf(child, depth + 1))
                # NOTE: if not isinstance(str, dict, common.Namespace): ignore
        else:
            # all elements must be strings before converting!
            raise RuntimeError(f"Found a non-string: {value}")
    if depth > 0:  # close BRANCH B-2 for parent
        out.append("\t" * (depth - 1) + "}\n")
    return "".join(out)
