##TODO:
# entitiy I/O visualisation (html? html based editor?)
# .js version for web-editor
# -- does js have faster import options? (builtins)
# locate overlapping brushes (especially duplicates and potential z-fighting)
# reduce brushsides (merge all brushes it makes sense to merge)

##QUESTIONS:
# can this code be used for .bsp entitiy lumps?
# -- are bsp entities ever multi-dimensional?
# can this code be used for .vmt?
import io

def pluralise(word):
    if word.endswith('f'): # self -> selves
        return word[:-1] + 'ves'
    elif word.endswith('y'): # body -> bodies
        return word[:-1] + 'ies'
    else:
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

def vmf_lines(vmf_dict, tab_depth=0):
    tabs = '\t' * tab_depth
    for key, value in vmf_dict.items():
        if isinstance(value, dict):
            yield f'{tabs}{key}\n{tabs}' + '{\n'
            for line in vmf_lines(value, tab_depth + 1):
                yield line
        elif isinstance(value, list):
            key = singularise(key)
            for item in value:
                yield f'{tabs}{key}\n{tabs}' + '{\n'
                for line in vmf_lines(item, tab_depth + 1):
                    yield line
        else:
            yield f'{tabs}"{key}" "{value}"' + '\n'
    if tab_depth > 0:
        yield '\t' * (tab_depth - 1) + '}\n'

def vmf_to_dict(file):
    if isinstance(file, io.TextIOWrapper):
        file_iter = file.readlines()
    elif isinstance(file, str):
        file_iter = file.split('\n')
    else:
        raise RuntimeError(f'Cannot construct dictionary from {type(file)}!')
    vmf_dict = dict()
    current_scope = scope([])
    previous_line = ''
    for line in file_iter:
        line = line.lstrip('\t')
        line = line.rstrip('\n')
        if line == '' or line.startswith('//'):
            continue # don't modify previous line
        elif line =='{':
            current_keys = eval(f'vmf_dict{current_scope}.keys()')
            lines = pluralise(previous_line)
            if previous_line in current_keys:
                exec(f'vmf_dict{current_scope}[lines] = [vmf_dict{current_scope}[previous_line]]')
                exec(f'vmf_dict{current_scope}.pop(previous_line)')
                exec(f'vmf_dict{current_scope}[lines].append(dict())')
                current_scope = scope([*current_scope.strings, lines, 1]) # why isn't this a method?
            elif lines in current_keys:
                current_scope.add(lines)
                exec(f"vmf_dict{current_scope}.append(dict())")
                current_scope.add(len(eval(f'vmf_dict{current_scope}')) - 1)
            else:
                current_scope.add(previous_line)
                exec(f'vmf_dict{current_scope} = dict()')
        elif line == '}':
            current_scope.reduce(1)
        elif ' ' in line:
            if '" "' in line:
                key, value = line.split('" "')
                key = key[1:]
                value = value[:-1]
            else:
                key, value = line.split()
            exec(f'vmf_dict{current_scope}[key] = value')
        previous_line = line
    return vmf_dict

def export_vmf(vmf_dict, outfile):
    """don't forget to close the file afterwards"""
    print('Exporting ... ', end='')
    for line in vmf_lines(vmf_dict):
        outfile.write(line)
    print('Done!')

if __name__ == "__main__":
##    from time import time
##    times = []
##    for i in range(16):
##        start = time()
##        # v = vmf_to_dict(open('mapsrc/test.vmf'))
##        # v = vmf_to_dict(open('mapsrc/test2.vmf'))
##        v = vmf_to_dict(open('mapsrc/sdk_pl_goldrush.vmf'))
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
