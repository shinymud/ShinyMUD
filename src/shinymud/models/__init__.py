from shinymud.lib.world import World
from shinymud.lib.registers import ModelRegister
import json

model_list = ModelRegister()

class Column(object):
    """Columns are used by Models to handle how data will be stored and
    retrieved from the database. The main functions used here are 'read'
    and 'write', with the rest of the attributes being additional options
    for how data can be stored. Both 'read' and 'write' have defaults shown
    in the init() below, but are commonly overridden by read and write functions
    provided in shiny_types.py
    
    Columns are only used in classes that inherit from models. 
    """
    def __init__(self, name, **args):
        #Name of the class attribute
        self.name = name
        #Data type to be stored in sql db (int, string, text)
        self.type = args.get('type', 'TEXT')
        #If there is no set value for this attribute, Store as a given default instead
        self.default = args.get('default', None)
        #Can this value be stored as null?
        #NOTE: This isn't currently being used.
        self.null = args.get('null', True)
        #Set if this value is a primary key
        self.primary_key = args.get('primary_key', False)
        #Set if this value is a foreign key
        self.foreign_key = args.get('foreign_key') # (model, column)
        #Set if unique
        self.unique = args.get('unique', False)
        #How shall data be retrieved by the db? Default is string, other opitons
        #are in shiny_types.py
        self.read = args.get('read', lambda x: x)
        #How shall this data be written to the db? Default is unicode string or None.
        self.write = args.get('write', lambda x: None if x is None else unicode(x))
        #Allows for ON UPDATE or ON DELETE cascading
        self.cascade = args.get('cascade')
        self.copy = args.get('copy', lambda x: x)
    
    def __str__(self):
        """Packages all of the columns information so it is ready to be given to the
        database. Only prepares db column information, does not prepare data."""
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
            # Don't bother setting this in the database -- we'll just enforce
            # it in code.
            # if not self.null:
            #     sql_string.append('NOT NULL')
            if self.cascade:
                sql_string.append('%s CASCADE' % str(self.cascade))
        return unicode(" ".join(sql_string))
    

class Model(object):
    """Models are used for saving and loading in-game objects. 
    
    How you use models:
    
    Saving: The first thing you need to do is specify a table name. This tells
    the database where to put all of the data for this kind of class. Use the 
    statement "db_table_name = <my_model>". Table names MUST be unique to all
    other model table names, or else bad things will happen.
    
    Next, models save data using columns (defined above). Any class attribute
    you want to save needs to have its own column. The name given to the column
    will be the name of the attribute when the class is initialized (loaded). If the
    attribute is anything more complex than a string, you will need to override
    the read and write functions (some basic ones in shiny_types; you can also 
    write your own). Add the columns to the db list and your objects will save!
    
    Example: 
    db_table_name = "sack_of_gold"
    db_columns.append(
        Column("owner", primary_key=true),
        Column("ammount", type="INTEGER", default=20, read=read_int),
        Column("weight", type="INTEGER", read=read_int)
        )
    NOTE: Many values such as 'read' and 'write' are left out above. You can do
        this for anything except for the column name, and it will default to the
        values shown in the Column class.
    
    Loading: Dependent models in shinymud load in a parent-child system. That is,
    an area loads all of its rooms, a room loads all of its npcs, an npc loads its
    inventory. When a parent model loads a dependent model, it hands the child a 
    huge lump of raw slq data, which the child parses through models.
    
    To activate a models super powers of parsing, simply add this line to the init
    function of your class:
            Model.__init__(self, args)
    Where 'args' is a dictionary from the parent.        
    """
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
        """Go through each of the columns in our decendent model, and set them as real
        attributes in our class. If a column doesn't have a name, check if it has default
        data or a default function. Lastly, if it was loaded (has dbid), load the extras.
        """
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
        """(For decendent Model) If a Model has anything it needs to load after the columns,
        it does so here. This is usually to load child models, or anything else which needs 
        to be loaded after the init() stage. This function olny gets called if it is loaded
        from the database"""
        pass
    
    def copy_save_attrs(self):
        """
        Copy all data in a model, according to its column 'copy' function, and return it.
        """
        copy_dict = {}
        for col in self.db_columns:
            val = getattr(self, col.name, col.default)
            copy_dict[col.name] = col.copy(val) if val else None
        return copy_dict
    
    def create_save_dict(self):
        """Grab all current data from the current model, getting it ready to be written. This
        probably never needs to be used anywhere but here."""
        save_dict = {}
        for col in self.db_columns:
            val = getattr(self, col.name, col.default)
            save_dict[col.name] = col.write(val) if val else None
        return save_dict
    
    def save(self):
        """Save model data to the database. This function should be freely used by decendent
        models to save changes."""
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
    
