from shinymud.world import World
from shinymud.models.room import Room
from shinymud.models.item import Item
from shinymud.models.npc import Npc

class Area(object):
    
    def to_dict(self):
        d = {}
        d['name'] = self.name
        d['level_range'] = self.level_range
        d['builders'] = ",".join(self.builders)
        d['description']  = self.description)
        if self.dbid:
            d['dbid'] = self.dbid
        return d
    
    def __init__(self, name=None, **args):
        self.name = name
        self.rooms = {}
        self.items = {}
        self.npcs = {}
        self.builders = args['builders'].split(',') if 'builders' in args else []
        self.level_range = args.get('level_range', 'All')
        self.description = args.get('description', 'No Description')
        self.dbid = args.get(dbid)
    
    def load_rooms(self):
        if self.dbid:
            world = World.get_world()
            rooms = world.db.select("* from room where area=?", [self.dbid])
            for room in rooms:
                room['area'] = self
                self.rooms[room['id']] = Room(**room)
    
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
    
    def list_items(self):
        names = self.items.keys()
        item_list = '______________________________________________\nItems in area "%s":\n' % self.name
        for key, value in self.items.items():
            item_list += '    %s - %s\n' % (key, value.title)
        item_list += '______________________________________________\n'
        return item_list
    
    def list_npcs(self):
        names = self.npcs.keys()
        npc_list = '______________________________________________\nNpcs in area "%s":\n' % self.name
        for key, value in self.npcs.items():
            npc_list += '    %s - %s\n' % (key, value.title)
        npc_list += '______________________________________________\n'
        return npc_list
    
    @classmethod
    def create(cls, name):
        """Create a new area instance and add it to the world's area list."""
        world = World.get_world()
        if not world.get_area(name):
            new_area = cls(name)
            a = new_area.to_dict()
            world.db.insert_from_dict('area', a)
            world.new_area(new_area)
            return new_area
        else:
            return "This area already exists.\n"
    
    def get_id(self, id_type):
        """Generate a new id for an item, npc, or room associated with this area."""
        if id_type in ['room', 'item', 'npc']:
            world = World.get_world()
            rows = world.db.select("max(id) as id from " + id_type " where area=?", [self.dbid])
            if rows:
                your_id = int(rows[0]['id']) + 1
            else:
                your_id = 1
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
    
    def new_room(self):
        """Add a new room to this area's room list."""
        new_room = Room.create(self, self.get_id('room'))
        world = World()
        new_room.dbid = world.db.insert_from_dict('room', new_room.to_dict())
        self.rooms[new_room.id] = new_room
        return new_room
    
    def new_item(self):
        """Add a new item to this area's item list."""
        new_item = Item.create(self, self.get_id('item'))
        self.items[new_item.id] = new_item
        return new_item
    
    def new_npc(self):
        """Add a new npc to this area's npc list."""
        new_npc = Npc.create(self, self.get_id('npc'))
        self.npcs[new_npc.id] = new_npc
        return new_npc
    
    def get_item(self, item_id):
        """Get an item from this area by its id, if it exists.
        If it does not exist, return None."""
        if item_id in self.items.keys():
            return self.items.get(item_id)
        return None
        
    def get_room(self, room_id):
        """Get a room from this area by its id, if it exists.
        If it does not exist, return None."""
        if room_id in self.rooms.keys():
            return self.rooms.get(room_id)
        return None
    
    def get_npc(self, npc_id):
        """Get an npc from this area by its id, if it exists.
        If it does not exist, return None."""
        if npc_id in self.npcs.keys():
            return self.npcs.get(npc_id)
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
    
