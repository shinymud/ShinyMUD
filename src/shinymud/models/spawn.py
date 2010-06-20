from shinymud.models import Model, Column, model_list
from shinymud.models.shiny_types import *

class Spawn(Model):
    db_table_name = 'room_spawns'
    db_columns = Model.db_columns + [
        Column('id', null=False),
        Column('room', write=lambda room: room.dbid, null=False, 
               foreign_key=('room', 'dbid'), type='INTEGER'),
        Column('spawn_type', null=False),
        Column('spawn_object_id', null=False),
        Column('spawn_object_area', null=False),
        Column('container', write=lambda container: container.id)
    ]
    def __init__(self, args={}):
        Model.__init__(self, args)
        self.spawn_object = args.get('obj')
        self.nested_spawns = []
    
    def __str__(self):
        string = ('%s - %s (%s:%s) - spawns %s' % (self.spawn_type.capitalize(), 
                                                   self.spawn_object.name,
                                                   self.spawn_object.id,
                                                   self.spawn_object.area.name,
                                                   self.get_spawn_point())
                 )
        return string
    
    def get_spawn_point(self):
        if self.container:
            if self.container.spawn_type == 'npc':
                return 'into %s\'s inventory (R:%s)' % (self.container.spawn_object.name, 
                                                        str(self.container.id))
            else:
                return 'into %s (R:%s)' % (self.container.spawn_object.name, 
                                           str(self.container.id))
        return 'in room'
    
    def get_spawn_id(self):
        if self.dbid:
            spawn_id = "%s,%s_%s-%s" % (self.room.id, self.room.area.name, 
                                        self.spawn_object.id, 
                                        str(self.id))
            return spawn_id
        return None
    
    spawn_id = property(get_spawn_id)
    
    def get_spawn_obj(self):
        return getattr(self, '_spawn_obj', None)
    
    def set_spawn_obj(self, val):
        self._spawn_obj = val
        self.spawn_object_id = val.id
        self.spawn_object_area = val.area.name
    
    spawn_obj = property(get_spawn_obj, set_spawn_obj)
    def add_nested_spawn(self, spawn):
        """Add another item to this object's "containee list"."""
        self.nested_spawns.append(spawn)
    
    def remove_nested_spawn(self, spawn):
        """Remove an item from this object's "containee list"."""
        if spawn in self.nested_spawns:
            self.nested_spawns.remove(spawn)
    
    def destruct(self):
        world = World.get_world()
        if self.dbid:
            world.db.delete('FROM room_spawns WHERE dbid=?', [self.dbid])
            for spawn in self.nested_spawns:
                spawn.destruct()
    
    def spawn(self):
        """load the object"""
        new_object = self.spawn_object.load()
        new_object.spawn_id = self.get_spawn_id()
        for spawn in self.nested_spawns:
            container = new_object.item_types.get('container')
            container.item_add(spawn.spawn())
        return new_object
    

model_list.register(Spawn)
