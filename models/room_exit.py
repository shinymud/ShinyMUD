from models import ShinyModel

class RoomExit(ShinyModel):
    states = {'true': True, 'false': False}
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
        list_exit = "[to: %s-%s, linked: %s, openable: %s, closed: %s, hidden: %s, locked: %s key: %s]" % (self.room.area.name, self.to_room.id, linked,
                                                                                                        str(self.openable), str(self.closed),
                                                                                                        str(self.hidden), str(self.locked),
                                                                                                        str(self.key))
        return list_exit
    
    def close_me(self, username):
        if self.door == False:
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
        if self.door == False:
            'You can\'t open that.\n'
        if not self.closed:
            return 'It\'s already open.\n'
        self.closed == False
        self.room.tell_room('%s opened the %s door.\n' % (username, self.direction), [username])
        if self.linked_exit:
            self.linked_exit.closed = False
            self.to_room.tell_room('The %s door was opened from the other side.\n' % self.linked_exit.direction)
        return 'You open the %s door.\n' % self.direction
    
