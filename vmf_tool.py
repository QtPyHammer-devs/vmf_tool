"""Can unpack a variety of Valve text-formats including .vmt & the Client Schema"""
#TODO: spot keys that appear more than once and pluralise
## e.g. "visgroupid" "7"\n"visgroupid" "8" = {'visgroupid': ['7', '8']}
#TODO: Functions for handling the horrible visgroup system
import io
import textwrap

def pluralise(word):
    if word.endswith('f'): # self -> selves
        return word[:-1] + 'ves'
    elif word.endswith('y'): # body -> bodies
        return word[:-1] + 'ies'
    else: # horse -> horses
        return word + 's'

def singularise(word):
    if word.endswith('ves'): # self <- selves
        return word[:-3] + 'f'
    elif word.endswith('ies'): # body <- bodies
        return word[:-3] + 'y'
    elif word.endswith('s'): # horse <- horses
        return word[:-1]
    else: # assume word is already singular
        return word

class scope:
    """Handles a string used to index a multi-dimensional dictionary, correctly reducing nested lists of dictionaries"""
    def __init__(self, strings=[]):
        self.strings = strings

    def __len__(self):
        """Returns depth, ignoring plural indexes"""
        return len(filter(lambda x: isinstance(x, str), self.strings))

    def __repr__(self):
        """Returns scope as a string that can index a deep dictionary"""
        scope_string = ''
        for string in self.strings:
            if isinstance(string, str):
                scope_string += f"['{string}']"
            elif isinstance(string, int):
                scope_string += f"[{string}]"
        return scope_string

    def add(self, new):
        self.strings.append(new)

    def reduce(self, count):
        for i in range(count):
            try:
                if isinstance(self.strings[-1], int):
                    self.strings = self.strings[:-2]
                else:
                    self.strings = self.strings[:-1]
            except:
                break


def dict_from(file): # rename
    if isinstance(file, io.TextIOWrapper):
        file_iter = file.readlines()
    elif isinstance(file, str):
        file_iter = file.split('\n')
    else:
        raise RuntimeError(f'Cannot construct dictionary from {type(file)}!')
    _dict = namespace()
    current_scope = scope([])
    previous_line = ''
    for line_no, line in enumerate(file_iter):
        try:
            line = line.rstrip('\n')
            line = textwrap.shorten(line, width=200)
            # ignore comments
            # if '//' in line:
            #     line = line.partition('//')[0]
            if line == '' or line.startswith('//'): # ignore blank / comments
                continue
            elif line =='{': # START declaration
                current_keys = eval(f'_dict{current_scope}.keys()')
                lines = pluralise(previous_line)
                if previous_line in current_keys: # NEW plural
                    exec(f'_dict{current_scope}[lines] = [_dict{current_scope}[previous_line]]')
                    exec(f'_dict{current_scope}.pop(previous_line)')
                    exec(f'_dict{current_scope}[lines].append(namespace())')
                    current_scope = scope([*current_scope.strings, lines, 1]) # why isn't this a method?
                elif lines in current_keys: # APPEND plural
                    current_scope.add(lines)
                    exec(f"_dict{current_scope}.append(namespace())")
                    current_scope.add(len(eval(f'_dict{current_scope}')) - 1)
                else: # NEW singular
                    current_scope.add(previous_line)
                    exec(f'_dict{current_scope} = namespace()')
            elif line == '}': # END declaration
                current_scope.reduce(1)
            elif '" "' in line: # KEY VALUE
                key, value = line.split('" "')
                key = key.lstrip('"')
                value = value.rstrip('"')
                exec(f'_dict{current_scope}[key] = value')
            elif line.count(' ') == 1:
                key, value = line.split()
                exec(f'_dict{current_scope}[key] = value')
            previous_line = line.strip('"')
        except:
            raise RuntimeError(f'error on line {line_no:04d}:\n{line}\n{previous_line}')
    return _dict
    
class namespace:
    """exposed __dict__ for dotted access\nuse only strings as keys"""
    def __setitem__(self, index, value):
        setattr(self, str(index), value)
    
    def __getitem__(self, index):
        return self.__dict__[str(index)]

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.keys())

    def __repr__(self):
        return f"namespace([{', '.join(self.keys())}])"

    def append(self, value):
        indices = [int(k) for k in self if str.isdigit(k)]
        if indices == []:
            indices = [0]
        self[max(indices) + 1] = value

    def index(self, key):
        """search tree for name"""
        for k, v in self.items():
            if k == key:
                key = str(key)
                if str.isdigit(key[0]) or ' ' in str(key): # is there a builtin check?
                    return f'[{self.__name__}]'
                return f'.{self.__name__}'
            elif isinstance(attr_value, namespace):
                for sub_attr in attr_value:
                    return f'.{self.__name__}{sub_attr.index(name)}'

    def items(self):
        return self.__dict__.items()
    
    def keys(self):
        return self.__dict__.keys()

    def pop(self, key):
        """remove value at given key / index"""
        return self.__dict__.pop(str(key))
    
    def values(self):
        return self.__dict__.values()


def namespace_from(nested_dict): # should be namespace.__init__ and take only dict
    out = namespace()
    for key, value in nested_dict.items():
        if isinstance(value, dict):
            setattr(out, key, namespace_from(value))
        elif isinstance(value, list):
            setattr(out, key, [namespace_from(i) for i in value])
        else:
            setattr(out, key, value)
    return out

def nested_dict_from(_namespace):
    out = dict()
    for key, value in _namespace.__dict__.items():
        if isinstance(value, namespace):
            out[key] = nested_dict_from(value)
        elif isinstance(value, list):
            out[key] = [nested_dict_from(i) for i in value]
        else:
            out[key] = value

def lines_from(_dict, tab_depth=0): # wrap with quotes
    tabs = '\t' * tab_depth
    for key, value in _dict.items():
        if isinstance(value, dict) or isinstance(value, namespace):
            yield f'{tabs}{key}\n{tabs}' + '{\n'
            for line in lines_from(value, tab_depth + 1):
                yield line
        elif isinstance(value, list):
            key = singularise(key)
            for item in value:
                yield f'{tabs}{key}\n{tabs}' + '{\n'
                for line in lines_from(item, tab_depth + 1):
                    yield line
        else:
            yield f'{tabs}"{key}" "{value}"\n'
    if tab_depth > 0:
        yield '\t' * (tab_depth - 1) + '}\n'

def export(_dict, outfile):
    """don't forget to close the file afterwards"""
    print('Exporting ... ', end='')
    for line in lines_from(_dict):
        outfile.write(line)
    print('Done!')

if __name__ == "__main__":
##    from time import time
##    times = []
##    for i in range(16):
##        start = time()
##        # v = dict_from(open('mapsrc/test.vmf'))
##        # v = dict_from(open('mapsrc/test2.vmf'))
##        v = dict_from(open('mapsrc/sdk_pl_goldrush.vmf'))
##        time_taken = time() - start
##        print(f'import took {time_taken:.3f} seconds')
##        times.append(time_taken)
##    print(f'average time: {sum(times) / 16:.3f}')
    pass

    # # filter(lambda x: x['material'] != 'TOOLS/TOOLSNODRAW' and x['material'] != 'TOOLS/TOOLSSKYBOX', all_sides)
    # # [x['classname'] for x in v.dict['entities']]
    # all_ents_with_outputs = list(filter(lambda e: 'connections' in e.keys(), v.dict['entities']))
    # all_connections = [e['connections'] for e in all_ents_with_outputs]
    # #now add all referenced targetnames to list
    # #and create a top-down map of these ents
