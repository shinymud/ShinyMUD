from shinymud.lib.world import World
from shinymud.lib.registers import ModelRegister
import json

model_list = ModelRegister()

class Column(object):
    def __init__(self, name, **args):
        self.name = name
        self.type = args.get('type', 'TEXT')
        self.default = args.get('default', None)
        self.null = args.get('null', True)
        self.primary_key = args.get('primary_key', False)
        self.foreign_key = args.get('foreign_key') # (model, column)
        self.unique = args.get('unique', False)
        self.read = args.get('read', lambda x: x)
        self.write = args.get('write', lambda x: None if x is None else unicode(x))
        self.cascade = args.get('cascade')
        self.copy = args.get('copy', lambda x: x)
    
    def __str__(self):
        sql_string = []
        sql_string.append(self.name)
        sql_string.append(self.type)
        if self.primary_key: 
            sql_string.append("PRIMARY KEY")
        else:
            if self.foreign_key:
                sql_string.append("REFERENCES %s(%s)" % (self.foreign_key[0], self.foreign_key[1]))
            if self.unique: 
                sql_string.append('UNIQUE')
            if not self.null:
                sql_string.append('NOT NULL')
            if self.cascade:
                sql_string.append('%s CASCADE' % str(self.cascade))
        return unicode(" ".join(sql_string))
    

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
    def __init__(self, args={}):
        for col in self.db_columns:
            if args.get(col.name):
                setattr(self, col.name, col.read(args[col.name]))
            else:
                if hasattr(col.default, '__call__'):
                    setattr(self, col.name, col.default())
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
            val = getattr(self, col.name, col.default)
            copy_dict[col.name] = col.copy(val) if val else None
        return copy_dict
    
    def create_save_dict(self):
        save_dict = {}
        for col in self.db_columns:
            val = getattr(self, col.name, col.default)
            save_dict[col.name] = col.write(val) if val else None
        return save_dict
    
    def save(self):
        save_dict = self.create_save_dict()
        if self.dbid:
                self.world.db.update_from_dict(self.db_table_name, save_dict)
        else:
            if 'dbid' in save_dict:
                del save_dict['dbid']
            self.dbid = self.world.db.insert_from_dict(self.db_table_name, save_dict)
    
    def destruct(self):
        if self.dbid:
            self.world.db.delete('FROM %s WHERE dbid=?' % self.db_table_name, [self.dbid])
    
