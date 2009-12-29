from shinymud.models.room_exit import RoomExit
from shinymud.world import World
import logging
import re

dir_opposites = {'north': 'south', 'south': 'north',
                      'east': 'west', 'west': 'east',
                      'up': 'down', 'down': 'up'}

class Room(object):

    def to_dict(self):
        d = {}
        d['id'] = self.id
        d['area'] = self.area.dbid
        d['title'] = self.title
        d['description'] = self.description
        if self.dbid:
            d['dbid'] = self.dbid
        self.log.debug(d)
        return d
         
    def __init__(self, area=None, id=0, **args):
        self.id = str(id)
        self.area = area
        self.title = args.get('title', 'New Room')
        self.description = args.get('description','This is a shiny new room!')
        self.items = []
        self.exits = {'north': None,
                      'south': None,
                      'east': None,
                      'west': None,
                      'up': None,
                      'down': None}
        self.npcs = []
        self.resets = []
        self.users = {}
        self.dbid = args.get('dbid')
        self.log = logging.getLogger('Room')
        self.world = World.get_world()
    
    @classmethod
    def create(cls, area=None, room_id=0):
        """Create a new room."""
        new_room = cls(area, room_id)
        return new_room
    
    def __str__(self):
        nice_exits = ''
        for direction, value in self.exits.items():
            if value:
                nice_exits += '        ' + direction + ': ' + str(value) + '\n'
            else:
                nice_exits += '        ' + direction + ': None\n'
                
        room_list ="""______________________________________________
Room: 
    id: %s
    area: %s
    title: %s
    description: %s
    exits: 
%s
______________________________________________\n""" % (self.id, self.area.name, self.title,
                                                       self.description, nice_exits)
        return room_list
    
    def user_add(self, user):
        self.users[user.name] = user
    
    def user_remove(self, user):
        if self.users.get(user.name):
            del self.users[user.name]
    
    def set_title(self, title):
        """Set the title of a room."""
        self.title = title
        self.world.db.update_from_dict('room', self.to_dict())
        return 'Room %s title set.\n' % self.id
    
    def set_description(self, desc):
        """Set the description of a room."""
        self.description = desc
        self.world.db.update_from_dict('room', self.to_dict())
        return 'Room %s description set.\n' % self.id
    
    def set_exit(self, args):
        args = args.split()
        if len(args) < 3:
            return 'Usage: set exit <direction> <attribute> <value(s)>. Type "help exits" for more detail.\n'
        my_exit = self.exits.get(args[0])
        if my_exit:
            if hasattr(my_exit, 'set_' + args[1]):
                return getattr(my_exit, 'set_' + args[1])(args[2:])
            else:
                return 'You can\'t set that.\n'
        else:
            return 'That exit doesn\'t exist.\n'
    
    def add_exit(self, args):
        exp = r'(?P<direction>(north)|(south)|(east)|(west)|(up)|(down))([ ]+to)?([ ]+(?P<room_id>\d+))([ ]+(?P<area_name>\w+))?'
        match = re.match(exp, args, re.I)
        message = 'Type "help exits" to get help using this command.\n'
        if match:
            direction, room_id, area_name = match.group('direction', 'room_id', 'area_name')
            area = World.get_world().get_area(area_name) or self.area
            if area:
                room = area.get_room(room_id)
                if room:
                    self.exits[direction] = RoomExit(self, direction, room)
                    message = 'Exit %s created.\n' % direction
                else:
                    message = 'That room doesn\'t exist.\n'
            else:
                message = 'That area doesn\'t exist.\n'
        return message
    
    def add_reset(self, args):
        exp = r'(?P<obj_type>(item)|(npc))([ ]+(?P<obj_id>\d+))(([ ]+from)?([ ]+area)?[ ]+(?P<area_name>\w+))?'
        match = re.match(exp, args, re.I)
        if match:
            obj_type, obj_id, area_name = match.group('obj_type', 'obj_id', 'area_name')
            area = World.get_world().get_area(area_name) or self.area
            if not area:
                return 'That area doesn\'t exist.\n'
            obj = getattr(area, obj_type + "s").get(obj_id)
            if not obj:
                return '%s number %s does not exist.\n' % (obj_type, obj_id)
            self.resets.append(obj)
            return 'A reset has been added for %s number %s.\n' % (obj_type, obj_id)
        return 'Type "help resets" to get help using this command.\n'
    
    def remove_exit(self, args):
        return 'This function isn\'t implemented yet.\n'
    
    def link_exits(self, direction, link_room):
        """Link exits between this room (self), and the room passed."""
        this_exit = self.exits.get(direction)
        that_dir = dir_opposites.get(direction)
        that_exit = link_room.exits.get(that_dir)
        if this_exit:
            # If this exit already exists, make sure to unlink it with any other
            # rooms it may have been previously unlinked to, then change its to_room
            this_exit.unlink()
            this_exit.to_room = link_room
        else:
            self.exits[direction] = RoomExit(self, direction, link_room)
            this_exit = self.exits[direction]
        if that_exit:
            # If that exit was already linked, unlink it
            that_exit.unlink()
            that_exit.to_room = self
        else:
            link_room.exits[that_dir] = RoomExit(link_room, that_dir, self)
            that_exit = link_room.exits[that_dir]
        # Now that the exits have been properly created/set, set the exits to point to each other
        this_exit.linked_exit = that_exit
        that_exit.linked_exit = this_exit
        return 'Linked room %s\'s %s exit to room %s\'s %s exit.\n' % (this_exit.room.id, this_exit.direction,
                                                                      that_exit.room.id, that_exit.direction)
            
    def tell_room(self, message, exclude_list=[]):
        """Echo something to everyone in the room, except the people on the exclude list."""
        for person in self.users.values():
            if person.name not in exclude_list:
                person.update_output(message)
    
    def get_npc(self, keyword):
        """Get an NPC from this room if its name is equal to the keyword given."""
        for npc in self.npcs:
            if keyword in npc.keywords:
                return npc
        return None

    def get_item(self, keyword):
        """Get an item from this room they keyword given matches its keywords."""
        for item in self.items:
            if keyword in item.keywords:
                return item
        return None

    def get_user(self, keyword):
        """Get a user from this room if their name is equal to the keyword given."""
        for user in self.users.values():
            if keyword == user.name:
                return user
        return None
    
    def check_for_keyword(self, keyword):
        """Return the first instance of an item, npc, or player that matches the keyword.
        If nothing in the room matches the keyword, return None."""
        # check the items in the room first
        item = self.get_item(keyword)
        if item: return item
        
        # then check the npcs in the room
        npc = self.get_npc(keyword)
        if npc: return npc
        
        # then check the PCs in the room
        user = self.get_user(keyword)
        if user: return user
        
        # If we didn't match any of the above, return None
        return None
    
    def item_add(self, item):
        """Add an item to this room."""
        self.items.append(item)
    
    def item_remove(self, item):
        """Remove an item from this room."""
        if item in self.items:
            self.items.remove(item)