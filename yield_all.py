def yield_dict(x):
    x_keys = x.keys()
    for key in x_keys:
        yield x.pop(key)

d = {0:1, 2:3, 4:5}
y = yield_dict(d)
print(next(y))
print(d)

def yield_list(x):
    x_len = len(x)
    for i in range(x_len):
        yield x.pop(0)

l = [0, 1, 2]
y = yield_list(l)
print(l)

def yield_all(x): #WHAT ABOUT EMPTY DICTS? HEADERS???
    depth = 0
    if isinstance(x, dict):
        x_keys = x.keys()
        for key in x_keys:
            a = x.pop(keys)
            try:
                yield_all(a)
                depth += 1 #how to read depth of recursive calls?
            except StopIteration:
                depth -= 1
            except RuntimeError: #found bottom layer
                yield depth, a #needs to return: "key" "value"
    elif isinstance(x, list):
        x_len = len(x):
        for i in range(x_len):
            a = x.pop(0)
            try:
                yield_all(a)
                depth += 1 #how to read depth of recursive calls?
            except StopIteration:
                depth -= 1
            except RuntimeError: #found bottom layer
                yield depth, a #needs to return: "key" "value"

test = {'visgroups': {},
          'world': {'id': '1',
          'classname': 'worldspawn',
          'solids': [{'id': '2',
                      'sides': [
                          {'id': '3',
                           'plane': '(X Y Z) (X Y Z) (X Y Z)'
                           }]
                      }]
        }
