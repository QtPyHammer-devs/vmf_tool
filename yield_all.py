def yield_dict(x):
    x_keys = x.keys()
    for key in x_keys:
        yield x.pop(key)

def yield_list(x):
    x_len = len(x)
    for i in range(x_len):
        yield x.pop(0)

from vmf_tool import scope
def deep_yield(x, depth=0):
    keys = x.keys()
    for key in keys:
        value = x[key]
        if isinstance(value, dict):
            yield key, (depth,)
            for i in deep_yield(value, depth + 1):
                yield i
        else:
            yield key, (depth, value)

def yield_all(x, depth=0): #WHAT ABOUT EMPTY DICTS? HEADERS???
    if isinstance(x, dict):
        x_keys = x.keys()
        for key in x_keys:
            a = x.pop(keys)
            try:
                yield_all(a, depth)
                depth += 1 #how to read depth of recursive calls?
            except StopIteration:
                depth -= 1
            except RuntimeError: #found bottom layer
                yield depth, a #needs to return: "key" "value"
    elif isinstance(x, list):
        x_len = len(x)
        for i in range(x_len):
            a = x.pop(0)
            try:
                yield_all(a, depth)
                depth += 1 #how to read depth of recursive calls?
            except StopIteration:
                depth -= 1
            except RuntimeError: #found bottom layer
                yield depth, a #needs to return: "key" "value"

if __name__ == "__main__":
    d = {0:1, 2:3, 4:5}
    y = yield_dict(d)
    print(next(y))
    print(d)
    
    l = [0, 1, 2]
    y = yield_list(l)
    print(l)

    dd = {'head':{'body':{'title':'deep dict'}}}
    y = deep_yield(dd)
    for depth, data in y:
          print(depth, *data)
    next(y)
    test = {'visgroups': {},
          'world': {'id': '1',
                    'classname': 'worldspawn',
                    'solids': [{'id': '2',
                                'sides':
                                        [{'id': '3',
                                          'plane': '(X Y Z) (X Y Z) (X Y Z)'}]}]}}
