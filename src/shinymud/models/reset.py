from shinymud.world import World

class Reset(object):
    
    def __init__(self, room, obj, reset_type, container_id=None, spawn_point='in room', **args):
        self.room = room
        self.reset_object = obj
        self.reset_type = reset_type
        self.container_id = container_id
        # nested_resets are the resets that should have their reset_objects added
        # to this reset's reset_object's inventory when it is spawned...
        self.nested_resets = []
        self.spawn_point = spawn_point
        self.dbid = args.get('dbid')
    
    def to_dict(self):
        d = {}
        d['room'] = self.room.dbid
        d['reset_type'] = self.reset_type
        d['reset_object_id'] = self.reset_object.id
        d['reset_object_area'] = self.reset_object.area.name
        d['spawn_point'] = self.spawn_point
        if self.container_id:
            d['container_id'] = self.container_id
        if self.dbid:
            d['dbid'] = self.dbid
        return d
    
    def add_containee(self, reset):
        """Add another item to this object's "containee list"."""
        self.nested_resets.append(reset)
    
    def remove_containee(self, reset):
        """Remove an item from this object's "containee list"."""
        if obj_id in self.nested_resets:
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
        if self.dbid:
            self.world.db.delete('FROM room WHERE dbid=?', [self.dbid])
    
    def spawn(self):
        """load the object"""
        new_object = self.reset_object.load()
        # new_object.spawn_id = self.spawn_id
        for reset in self.nested_resets:
            new_object.add_item(reset.spawn())
        return new_object
    
