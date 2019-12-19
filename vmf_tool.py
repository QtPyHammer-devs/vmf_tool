"""Can unpack a variety of Valve text-formats including .vmt & the Client Schema"""
# TODO: Functions for handling the horrible visgroup system
# e.g. "visgroupid" "7"\n"visgroupid" "8" = {'visgroupid': ['7', '8']}
import io
import re
import textwrap


def pluralise(word):
    if word.endswith('f'): # self -> selves
        return word[:-1] + 'ves'
    elif word.endswith('y'): # body -> bodies
        return word[:-1] + 'ies'
    elif word.endswith('ex'): # vertex -> vertices
        return word[:-2] + 'ices'
    else: # side -> sides
        return word + 's'


def singularise(word):
    if word.endswith('ves'): # self <- selves
        return word[:-3] + 'f'
    elif word.endswith('ies'): # body <- bodies
        return word[:-3] + 'y'
    elif word.endswith('ices'): # vertex <- vertices
        return word[:-4] + 'ex'
    # in the face of ambiguity, refuse the temptation to guess
    elif word.endswith('s'): # side <- sides
        return word[:-1]
    else:
        return word # assume word is already singular


class namespace: # VMF COULD OVERLOAD METHODS
    """Nested Dicts -> Nested Objects"""
    def __init__(self, nested_dict=dict()):
        for key, value in nested_dict.items() if isinstance(nested_dict, dict) else nested_dict.__dict__.items():
            if isinstance(value, dict):
                self[key] = namespace(value)
            elif isinstance(value, list):
                self[key] = [namespace(i) for i in value]
            else:
                self[key] = value

    def __setitem__(self, index, value):
        setattr(self, str(index), value)

    def __getitem__(self, index):
        return self.__dict__[str(index)]

    def __iter__(self):
        return iter(self.__dict__.keys())

    def __len__(self):
        return len(self.__dict__.keys())

    def __repr__(self):
        attrs = []
        for attr_name, attr in self.items():
            if " " in attr_name:
                attr_name = "{}".format(attr_name)
            attr_string = "{}: {}".format(attr_name, type(attr))
            attrs.append(attr_string)
        return "<namespace({})>".format(", ".join(attrs))

    def items(self):
        for k, v in self.__dict__.items():
            yield (k, v)


class scope:
    """Array of indices into a nested array"""
    def __init__(self, tiers=[]):
        self.tiers = tiers

    def __repr__(self):
        repr_strings = []
        for tier in self.tiers:
            if isinstance(tier, str):
                if " " in tier or tier[0].lower() not in "abcdefghijklmnopqrstuvwxyz":
                    repr_strings.append("['{}']".format(tier))
                else:
                    repr_strings.append(".{}".format(tier))
            else:
                repr_strings.append("[{}]".format(tier))
        return "".join(repr_string)

    def add(self, tier):
        """Go a layer deeper"""
        self.tiers.append(tier)

    def increment(self): # does not check if tiers[-1] is an integer
        self.tiers[-1] += 1

    def get_from(self, nest):
        """Gets the item stored in nest which this scope points at"""
        target = nest
        for tier in self.tiers:
            target = target[tier]
        return target

    def retreat(self):
        """Retreat up 1 tier (2 tiers for plurals)"""
        popped = self.tiers.pop(-1)
        if isinstance(popped, int):
            self.tiers.pop(-1)

    def remove_from(self, nest): # used for changing singulars into plurals
        """Delete the item stored in nest which this scope points at"""
        target = nest
        for i, tier in enumerate(self.tiers):
            if i == len(self.tiers) - 1: # must set from tier above
                target.pop(tier)
            else:
                target = target[tier]
        # stop pointing at deleted index
        self.retreat()
        # unsure what will happen when deleting an item from a plural
        # also unsre what SHOULD happen when deleting an item from a plural

    def set_in(self, nest, value):
        """Sets the item stored in nest which this scope points at to value"""
        target = nest
        for i, tier in enumerate(self.tiers):
            if i == len(self.tiers) - 1: # must set from tier above
                target[tier] = value # could be creating this value
            else:
                target = target[tier]


# REGULAR EXPRESSIONS
re_closer = "}"
re_float = "-?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?"
re_opener = "{"
re_plane = '^[ \t]+"plane" "((\(%s ?){3}\) ?){3}"' % re_float # BROKEN
re_quoted = '("([^"]|"")*")'
    

def parse_lines(iterable):
    """String or .vmf file to nested namespace"""
    namespace_nest = namespace({})
    current_scope = scope([])
    previous_line = ''
    for line_number, line in enumerate(iterable):
        try:
            new_namespace = namespace({'_line': line_number})
            line = line.rstrip('\n')
            line = textwrap.shorten(line, width=2000) # cleanup spacing, broke at 200+ chars, not the right tool for the job
            if line == '' or line.startswith('//'): # ignore blank / comments
                continue
            elif line =='{': # START declaration
                current_keys = eval("namespace_nest{}.__dict__.keys()".format(current_scope))
                plural = pluralise(previous_line)
                if previous_line in current_keys: # NEW plural
                    exec("namespace_nest{}[plural] = [namespace_nest{}[previous_line]]".format(current_scope, current_scope))
                    exec("namespace_nest{}.__dict__.pop(previous_line)".format(current_scope))
                    exec("namespace_nest{}[plural].append(new_namespace)".format(current_scope))
                    current_scope = scope([*current_scope.strings, plural, 1]) # why isn't this a method?
                elif plural in current_keys: # APPEND plural
                    current_scope.add(plural)
                    exec("namespace_nest{}.append(new_namespace)".format(current_scope))
                    current_scope.add(len(eval("namespace_nest{}".format(current_scope))) - 1)
                else: # NEW singular
                    current_scope.add(previous_line)
                    exec("namespace_nest{} = new_namespace".format(current_scope))
            elif line == '}': # END declaration
                current_scope.reduce(1)
            elif '" "' in line: # KEY VALUE
                key, value = line.split('" "')
                key = key.lstrip('"')
                value = value.rstrip('"')
                exec("namespace_nest{}[key] = value".format(current_scope))
            elif line.count(' ') == 1:
                key, value = line.split()
                exec("namespace_nest{}[key] = value".format(current_scope))
            previous_line = line.strip('"')
        except Exception as exc:
            print("error on line {0:04d}:\n{1}\n{2}".format(line_number, line, previous_line))
            raise exc
    return namespace_nest


def lines_from(_dict, tab_depth=0): # rethink & refactor
    """Takes a nested dictionary (which may also contain lists, but not tuples)
from this a series of strings resembling valve's text format used in .vmf files
are generated approximately one line at a time"""
    tabs = '\t' * tab_depth
    for key, value in _dict.items():
        if isinstance(value, (dict, namespace)): # another nest
            value = (value,)
        elif isinstance(value, list): # collection of plurals
            key = singularise(key)
        else: # key-value pair
            if key == "_line":
                continue
            yield """{}"{}" "{}"\n""".format(tabs, key, value)
            continue
        for item in value:
            yield """{}{}\n{}""".format(tabs, key, tabs) + "{\n" # go deeper
            for line in lines_from(item, tab_depth + 1): # recurse down
                yield line
    if tab_depth > 0:
        yield "\t" * (tab_depth - 1) + "}\n" # close the plural index / namespace


def export(nest, outfile):
    """Don't forget to close the file afterwards!"""
    print("Exporting {} ... ".format(outfile.name), end="")
    for line in lines_from(nest):
        outfile.write(line) # writing one line at a time seems wasteful
        # ''.join([line for line in lines_from(_dict)]) also works
    print("Done!")
