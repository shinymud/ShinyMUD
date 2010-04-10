from shinymud.lib.world import World

class Spawn(object):
    
    def __init__(self, id, room, obj, spawn_type, container=None, **args):
        self.id = str(id)
        self.room = room
        self.spawn_object = obj
        self.spawn_type = spawn_type
        self.container = container
        self.nested_spawns = []
        self.dbid = args.get('dbid')
    
    def to_dict(self):
        d = {}
        d['id'] = int(self.id)
        d['room'] = self.room.dbid
        d['spawn_type'] = self.spawn_type
        d['spawn_object_id'] = self.spawn_object.id
        d['spawn_object_area'] = self.spawn_object.area.name
        if self.container:
            d['container'] = self.container.id
        if self.dbid:
            d['dbid'] = self.dbid
        return d
    
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
    def add_nested_spawn(self, spawn):
        """Add another item to this object's "containee list"."""
        self.nested_spawns.append(spawn)
    
    def remove_nested_spawn(self, spawn):
        """Remove an item from this object's "containee list"."""
        if spawn in self.nested_spawns:
            self.nested_spawns.remove(spawn)
    
    def save(self, save_dict=None):
        world = World.get_world()
        if self.dbid:
            if save_dict:
                save_dict['dbid'] = self.dbid
                world.db.update_from_dict('room_spawns', save_dict)
            else:
                world.db.update_from_dict('room_spawns', self.to_dict())
        else:
            self.dbid = world.db.insert_from_dict('room_spawns', 
                                                  self.to_dict())
    
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
    
