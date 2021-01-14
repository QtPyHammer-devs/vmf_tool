from __future__ import annotations

import io
import re
from typing import Any, ItemsView, Iterable, List, Mapping, Union


def parse(string_or_file: Union[str, io.TextIOWrapper, io.StringIO]) -> Namespace:
    """.vmf text -> Namespace"""
    if not isinstance(string_or_file, (str, io.TextIOWrapper, io.StringIO)):
        raise RuntimeError(f"{string_or_file} is neither a string nor a file")
    if isinstance(string_or_file, str):  # make string file-like
        file = io.StringIO(string_or_file)
    else:  # it's a file
        file = string_or_file

    out_namespace = Namespace()
    # out_namespace = Namespace(world=Namespace(solid=[]), entity=[])
    current_scope = Scope()
    previous_line = str()
    for line_number, line in enumerate(file.readlines()):
        try:
            new_namespace = Namespace(_line=line_number)
            current_target = current_scope.get_from(out_namespace)
            line = line.strip()  # cleanup spacing
            if line == "" or line.startswith("//"):  # ignore blank / comments
                continue
            elif line == "{":  # START declaration
                previous_line = previous_line.strip('"')
                current_target.add_attr(previous_line, new_namespace)
                # TODO: aim scope at newly created location
                current_scope.add(previous_line)
                current_target = current_scope.get_from(out_namespace)
                if isinstance(current_target, list):
                    current_scope.add(len(current_target) - 1)
            elif line == "}":  # END declaration
                current_scope.retreat()
            elif '" "' in line:  # "KEY" "VALUE"
                key, value = line.split('" "')
                key = key.lstrip('"')
                value = value.rstrip('"')
                current_target.add_attr(key, value)
            elif line.count(" ") == 1:  # KEY VALUE
                key, value = line.split()
                current_target.add_attr(key, value)
            previous_line = line
        except Exception as exc:
            print("error on line {0:04d}:\n{1}\n{2}".format(line_number, previous_line, line))
            raise exc
    return out_namespace


def text_from(namespace: Union[dict, Namespace], depth: int = 0) -> str:
    """Namespace / dictionary --> text resembling a .vmf"""
    out = list()
    indent = "\t" * depth
    for key, value in namespace.items():
        if key == "_line":
            continue  # ignore line numbers
        # BRANCH A: Key-Value Pair
        elif isinstance(value, str):  # key-value pair
            # ^ this isn't a great way of checking for key-value pairs
            # ideally values can be any type (even iterables; vec3, dispinfo rows etc.)
            # and repr would provide a valid (recognised by stock hammer) string value
            out.append(f"""{indent}"{key}" "{value}"\n""")
        # BRANCH B-1: Namespace / "Plural" of Namespaces
        elif isinstance(value, (dict, Namespace)):  # singular
            out.append(f"""{indent}{key}\n{indent}""" + "{\n")
            out.append(text_from(value, depth + 1))
        elif isinstance(value, list):
            if len(value) == 0:
                continue  # skip empty lists
            elif isinstance(value[0], str):  # key occured more that once (entity connections etc.)
                for duplicate_keyvalue in value:
                    out.append(f"""{indent}"{key}" "{duplicate_keyvalue}"\n""")
            elif isinstance(value[0], (dict, Namespace)):
                for child_namespace in value:  # BRANCH B-2: Recurse
                    out.append(f"""{indent}{key}\n{indent}""" + "{\n")
                    out.append(text_from(child_namespace, depth + 1))
        else:
            raise RuntimeError(f"Found a non-string: {value}")
    if depth > 0:  # close BRANCH B-2 for parent
        out.append("\t" * (depth - 1) + "}\n")
    return "".join(out)


class Scope:
    """Array of indices into a nested array"""
    def __init__(self, tiers: list = []):
        self.tiers = tiers

    def __repr__(self) -> str:
        """returns a string which points to an attribute in a Namespace"""
        repr_strings = []
        for tier in self.tiers:
            if isinstance(tier, str):
                if re.match("^[A-Za-z_][A-Za-z_0-9]*$", tier):
                    repr_strings.append(".{tier}")
                else:  # tier is not a valid attribute
                    repr_strings.append("['{tier}']")
            else:
                repr_strings.append(f"[{tier}]")
        return "".join(repr_strings)

    def add(self, tier: str):
        """Go a layer deeper"""
        self.tiers.append(tier)

    def increment(self):
        if not isinstance(self.tiers[-1], int):
            raise RuntimeError(f'"{self.tiers[-1]}" is not an integer')
        self.tiers[-1] += 1

    def get_from(self, namespace: Namespace) -> Any:  # getattr equivalent
        """Get the value this scope points at in 'namespace'"""
        target = namespace
        for tier_number, tier in enumerate(self.tiers):
            try:
                target = target[tier]
            except KeyError:
                raise KeyError(f"Scope({self.tiers}) tier #{tier_number} ({tier}) does not exist in {target}")
        return target

    def retreat(self):
        """Retreat up 1 tier (2 tiers for plurals)"""
        popped = self.tiers.pop(-1)
        if isinstance(popped, int):
            self.tiers.pop(-1)

    def remove_from(self, namespace: Namespace):  # delattr equivalent
        """Delete the item this scope points at from 'namespace'"""
        # NOTE: this methods is unused / untested!
        target = namespace
        for i, tier in enumerate(self.tiers):
            if i == len(self.tiers) - 1:  # must set from tier above
                target.pop(tier)
            else:
                target = target[tier]
        # stop pointing at deleted index
        self.retreat()
        # unsure what will happen when deleting an item from a plural
        # also unsre what SHOULD happen when deleting an item from a plural

    def set_in(self, namespace: Namespace, value: Any):  # setattr equivalent
        """Set the value this scope points at in 'namespace' to 'value'"""
        target = namespace
        for i, tier in enumerate(self.tiers):
            if i == len(self.tiers) - 1:  # must set from tier above
                target[tier] = value  # could be creating this value
            else:
                target = target[tier]


class Namespace:
    """Maps objects like a dictionary, all keys are strings.
    Values can be accessed as class attributes.
    If a key is not a valid attribute name, if can be used like a dictionary key."""
    def __init__(self, **presets: Mapping[str, Union[Namespace, List, str]]):
        # Namespace(key=value, key2=value2)
        for key, value in presets.items():
            if isinstance(value, dict):
                self[key] = Namespace(value)
            elif isinstance(value, list):
                self[key] = [Namespace(i) for i in value]
            else:
                self[key] = value

    def __setitem__(self, index: Any, value: Any):
        setattr(self, str(index), value)

    def __getitem__(self, index: Any) -> Any:
        return self.__dict__[str(index)]

    def __iter__(self) -> Iterable:
        return iter(self.__dict__.keys())

    def __len__(self) -> int:
        return len(self.__dict__.keys())

    def __repr__(self) -> str:
        attributes: List[str] = list()
        for attribute_name, attr in self.items():
            if not re.match("^[A-Za-z_][A-Za-z_0-9]*$", attribute_name):
                attribute_name = f'"{attribute_name}"'  # invalid attribute names in quotes
            attributes.append(attribute_name)
        return f"<Namespace({', '.join(attributes)})>"

    def add_attr(self, attr, value):
        if hasattr(self, attr):
            if isinstance(self[attr], list):
                self[attr].append(value)
            else:
                self[attr] = [self[attr], value]
        else:
            self[attr] = value

    def items(self) -> ItemsView:
        """exposes self.__dict__"""
        return self.__dict__.items()
