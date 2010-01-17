from shinymud.lib.world import World

class Reset(object):
    
    def __init__(self, room, obj, reset_type, container=None, **args):
        self.room = room
        self.reset_object = obj
        self.reset_type = reset_type
        self.container = container
        self.nested_resets = []
        self.dbid = args.get('dbid')
    
    def to_dict(self):
        d = {}
        d['room'] = self.room.dbid
        d['reset_type'] = self.reset_type
        d['reset_object_id'] = self.reset_object.id
        d['reset_object_area'] = self.reset_object.area.name
        if self.container:
            d['container'] = self.container.dbid
        if self.dbid:
            d['dbid'] = self.dbid
        return d
    
    def __str__(self):
        string = '%s - %s - spawns %s' % (self.reset_type.capitalize(), self.reset_object.name, 
                                                       self.get_spawn_point())
        return string
    
    def get_spawn_point(self):
        if self.container:
            if self.container.reset_type == 'npc':
                return 'into %s\'s inventory (R:%s)' % (self.container.reset_object.name, 
                                                        str(self.container.dbid))
            else:
                return 'into %s (R:%s)' % (self.container.reset_object.name, str(self.container.dbid))
        return 'in room'
    
    def add_nested_reset(self, reset):
        """Add another item to this object's "containee list"."""
        self.nested_resets.append(reset)
    
    def remove_nested_reset(self, reset):
        """Remove an item from this object's "containee list"."""
        if reset in self.nested_resets:
            self.nested_resets.remove(reset)
    
    def save(self, save_dict=None):
        world = World.get_world()
        if self.dbid:
            if save_dict:
                save_dict['dbid'] = self.dbid
                world.db.update_from_dict('room_resets', save_dict)
            else:
                world.db.update_from_dict('room_resets', self.to_dict())
        else:
            self.dbid = world.db.insert_from_dict('room_resets', self.to_dict())
            # self.spawn_id = "%s,%s_%s-%s" % (self.room.id, self.room.area.name, 
            #                                  self.reset_object.id, str(self.dbid))
            # world.db.update_from_dict('room_resets', {'dbid': self.dbid, 'spawn_id': self.spawn_id})
    
    def destruct(self):
        world = World.get_world()
        if self.dbid:
            world.db.delete('FROM room_resets WHERE dbid=?', [self.dbid])
            for reset in self.nested_resets:
                reset.destruct()
    
    def spawn(self):
        """load the object"""
        new_object = self.reset_object.load()
        # new_object.spawn_id = self.spawn_id
        for reset in self.nested_resets:
            container = new_object.item_types.get('container')
            container.item_add(reset.spawn())
        return new_object
    
