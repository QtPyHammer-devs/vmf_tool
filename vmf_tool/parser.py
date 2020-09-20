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

    namespace = Namespace()
    current_scope = Scope()
    previous_line = str()
    for line_number, line in enumerate(file.readlines()):
        try:
            new_namespace = Namespace(_line=line_number)
            current_target = current_scope.get_from(namespace)
            line = line.strip()  # cleanup spacing
            if line == "" or line.startswith("//"):  # ignore blank / comments
                continue
            elif line == "{":  # START declaration
                current_keys = current_target.__dict__.keys()
                plural = pluralise(previous_line)
                previous_line = previous_line.strip('"')
                if previous_line in current_keys:  # NEW plural
                    current_target[plural] = [current_target[previous_line]]  # create plural from old singular
                    current_target.__dict__.pop(previous_line)  # delete singular
                    current_target[plural].append(new_namespace)  # second entry
                    current_scope.add(plural)
                    current_scope.add(1)  # point at new_namespace
                elif plural in current_keys:  # APPEND plural
                    current_scope.add(plural)  # point at plural
                    current_scope.get_from(namespace).append(new_namespace)
                    current_scope.add(len(current_scope.get_from(namespace)) - 1)  # current index in plural
                else:  # NEW singular
                    current_scope.add(previous_line)
                    current_scope.set_in(namespace, new_namespace)
            elif line == "}":  # END declaration
                current_scope.retreat()
            elif '" "' in line:  # "KEY" "VALUE"
                key, value = line.split('" "')
                key = key.lstrip('"')
                value = value.rstrip('"')
                current_target[key] = value
            elif line.count(" ") == 1:  # KEY VALUE
                key, value = line.split()
                current_target[key] = value
            previous_line = line
        except Exception as exc:
            print("error on line {0:04d}:\n{1}\n{2}".format(line_number, previous_line, line))
            raise exc
    return namespace


def text_from(_dict: Union[dict, Namespace], tab_depth: int = 0) -> str:
    """Namespace / dictionary --> text resembling a .vmf"""
    out = list()
    tabs = "\t" * tab_depth
    for key, value in _dict.items():
        if key == "_line":
            continue
        elif isinstance(value, str):  # key-value pair
            out.append(f"""{tabs}"{key}" "{value}"\n""")
            continue
        elif isinstance(value, (dict, Namespace)):  # another nest
            value = (value,)
        elif isinstance(value, (list, tuple)):  # collection of plurals
            key = singularise(key)
        else:
            raise RuntimeError(f"Found a non-string: {value}")
        for item in value:  # go a layer deeper
            out.append(f"""{tabs}{key}\n{tabs}""" + "{\n")
            out.append(text_from(item, tab_depth + 1))
    if tab_depth > 0:  # close the plural index / namespace
        out.append("\t" * (tab_depth - 1) + "}\n")
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
    def __init__(self, **presets: Mapping[str, Any]):
        # absorb presets
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
        """based on collections.namedtuple's repr method"""
        attributes: List[str] = list()
        for attribute_name, attr in self.items():
            if not re.match("^[A-Za-z_][A-Za-z_0-9]*$", attribute_name):
                # invalid attribute names are placed in quotes
                attribute_name = f'"{attribute_name}"'
            attribute_string = f"{attribute_name}: {attr.__class__.__name__}"
            attributes.append(attribute_string)
        return f"<Namespace({', '.join(attributes)})>"

    def items(self) -> ItemsView:
        """exposes self.__dict__"""
        return self.__dict__.items()


def pluralise(word: str) -> str:
    if word.endswith("f"):  # self -> selves
        return word[:-1] + "ves"
    elif word.endswith("y"):  # body -> bodies
        return word[:-1] + "ies"
    elif word.endswith("ex"):  # vertex -> vertices
        return word[:-2] + "ices"
    else:  # side -> sides
        return word + "s"


def singularise(word: str) -> str:
    if word.endswith("ves"):  # self <- selves
        return word[:-3] + "f"
    elif word.endswith("ies"):  # body <- bodies
        return word[:-3] + "y"
    elif word.endswith("ices"):  # vertex <- vertices
        return word[:-4] + "ex"
    elif word.endswith("s"):  # side <- sides
        return word[:-1]
    else:
        return word  # assume word is already singular
        # "in the face of ambiguity, refuse the temptation to guess" - PEP 20
