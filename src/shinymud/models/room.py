from models import ShinyModel
from models.room_exit import RoomExit
from models.area import Area
dir_opposites = {'north': 'south', 'south': 'north',
                      'east': 'west', 'west': 'east',
                      'up': 'down', 'down': 'up'}

class Room(ShinyModel):
    UNIQUE = ['area', 'id']
    save_attrs =    {   "id": [None, int],
                        "area": [None, Area],
                        "title": ["New Room", str],
                        "description": ["This is a shiny new room!", str]
                    }
    def __init__(self, area=None, **args):
        self.id = 0
        super(Room, self).__init__(**args)
        self.items = {}
        self.exits = {'north': None,
                      'south': None,
                      'east': None,
                      'west': None,
                      'up': None,
                      'down': None}
        if area:
            self.area = area
        self.resets = {}
        self.users = {}
    
    @classmethod
    def create(cls, area):
        """Create a new room."""
        new_room = cls(area)
        new_room.id = area.get_id('room')
        area.new_room(new_room)
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
        return 'Room %s title set.\n' % self.id
    
    def set_description(self, desc):
        """Set the description of a room."""
        self.description = desc
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
        exp = r'(?P<direction>(north)|(south)|(east)|(west)|(up)|(down))([ ]+(?P<room_id>\d+))([ ]+(?P<area_name>\w+))?'
        match = re.match(exp, args, re.I)
        message = 'Type "help exits" to get help using this command.\n'
        if match:
            direction, room_id, area_name = match.group('direction', 'room_id', 'area_name')
            area = user.world.areas.get(area_name) or self.area
            if area:
                room = area.get_room(room_id)
                if room:
                    room.exits[direction] = RoomExit(self, direction, room)
                    message = 'Exit %s created.' % direction
        return message
    
    def remove_exit(self, args):
        pass
    
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
    
