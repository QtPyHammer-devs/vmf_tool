def yield_dict(x, depth=0):
    keys = x.keys()
    for key in keys:
        value = x[key]
        if isinstance(value, dict):
            yield depth, key
            for i in yield_dict(value, depth + 1):
                yield i
        else:
            yield depth, (key, value)

def yield_all(x, depth=0): #WHAT ABOUT EMPTY DICTS? HEADERS???
    if isinstance(x, dict):
        for y, data in yield_dict(x, depth + 1):
##            print(y, data)
            if isinstance(data, tuple):
                i = data[1]
                if isinstance(i, dict):
                    print('*** dict tuple dict')
                    for j in yield_dict(i, depth + 1):
                        yield j
                elif isinstance(i, list):
                    print('*** dict tuple list')
                    for j in yield_all(i, depth + 1):
                        yield j        
    elif isinstance(x, list):
        for i in x:
            print('*** list')
            for j in yield_all(i, depth + 1):
                yield j
                
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
    print('???')
    for depth, data in yield_all(test):
        print(depth, data)
