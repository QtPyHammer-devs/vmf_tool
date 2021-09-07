"""Singular: a key in a namespace, alone in it's tier
Plural: a duplicate key which shares a tier with an identically named entry"""
from __future__ import annotations

import re
from typing import Any, ItemsView, Iterable, List, Mapping, Tuple


# Glossary
# singular: a key in a namespace, alone in it's tier
# plural: a duplicate key which shares a tier with an identically named entry
class Namespace:
    """Maps objects like a dictionary, all keys are strings.
    Values can be accessed as class attributes.
    If a key is not a valid attribute name, if can be used like a dictionary key."""
    # Namespace(List[Union[Namespace, Any]], Namespace, Any)
    # NOTE: a list inside a namespace is assumed to be a plural / duplicate key!

    def __init__(self, *args: List[Tuple[str, Any]], **presets: Mapping[str, Any]):
        # args = Namespace([("key", value), ("key", "value2"), ("key2", value)])
        # kwargs = Namespace(key=value, key2=value2)
        for kvp_list in (*args, presets.items()):
            for key, value in kvp_list:
                self[key] = value

    # TODO: def __delitem__(self, key: str):

    def __setitem__(self, key: str, value: Any):
        if key in self:  # make plural
            old_value = getattr(self, key)
            if isinstance(old_value, list):
                value = old_value
            else:
                value = [old_value, value]
        setattr(self, key, value)

    def __getitem__(self, key: str) -> Any:
        return self.__dict__[key]

    def __iter__(self) -> Iterable:
        return iter(self.__dict__.keys())

    def __len__(self) -> int:
        return len(self.__dict__.keys())

    def __repr__(self) -> str:
        # TODO: consider string size and communicate depth better
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

    def update(self, *args: List[Tuple[str, Any]], **kwargs: Mapping[str, Any]):
        for kvp_list in (*args, kwargs.items()):
            for key, value in kvp_list:
                self[key] = value

    def items(self) -> ItemsView:
        """exposes self.__dict__"""
        return self.__dict__.items()
