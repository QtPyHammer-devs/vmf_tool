from __future__ import annotations

import io
import re
from typing import Any, ItemsView, Iterable, List, Mapping, Union


def parse(file: Union[io.TextIOWrapper, io.StringIO]) -> Namespace:
    """.vmf text -> Namespace"""
    out_namespace = Namespace()
    current_scope = Scope()
    previous_line = str()
    for line_number, line in enumerate(file.readlines()):
        try:
            new_namespace = Namespace(_line=line_number)
            # new_basic_entity = ...
            current_target = current_scope.get_from(out_namespace)
            line = line.strip()  # cleanup spacing
            if line == "" or line.startswith("//"):  # ignore blank / comments
                continue
            elif line == "{":  # START declaration
                previous_line = previous_line.strip('"')
                current_target.add_attr(previous_line, new_namespace)
                current_scope.add(previous_line)
                # check if scope is aimed at a key that occured more than once
                current_target = current_scope.get_from(out_namespace)
                if isinstance(current_target, list):
                    current_scope.add(len(current_target) - 1)
                # ^ scoping into an existing list should be a method instead
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
            print(f"Error on line {line_number:04d}:\n{previous_line}\n{line}")
            raise exc
    return out_namespace


class Scope:
    """Provides a mapping into a nested object"""
    def __init__(self, tiers: list = []):
        self.tiers = tiers

    def __repr__(self) -> str:
        """returns a string which points to an attribute in a Namespace"""
        repr_strings = []
        for tier in self.tiers:
            if isinstance(tier, str):
                if re.match("^[A-Za-z_][A-Za-z_0-9]*$", tier):  # valid attribute name
                    repr_strings.append(".{tier}")
                else:  # if invalid: present as a dict key
                    repr_strings.append("['{tier}']")
            else:  # default for object keys (int, float, tuple & other hashable types)
                repr_strings.append(f"[{tier}]")
        return "".join(repr_strings)

    def add(self, tier: str):
        self.tiers.append(tier)

    def increment(self):
        """If the current tier is an index into a list, increment that index"""
        if not isinstance(self.tiers[-1], int):
            # raise an error if the current tier is not incrementable
            raise RuntimeError(f'"{self.tiers[-1]}" is not an integer')
        self.tiers[-1] += 1

    def get_from(self, namespace: Namespace) -> Any:  # getattr equivalent
        """Get the value this scope points to in 'namespace'"""
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

    def as_string(self, depth: int = 0) -> str:
        """Namespace / dictionary --> text resembling a .vmf"""
        out = list()
        indent = "\t" * depth
        for key, value in self.items():
            if key == "_line":
                continue  # ignore line numbers
            # BRANCH A: Key-Value Pair
            elif isinstance(value, str):  # key-value pair
                out.append(f"""{indent}"{key}" "{value}"\n""")
            # BRANCH B-1: Namespace / "Plural" of Namespaces
            elif isinstance(value, (dict, Namespace)):  # singular
                out.append(f"""{indent}{key}\n{indent}""" + "{\n")
                out.append(value.as_string(depth + 1))
            elif isinstance(value, list):
                for child in value:
                    if isinstance(child, str):  # key occured more that once (entity connections etc.)
                        out.append(f"""{indent}"{key}" "{child}"\n""")
                    elif isinstance(child, (dict, Namespace)):  # BRANCH B-2: Recurse
                        if len([k for k in child if k != "_line"]) > 0:  # ignore The Empty Child
                            out.append(f"""{indent}{key}\n{indent}""" + "{\n")
                            out.append(child.as_string(depth + 1))
            else:
                raise RuntimeError(f"Found a non-string: {value}")
        if depth > 0:  # close BRANCH B-2 for parent
            out.append("\t" * (depth - 1) + "}\n")
        return "".join(out)

    def items(self) -> ItemsView:
        """exposes self.__dict__"""
        return self.__dict__.items()
