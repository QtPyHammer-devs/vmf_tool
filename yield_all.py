def yield_dict(x, depth=0):
    keys = x.keys()
    for key in keys:
        value = x[key]
        if isinstance(value, dict):
            yield key, depth
            for i in deep_yield(value, depth + 1):
                yield i
        else:
            yield key, (depth, value)

def yield_all(x, depth=0): #WHAT ABOUT EMPTY DICTS? HEADERS???
    if isinstance(x, dict):
        yield_dict(x, depth + 1)
    elif isinstance(x, list):
        for i in x:
            if isinstance(i, list) or isinstance(i, dict):
                yield yield_all(i, depth + 1)
            else:
                yield i, depth

if __name__ == "__main__":
    dd = {'head':{'body':{'title':'deep dict'}}}
    for depth, data in yield_dict(dd):
        if isinstance(data, tuple):
            print('\t' * depth, '"{}" "{}"'.format(*data), sep='')
        else:
            print('\t' * depth, data, sep='')
            
    test = {'visgroups': {},
          'world': {'id': '1',
                    'classname': 'worldspawn',
                    'solids': [{'id': '2',
                                'sides':
                                        [{'id': '3',
                                          'plane': '(X Y Z) (X Y Z) (X Y Z)'}]}]}}
    for depth, data in yield_all(test):
        print(depth, data)
