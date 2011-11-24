from shinymud.lib.world import World
import json

world = World.get_world()

def to_bool(val):
    """Take a string representation of true or false and convert it to a boolean
   value. Returns a boolean value or None, if no corresponding boolean value
    exists.
    """
    bool_states = {'true': True, 'false': False, '0': False, '1': True}
    if not val:
        return None
    if isinstance(val, bool):
        return val
    val = str(val)
    val = val.strip().lower()
    return bool_states.get(val)

def read_dict(val):
    # val is a string like "foo=bar,name=fred"
    # return {'foo':'bar', 'name':'fred'}
    return dict([thing.split('=') for thing in val.split(',')])

def write_dict(val):
    return ",".join('='.join([str(k),str(v)]) for k,v in val.items())

def copy_dict(val):
    return dict(val.items())

def read_list(val):
    if isinstance(val, list):
        return val
    if not val:
        return []
    return val.split(',')

def write_list(val):
    if not val:
        return None
    return ','.join(map(str,val))

def copy_list(val):
    return val[:]

def read_area(val):
    if isinstance(val, basestring):
        return world.get_area(val)
    return val

def write_area(val):
    if isinstance(val, basestring):
        return val
    return val.name

def read_merchandise(val):
    return [read_dict(each) for each in val.split('<>')]

def write_merchandise(val):
    lst = []
    for dicts in val:
        if dicts.get('keywords'):
            del dicts['keywords']
        lst.append(write_dict(dicts))
    return '<>'.join(lst)

def read_json(val):
    return json.loads(val)

def write_json(val):
    return json.dumps(val)

def write_model(val):
    if isinstance(val, int):
        return val
    return val.dbid    

def read_int_dict(val):
    d = {}
    if val:
        for a in val.split(','):
            key, val = a.split('=')
            d[key] = int(val)
    return d

def write_int_dict(val):
    s = []
    if val:
        for key, val in val.items():
            s.append("%s=%s" % (str(key), str(val)))
    return ",".join(s)

def read_damage(val):
    dmg = []
    if val:
        for d in val.split('|'):
            dmg.append(Damage(d))
    return dmg

def write_damage(val):
    return '|'.join([str(d) for d in val])

def read_channels(val):
    d = {}
    for pair in val.split(','):
        k,v = pair.split('=')
        d[k] = to_bool(v)
    return d    

def read_location(val):
    #loc == 'area,id'
    loc = val.split(',')
    return world.get_location(loc[0], loc[1])

def write_location(val):
    if val:
        return '%s,%s' % (val.area.name, val.id)
    return None

def read_int(val):
    try:
        r = int(val)
    except ValueError:
        r = 0
    return r

def read_float(val):
    try:
        r = float(val)
    except ValueError:
        r = 0.0
    return r
