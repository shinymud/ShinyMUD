from shinymud.world import World

class Area(object):
    
    def to_dict(self):
        d = {}
        d['name'] = self.name
        d['level_range'] = self.level_range
        d['builders'] = ",".join(self.builders)
        d['description']  = self.description)
        return d
    
    def from_dict(self, d):
        self.name = d.get('name', "")
        self.level_range = d.get('level_range', 'All')
        self.builders = d['builders'].split(',') if 'builders' in d else []
        self.description = d.get('description', 'No Description')
    
    def __init__(self, name=None, lr='All', **args):
        super(Area, self).__init__(**args)
        if name:
            self.name = name
        self.rooms = {}
        self.ids = {'room': 1, 'item': 1, 'npc': 1}
    
    def add_builder(self, username):
        """Add a user to the builder's list."""
        self.builders.append(username)
        return '%s has been added to the builder\'s list for this area.\n' % username.capitalize()
    
    def remove_builder(self, username):
        """Remove a user from the builder's list."""
        if username in self.builders:
            self.builders.remove(username)
            return '%s has been removed from the builder\'s list for this area.\n' % username.capitalize()
        else:
            return '%s is not on the builder\'s list for this area.\n' % username.capitalize()
    
    def __str__(self):
        """Print out a nice string representation of this area's attributes."""
        
        builders = ', '.join(self.builders)
        area_list = """______________________________________________
 Area: %s
    Level Range: %s
    Builders: %s
    Number of rooms: %s
    Description: \n        %s
______________________________________________\n""" % (self.name, 
                                                         self.level_range, 
                                                         builders.capitalize(),
                                                         str(len(self.rooms.keys())),
                                                         self.description)
        return area_list
    
    def list_rooms(self):
        names = self.rooms.keys()
        room_list = '______________________________________________\nRooms in area "%s":\n' % self.name
        for key, value in self.rooms.items():
            room_list += '    %s - %s\n' % (key, value.title)
        room_list += '______________________________________________\n'
        return room_list
    
    @classmethod
    def create(cls, name):
        """Create a new area instance and add it to the world's area list."""
        world = World.get_world()
        if not world.get_area(name):
            new_area = cls(name)
            world.new_area(new_area)
            return new_area
        else:
            return "This area already exists.\n"
    
    def get_id(self, id_type):
        """Generate a new id for an item, npc, or room associated with this area."""
        if id_type in self.ids.keys():
            your_id = self.ids.get(id_type)
            self.ids[id_type] += 1
            return str(your_id)
    
    def set_description(self, desc):
        """Set this area's description."""
        self.description = desc
        return 'Area description set.\n'
    
    def set_levelrange(self, lvlrange):
        """Set this area's level range."""
        self.level_range = lvlrange
        return 'Area levelrange set.\n'
    
# ************************ Room Functions ************************
# Here exist all the function that an area uses to manage the rooms
# it contains.
    def destroy_room(self, room_id):
        """Destroy a specific room in this area."""
        room = self.get_room(room_id)
        if room:
            if room.users:
                return 'You can\'t destroy that room, there are people in there!.\n'
            doors = room.exits.keys()
            for door in doors:
                del room.exits[door]
            room.id = None
            del self.rooms[room_id]
            return 'Room %s has been deleted.\n' % room_id
        return 'Room %s doesn\'t exist.\n' % room_id
    
    def new_room(self, room):
        """Add a new room to this area's room list."""
        self.rooms[room.id] = room
    
    def get_room(self, room_id):
        """Get a room from this area by its id, if it exists.
        If it does not exist, return None."""
        if room_id in self.rooms.keys():
            return self.rooms.get(room_id)
        return None
    
# ************************ NPC Functions ************************
# Here exist all the function that an area uses to manage the NPC's
# it contains.
    def destroy_npc(self, npc_id):
        return 'Npc\'s don\'t exist yet.\n'
    
# ************************ Item Functions ************************
# Here exist all the function that an area uses to manage the items
# it contains.
    def destroy_item(self, npc_id):
        return 'Items don\'t exist yet.\n'
    
