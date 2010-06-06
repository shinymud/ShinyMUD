from shinymud.lib.world import World
from shinymud.lib.registers import ModelRegister

model_list = ModelRegister()

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
    # val ="foo=bar,name=fred"
    # return {'foo':'bar', 'name':'fred'}
    return dict([thing.split('=') for thing in x.split(',')]),

def write_dict(val):
    return ",".join('='.join([str(k),str(v)]) for k,v in val.items())

def read_list(val):
    if not val:
        return []
    return val.split(',')

def write_list(val):
    return ','.join(val)


class Column(object):
    def __init__(self, name, **args):
        self.name = name
        self.type = args.get('type', 'TEXT')
        self.default = args.get('default')
        self.null = args.get('null', True)
        self.primary_key = args.get('primary_key', False)
        self.foreign_key = args.get('foreign_key') # (model, column)
        self.unique = args.get('unique', False)
        self.read = args.get('read', unicode)
        self.write = args.get('write', unicode)
        self.cascade = args.get('cascade')
    
    def __str__(self):
        sql_string = []
        sql_string.append(self.name)
        sql_string.append(self.type)
        if self.primary_key: 
            sql_string.append("PRIMARY KEY")
        else:
            if self.foreign_key:
                sql_string.append("REFERENCES %s(%s)" % (self.foreign_key[0].db_table_name, self.foreign_key[1]))
            if self.unique: 
                sql_string.append('UNIQUE')
            if not self.null:
                sql_string.append('NOT NULL')
            if self.cascade:
                sql_string.append('CASCADE %s' % str(self.cascade))
        return unicode(" ".join(sql_string))
    

# primary_key, null, unique, cascade_on_delete, references, 
class Model(object):
    world = World.get_world()
    db_table_name = None
    db_columns = [
        Column('dbid',
            primary_key=True, 
            null=False, 
            type='INTEGER',
            read=int,
            write=int
        )
    ]
    db_extras = []
    def __init__(self, args):
        for col in self.db_columns:
            if col.name in args:
                if args[col.name] is None:
                    setattr(self, col.name, None)
                else:
                    setattr(self, col.name, col.read(args[col.name]))
            else:
                setattr(self, col.name, col.default)
        if hasattr(self, 'dbid'):
            if self.dbid:
                self.load_extras()
    
    def load_extras(self):
        pass
    
    def copy_save_attrs(self):
        copy_dict = {}
        for col in self.db_columns:
            val = getattr(self, col.name)
            copy_dict[col.name] = col.read(col.write(val)) if val else None
        return copy_dict
    
    def save(self):
        save_dict = {}
        for col in self.db_columns:
            val = getattr(self, col.name)
            save_dict[col.name] = col.write(val) if val else None
        if self.dbid:
                self.world.db.update_from_dict(self.db_table_name, save_dict)
        else:
            self.dbid = self.world.db.insert_from_dict(self.db_table_name, save_dict)
    
    def destruct(self):
        if self.dbid:
            self.world.db.delete('FROM ? WHERE dbid=?', [self.db_table_name, self.dbid])

