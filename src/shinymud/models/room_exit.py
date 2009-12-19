from shinymud.models import to_bool
from shinymud.models.world import World

class RoomExit(object):
    
    def __init__(self, from_room=None, direction=None, to_room=None):
        self.to_room = to_room
        self.room = from_room
        self.linked_exit = None
        self.direction = direction
        self.openable = False
        self.closed = False
        self.hidden = False
        self.locked = False
        self.key = None
    
    def unlink(self):
        """Unlink any corresponding exits if they exist."""
        if self.linked_exit:
            # Remove the door I point to
            self.linked_exit = None
            # Remove the door that points to me 
            self.to_room.linked_exit = None
    
    def __str__(self):
        linked = "false"
        if self.linked_exit:
            linked = "true"
        list_exit = "[to: %s-%s, linked: %s, openable: %s, closed: %s, hidden: %s, locked: %s, key: %s]" % (self.room.area.name, self.to_room.id, linked,
                                                                                                        str(self.openable), str(self.closed),
                                                                                                        str(self.hidden), str(self.locked),
                                                                                                        str(self.key))
        return list_exit
    
    def close_me(self, username):
        if self.openable == False:
            return 'You can\'t close that.\n'
        if self.closed:
            return 'It\'s already closed.\n'
        self.closed == True
        self.room.tell_room('%s closed the %s door.\n' % (username, self.direction), [username])
        if self.linked_exit:
            self.linked_exit.closed = True
            self.to_room.tell_room('The %s door was closed from the other side.\n' % self.linked_exit.direction)
        return 'You close the %s door.\n' % self.direction
    
    def open_me(self, username):
        if self.openable == False:
            'You can\'t open that.\n'
        if not self.closed:
            return 'It\'s already open.\n'
        self.closed == False
        self.room.tell_room('%s opened the %s door.\n' % (username, self.direction), [username])
        if self.linked_exit:
            self.linked_exit.closed = False
            self.to_room.tell_room('The %s door was opened from the other side.\n' % self.linked_exit.direction)
        return 'You open the %s door.\n' % self.direction
    
    def set_closed(self, args):
        try:
            boolean = to_bool(args[0])
        except Exception, e:
            return str(e)
        else:
            self.closed = boolean
            return 'Exit attribute "closed" is now %s.\n' % str(boolean)
    
    def set_openable(self, args):
        try:
            boolean = to_bool(args[0])
        except Exception, e:
            return str(e)
        else:
            self.openable = boolean
            return 'Exit attribute "openable" is now %s.\n' % str(boolean)
    
    def set_hidden(self, args):
        try:
            boolean = to_bool(args[0])
        except Exception, e:
            return str(e)
        else:
            self.hidden = boolean
            return 'Exit attribute "hidden" is now %s.\n' % str(boolean)
    
    def set_locked(self, args):
        try:
            boolean = to_bool(args[0])
        except Exception, e:
            return str(e)
        else:
            self.locked = boolean
            return 'Exit attribute "locked" is now %s.\n' % str(boolean)
    
    def set_to(self, args):
        if not len(args) == 2:
            return 'Usage: set exit <direction> to <area-name> <room-number>\n'
        area = World.get_world().get_area(args[0])
        if not area:
            return 'That area doesn\'t exist.\n'
        room = area.get_room(args[1])
        if not room:
            return 'That room doesn\'t exist.\n'
        if not room.linked_exit:
            self.to_room = room
            return ' The %s exit now goes to room %s in area %s.\n' % (self.direction,
                                                                       self.to_room.id,
                                                                       self.to_room.area.name)
        else:
            return 'That exit is linked. You should unlink it before you set it to somewhere else.\n'

    
    def set_key(self, args):
        return 'This functionality coming soon!\n'
