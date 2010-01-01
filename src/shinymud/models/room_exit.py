from shinymud.models import to_bool
from shinymud.world import World

class RoomExit(object):
    
    def __init__(self, from_room=None, direction=None, to_room=None, **args):
        self.to_room = to_room
        self.room = from_room
        self.linked_exit = args.get('linked_exit')
        self.direction = direction
        self.openable = to_bool(args.get('openable')) or False
        self.closed = to_bool(args.get('closed')) or False
        self.hidden = to_bool(args.get('hidden')) or False
        self.locked = to_bool(args.get('locked')) or False
        self.key = None
        self.key_area = str(args.get('key_area', ''))
        self.key_id = str(args.get('key_id', ''))
        self.to_id = str(args.get('to_id', ''))
        self.to_area = str(args.get('to_area', ''))
        self.dbid = args.get('dbid')
        self.world = World.get_world()
    
    def to_dict(self):
        d = {}
        d['to_room'] = self.to_room.dbid
        d['room'] = self.room.dbid
        if self.linked_exit:
            d['linked_exit'] = self.linked_exit
        d['direction'] = self.direction
        d['openable'] = self.openable
        d['closed'] = self.closed
        d['hidden'] = self.hidden
        d['locked'] = self.locked
        if self.key:
            d['key'] = self.key.dbid
        if self.dbid:
            d['dbid'] = self.dbid
        return d
    
    def destruct(self):
        if self.dbid:
            self.world.db.delete('FROM room_exit WHERE dbid=?', [self.dbid])
    
    def unlink(self):
        """Unlink any corresponding exits if they exist."""
        if self.linked_exit:
            # Remove the door I point to
            self.linked_exit = None
            # Remove the door that points to me 
            self.to_room.linked_exit = None
    
    def _resolve_to_room(self):
        if self._to_room:
            return self._to_room
        try:
            self.to_room = self.world.get_area(str(self.to_area)).get_room(str(self.to_id))
            return self._to_room
        except:
            return None
    
    def _set_to_room(self, to_room):
        self._to_room = to_room
    to_room = property(_resolve_to_room, _set_to_room)
    
    def _resolve_key(self):
        if self._key:
            return self._key
        try: 
            self.key = self.world.get_area(self.key_area).get_item(self.key_id)
            return self._key
        except:
            return None
    
    def _set_key(self, key):
        self._key = key
    key = property(_resolve_key, _set_key)
    
    def __str__(self):
        linked = "false"
        if self.linked_exit:
            linked = "true"
        list_exit = "[to: %s-%s, linked: %s, openable: %s, closed: %s, hidden: %s, locked: %s, key: %s]" % (self.to_room.area.name, self.to_room.id, linked,
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
            self.world.db.update_from_dict('room_exit', {'dbid': self.dbid, 'closed': self.closed})
            return 'Exit attribute "closed" is now %s.\n' % str(boolean)
    
    def set_openable(self, args):
        try:
            boolean = to_bool(args[0])
        except Exception, e:
            return str(e)
        else:
            self.openable = boolean
            self.world.db.update_from_dict('room_exit', {'dbid': self.dbid, 'openable': self.openable})
            return 'Exit attribute "openable" is now %s.\n' % str(boolean)
    
    def set_hidden(self, args):
        try:
            boolean = to_bool(args[0])
        except Exception, e:
            return str(e)
        else:
            self.hidden = boolean
            self.world.db.update_from_dict('room_exit', {'dbid': self.dbid, 'hidden': self.hidden})
            return 'Exit attribute "hidden" is now %s.\n' % str(boolean)
    
    def set_locked(self, args):
        try:
            boolean = to_bool(args[0])
        except Exception, e:
            return str(e)
        else:
            self.locked = boolean
            self.world.db.update_from_dict('room_exit', {'dbid': self.dbid, 'locked': self.locked})
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
            self.world.db.update_from_dict('room_exit', {'dbid': self.dbid, 'to_room': self.to_room.dbid})
            return ' The %s exit now goes to room %s in area %s.\n' % (self.direction,
                                                                       self.to_room.id,
                                                                       self.to_room.area.name)
        else:
            return 'That exit is linked. You should unlink it before you set it to somewhere else.\n'

    
    def set_key(self, args):
        # self.world.db.update_from_dict('room_exit', {'dbid': self.dbid, 'key': self.key.dbid})
        return 'This functionality coming soon!\n'
