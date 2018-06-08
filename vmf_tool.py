##TODO:
# python 3.7 (dataclasses)
# entitiy I/O visualisation (html? html based editor?)
# .js version for web-editor
# -- does js have faster import options? (builtins)
# .vmf diff (utilise difflib) <already in hammer>
# -- export to vmf
# --- two visgroups, one for each map
# --- only diffent solids / entities
# locate overlapping brushes (especially identical planes)
# reduce brushsides (merge all brushes it makes sense to merge)

##VMT_TOOL
# Test on a .vmt for water or other complex material
# if it works create a base class, and extend each with specific methods

##QUESTIONS:
# can this code be used for .bsp entitiy lumps?
# -- are bsp entities ever multi-dimensional?
import io

def pluralise(word):
    if word.endswith('f'): # self -> selves
        return word[:-1] + 'ves'
    elif word.endswith('y'): # body -> bodies
        return word[:-1] + 'ies'
    else:
        return word + 's'

class scope:
    """Handles a string used to index a multi-dimensional dictionary, correctly reducing nested lists of dictionaries"""
    def __init__(self, strings=[]):
        self.strings = strings

    def __len__(self):
        """ returns depth, ignoring plural indexes"""
        return len(filter(lambda x: isinstance(x, str), self.strings))

    def __repr__(self):
        scope_string = ''
        for string in self.strings:
            if isinstance(string, str):
                scope_string += "['" + string + "']"
            elif isinstance(string, int):
                scope_string += "[" + str(string) + "]"
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

def singularise(word):
    if word.endswith('ves'): # self <- selves
        return word[:-3] + 'f'
    elif word.endswith('ies'): # body <- bodies
        return word[:-3] + 'y'
    elif word.endswith('s'): # horse <- horses
        return word[:-1]
    else: # assume word is already singular
        return word

def yield_dict(d, depth=0):
    keys = d.keys()
    for key in keys:
        value = d[key]
        if isinstance(value, dict):
            yield '\t' * depth + key + '\n' + '\t' * depth + '{\n'
            for output in yield_dict(value, depth + 1):
                yield output
        elif isinstance(value, list):
            key = singularise(key)
            for item in value:
                yield '\t' * depth + key + '\n' + '\t' * depth + '{\n'
                for output in yield_dict(item, depth + 1):
                    yield output
        else:
            yield '\t' * depth + f'"{key}" "{value}"' + '\n'
    if depth > 0:
        yield '\t' * (depth - 1) + '}\n'

class vmf:
    def __init__(self, file):
        if isinstance(file, io.TextIOWrapper):
            self.filename = file.name
            file_iter = file.readlines()
        elif isinstance(file, str):
            self.filename = None
            file_iter = file.split('\n')
        else:
            raise RuntimeError('Bad Input')
        self.dict = {}
        current_scope = scope([])
        line_no = 1
        previous_line = ''
        for line in file_iter:
            # print(line_no, line, end='')
            line_no +=1
            line = line.lstrip('\t')
            line = line.rstrip('\n')
            if line == '' or line.startswith('//'):
                pass
            elif line =='{':
                current_keys = eval(f'self.dict{current_scope}.keys()')
                lines = pluralise(previous_line)
                if previous_line in current_keys:
                    # print('*** SHIFT TO PLURAL ***')
                    # print(f"{current_scope}['{lines}'] = [{current_scope}['{previous_line}']]")
                    exec(f'self.dict{current_scope}[lines] = [self.dict{current_scope}[previous_line]]')
                    # print(f'self.dict{current_scope}.pop({previous_line})')
                    exec(f'self.dict{current_scope}.pop(previous_line)')
                    # print(f"{current_scope}['{lines}'].append(dict())")
                    exec(f'self.dict{current_scope}[lines].append(dict())')
                    current_scope = scope([*current_scope.strings, lines, 1])
                elif lines in current_keys:
                    # print('*** PLURAL APPEND ***')
                    current_scope.add(lines)
                    # print(f"{current_scope}.append(dict())")
                    exec(f"self.dict{current_scope}.append(dict())")
                    current_scope.add(len(eval(f'self.dict{current_scope}')) - 1)
                else:
                    current_scope.add(previous_line)
                    # print(f'self.dict{current_scope} = dict()')
                    exec(f'self.dict{current_scope} = dict()')
            elif line == '}': #'}' in line & .count() for less strict formats
                # print('*** DOWNSHIFTING ***')
                # print(current_scope, '>>>', end=' ')
                current_scope.reduce(1)
                # print(current_scope)
            elif ' ' in line:
                # print('*** KEY VALUE UPDATE ***')
                if '" "' in line:
                    key, value = line.split('" "')
                    key = key[1:]
                    value = value[:-1]
                else:
                    key, value = line.split()
                # print(f"self.dict{current_scope}['{key}'] = '{value}'")
                exec(f'self.dict{current_scope}[key] = value')
            else:
                pass
            previous_line = line

    def export(self, outfile):
        """don't forget to close the file afterwards"""
        print('Exporting ... ', end='')
        outfile.write('// This .vmf was generated by vmf_tool.py\n') # hammer discards comments
        outfile.write(f'// source: {self.filename}\n')
        for line in yield_dict(self.dict):
            outfile.write(line)
        print('Done!')

if __name__ == "__main__":
    from time import time
    times = []
    for i in range(16):
        start = time()
        # v = vmf(open('mapsrc/test.vmf'))
        # v = vmf(open('mapsrc/test2.vmf'))
        v = vmf(open('mapsrc/sdk_pl_goldrush.vmf'))
        time_taken = time() - start
        print(f'import took {time_taken:.3f} seconds')
        times.append(time_taken)
    print(f'average time: {sum(times) / 16:.3f}')


    # # filter(lambda x: x['material'] != 'TOOLS/TOOLSNODRAW' and x['material'] != 'TOOLS/TOOLSSKYBOX', all_sides)
    # # [x['classname'] for x in v.dict['entities']]
    # all_ents_with_outputs = list(filter(lambda e: 'connections' in e.keys(), v.dict['entities']))
    # all_connections = [e['connections'] for e in all_ents_with_outputs]
    # #now add all referenced targetnames to list
    # #and create a top-down map of these ents
