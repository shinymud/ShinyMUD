class CommandRegister(object):
    
    def __init__(self):
        self.commands = {}
    
    def __getitem__(self, key):
        return self.commands.get(key)
    
    def register(self, func, aliases):
        for alias in aliases:
            self.commands[alias] = func

class ModelRegister(object):
    def __init__(self):
        self.models = {}

    def register(self, model):
        self.models[model.db_table_name] = model
    
    def values(self):
        return self.models.values()
    
    def get(self, key, default=None):
        return self.models.get(key,default)
    
class IntRegister(object):
    """Keeps a dictionary of id:integer pairs, so we can keep track
    of the things affecting a particular attribute.
    """
    def __init__(self):
        self.things = {}
        self.next_id = 0
        self.changed = True
        self._calculated = None

    def evaluate(self, thing):
        # evaluate the value of the thing
        # This should be overloaded by baseclasses if 
        # they have something other than an int.
        return int(thing)

    def __getitem__(self, key):
        return self.things.get(key)

    def __setitem__(self, key, val):
        self.things[key] = val
        self.changed = True

    def append(self, val):
        this_id = self.next_id
        self.things[this_id] = val
        self.next_id += 1
        self.changed = True
        return this_id

    def __delitem__(self, key):
        if key in self.things:
            del self.things[key]
            self.changed = True

    def calculate(self):
        if self.changed:        
            self._calculated = 0
            for val in self.things.values():
                self._calculated += self.evaluate(val)
            self.changed = False
        return self._calculated


class DictRegister(IntRegister):
    """Keeps a dictionary of id:(group, val) pairs,
    and returns a dictionary of group:sum(val) pairs.
    """
    def evaluate(self, thing):
        return thing

    def calculate(self):
        if self.changed:
            self._calculated = {}
            for value in self.things.values():
                key, val = self.evaluate(value)
                self._calculated[key] = self._calculated.get(key,0) + val
        return self._calculated


class DamageRegister(DictRegister):
    """Special case of DictRegister, keeps dictionary of id:Damage pairs,
    and returns a dictionary of Damage.type:sum(calculated_damage) pairs.
    """
    changed = property((lambda x: True), (lambda x, y: None))
    def evaluate(self, thing):
        key = thing.type
        if thing.probability == 100 or thing.probability <= randint(1,100):
            val = randint(thing.range[0], thing.range[1])
        else:
            val = 0
        return key, val

    def display(self):
        types = {}
        mins = {}
        maxs = {}
        for value in self.things.values():
            mins[value.type] = mins.get(value.type, 0) + value.range[0]
            maxs[value.type] = maxs.get(value.type, 0) + value.range[1]
            types[value.type] = True
        return [(t, mins[t], maxs[t]) for t in types.keys()]
