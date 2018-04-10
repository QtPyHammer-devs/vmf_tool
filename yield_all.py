from vmf_tool import singularise

def yield_dict(d, depth=0):
    keys = d.keys()
    for key in keys:
        value = d[key]
        if isinstance(value, dict):
            yield '\t' * depth + key + '\n' + '\t' * depth + '{\n'
            for output in yield_dict(value, depth + 1):
                yield output
        elif isinstance(value, list):
            yield '\t' * depth, singularise(key)
            for output in yield_list(value, depth + 1):
                yield output            
        else:
            yield '\t' * depth + '"{}" "{}"'.format(key, value)
    #not to end key value lists
    yield '\t' * depth + '}\n'

def yield_list(l, depth=0):
    for item in list:
        if isinstance(item, dict):
            yield depth, item
            for output in yield_dict(item, depth + 1):
                print("*** dict within list")
                yield output
        elif isinstance(item, list):
            yield depth, singularise(item)
            for output in yield_list(item, depth + 1):
                yield output

if __name__ == "__main__":
    dd = {'head':{'body':{'title':'deep dict'}}}
    for line in yield_dict(dd):
        print(line)
            
    test = {'visgroups': {},
          'world': {'id': '1',
                    'classname': 'worldspawn',
                    'solids': [{'id': '2',
                                'sides':
                                        [{'id': '3',
                                          'plane': '(X Y Z) (X Y Z) (X Y Z)'}]}]}}
    for line in yield_dict(test):
        print(line)
