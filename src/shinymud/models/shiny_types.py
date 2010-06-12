from shinymud.lib.world import World
import json

world = World.get_world()

__all__ = [
'to_bool',
'read_dict',
'write_dict',
'copy_dict',
'read_list',
'write_list',
'copy_list',
'read_area',
'write_area',
'read_json',
'write_json',

]
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
    return dict([thing.split('=') for thing in x.split(',')]),

def write_dict(val):
    return ",".join('='.join([str(k),str(v)]) for k,v in val.items())

def copy_dict(val):
    return dict(val.items())

def read_list(val):
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
        return cls.world.get_area(val)
    return val

def write_area(val):
    if isinstance(val, basestring):
        return val
    return val.name

def read_json(val):
    return json.loads(val)

def write_json(val):
    return json.dumps(val)