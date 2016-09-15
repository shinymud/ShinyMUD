from shinymud.models import Model, Column, model_list
from shinymud.models.shiny_types import *
from shinymud.data.config import *
import re

class RoomExit(Model):
    db_table_name = 'room_exit'
    db_columns = Model.db_columns + [
        Column('to_room_id', null=False),
        Column('to_area', null=False),
        # I always expect room to be passed in by the function calling this class'
        # constructor. For this reason, I'm not bothering with a more elaborate
        # read function for room_id.
        Column('room', null=False, write=write_model),
        Column('direction', null=False),
        Column('linked_exit'),
        Column('openable', read=to_bool),
        Column('closed', read=to_bool),
        Column('hidden', read=to_bool),
        Column('locked', read=to_bool),
        Column('key_area'),
        Column('key_id')
    ]
    db_extras = Model.db_extras + ['UNIQUE (room, direction)']
    
    def __init__(self, args={}):
        Model.__init__(self, args)
        # Initialize the current state of the door from the default settings:
        self._closed = self.closed
        self._locked = self.locked
        if 'to_room' in args:
            self.to_room = args.get('to_room')
    
    def save(self, save_dict=None):
        if not self.to_room:
            # Quick Hack:
            # if for some reason the to_room to this room has become None, don't
            # save it! This should be fixed in later code so that it won't be
            # possible
            return
        Model.save(self)
    
    def unlink(self):
        """Unlink any corresponding exits if they exist."""
        if self.linked_exit:
            # Remove the door I point to
            self.linked_exit = None
            # Remove the door that points to me 
            self.to_room.linked_exit = None
    
    def _resolve_to_room(self):
        if getattr(self, '_to_room', None):
            return self._to_room
        try:
            self.to_room = self.world.get_area(str(self.to_area)).get_room(str(self.to_room_id))
            return self._to_room
        except:
            return None
    
    def _set_to_room(self, to_room):
        self._to_room = to_room
        if to_room:
            self.to_area = to_room.area.name
            self.to_room_id = to_room.id
    
    to_room = property(_resolve_to_room, _set_to_room)
    
    def _resolve_key(self):
        if getattr(self, '_key', None):
            return self._key
        if self.key_area and self.key_id:
            try: 
                self.key = self.world.get_area(self.key_area).get_item(self.key_id)
                return self._key
            except:
                pass
        return None
    
    def _set_key(self, key):
        self._key = key
        if key:
            self.key_area = key.area.name
            self.key_id = key.id
        else:
            self.key_area = None
            self.key_id = None
    key = property(_resolve_key, _set_key)
    
    def _str_key(self):
        if self.key:
            return '%s (%s, %s)' % (self.key.name, self.key.id, self.key.area.name)
        else:
            return 'None'
    
    def __str__(self):
        linked = "false"
        if self.linked_exit:
            linked = "true"
        list_exit = "[to: %s-%s, linked: %s, openable: %s, closed: %s, hidden: %s, locked: %s, key: %s]" % (self.to_room.area.name, self.to_room.id, linked,
                                                                                                        str(self.openable), str(self.closed),
                                                                                                        str(self.hidden), str(self.locked),
                                                                                                        self._str_key())
        return list_exit
    
    def reset(self):
        """Reset all closed/locked states back to their defaults."""
        self._closed = self.closed
        self._locked = self.locked
        # if self.linked_exit:
        #     to_exit = self.to_room.exits[self.linked_exit]
        #     to_exit._closed = to_exit.closed
        #     to_exit.locked = to_exit.locked
    
    def close_me(self, player):
        if self.openable == False:
            return 'You can\'t close that.\n'
        if self._closed:
            return 'It\'s already closed.\n'
        self._closed = True
        self.room.tell_room('%s closed the %s door.\n' % (player.fancy_name(), self.direction), [player.name])
        if self.linked_exit:
            self.to_room.exits[self.linked_exit]._closed = True
            self.to_room.tell_room('The %s door was closed from the other side.\n' % self.linked_exit)
        return 'You close the %s door.\n' % self.direction
    
    def open_me(self, player):
        if self.openable == False:
            return 'You can\'t open that.'
        if not self._closed:
            return 'It\'s already open.'
        r_msg = p_msg = ''
        if self.key and self._locked:
            if player.permissions & GOD:
                p_msg = 'The %s door unlocks itself at your divine bidding.\n' % (self.direction)
                r_msg = 'The %s door unlocks itself at %s\'s divine bidding.\n' % (self.direction, player.fancy_name())
            elif player.has_item(self.key):
                self._locked = False
                p_msg = 'You unlock the door with %s.\n' % self.key.name
                r_msg = '%s unlocks the door with %s.\n' % (player.fancy_name(), self.key.name)
            else:
                return "It's locked."
        self._closed = False
        r_msg += '%s opens the %s door.' % (player.fancy_name(), self.direction)
        self.room.tell_room(r_msg, [player.name])
        if self.linked_exit:
            self.to_room.exits[self.linked_exit]._closed = False
            self.to_room.tell_room('The %s door was opened from the other side.\n' % self.linked_exit)
        p_msg += 'You open the %s door.\n' % self.direction
        return p_msg
    
    def lock_me(self, player):
        if self.key and (player.permissions & GOD or player.has_item(self.key)):
            self._locked = True
            message = self.close_me(player)
            self.room.tell_room('%s locked the %s door.\n' % (player.fancy_name(), self.direction), [player.name])
            if self.linked_exit:
                self.to_room.exits[self.linked_exit]._locked = True
                self.to_room.tell_room('The %s door was locked from the other side.\n' % self.linked_exit)
            return message + "You lock it."
        return "You can't lock that."
    
    def build_set_closed(self, args):
        try:
            boolean = to_bool(args[0])
        except Exception as e:
            return str(e)
        else:
            self.closed = boolean
            self._closed = boolean
            if self.linked_exit:
                self.to_room.exits[self.linked_exit].closed = boolean
                self.to_room.exits[self.linked_exit]._closed = boolean
                self.to_room.exits[self.linked_exit].save()
            self.save()
            return 'Exit attribute "closed" is now %s.' % str(boolean)
    
    def build_set_openable(self, args):
        boolean = to_bool(args[0])
        if not boolean:
            return 'Acceptable values are true or false.'
        else:
            self.openable = boolean
            self.save()
            if self.linked_exit:
                self.to_room.exits[self.linked_exit].openable = boolean
                self.to_room.exits[self.linked_exit].save()
            return 'Exit attribute "openable" is now %s.\n' % str(boolean)
    
    def build_set_hidden(self, args):
        try:
            boolean = to_bool(args[0])
        except Exception as e:
            return str(e)
        else:
            self.hidden = boolean
            self.save()
            return 'Exit attribute "hidden" is now %s.\n' % str(boolean)
    
    def build_set_locked(self, args):
        try:
            boolean = to_bool(args[0])
        except Exception as e:
            return str(e)
        else:
            self.locked = boolean
            self._locked = boolean
            self.save()
            if self.linked_exit:
                self.to_room.exits[self.linked_exit].locked = boolean
                self.to_room.exits[self.linked_exit]._locked = boolean
                self.to_room.exits[self.linked_exit].save()
            return 'Exit attribute "locked" is now %s.\n' % str(boolean)
    
    def build_set_to(self, args):
        """Set the to_room attribute to point to a new room."""
        if not args:
            return 'Usage: set exit <direction> to room <room-id> in area <area-name>\n'
        exp = r'([ ]+)?room?(?P<room_id>\d+)(([ ]+in)?([ ]+area)?([ ]+(?P<area_name>\w+)))?'
        match = re.match(exp, ''.join(args), re.I)
        if not match:
            return 'Usage: set exit <direction> to room <room-id> in area <area-name>\n'
        
        room_id, area_name = match.group('room_id', 'area_name')
        if area_name:
            area = World.get_world().get_area(area_name)
            if not area:
                return 'That area doesn\'t exist.\n'
        else:
            area = self.room.area
        room = area.get_room(room_id)
        if not room:
            return 'That room doesn\'t exist.\n'
        if not room.linked_exit:
            self.to_room = room
            self.save()
            return ' The %s exit now goes to room %s in area %s.\n' % (self.direction,
                                                                       self.to_room.id,
                                                                       self.to_room.area.name)
        else:
            return 'That exit is linked. You should unlink it before you set it to somewhere else.\n'
    
    def build_set_key(self, args):
        if not args:
            return 'Usage: set exit <direction> key <item-id> from area <area-name>\n'
        exp = r'([ ]+)?(?P<key_id>\d+)(([ ]+in)?([ ]+area)?([ ]+(?P<area_name>\w+)))?'
        match = re.match(exp, ''.join(args), re.I)
        if not match:
            return 'Usage: set key <item-id> from area <area-name>\n'
        key_id, area_name = match.group('key_id', 'area_name')
        if area_name:
            area = self.world.get_area(area_name)
            if not area:
                return 'That area doesn\'t exist.\n'
        else:
            area = self.room.area
        key = area.get_item(key_id)
        if not key:
            return 'That item doesn\'t exist.\n'
        self.key = key
        self.save()
        if self.linked_exit:
            self.to_room.exits[self.linked_exit].key = self.key
            self.to_room.exits[self.linked_exit].save()
        return '%s has been added as a key to room %s\'s %s exit.\n' % (key.name.capitalize(),
                                                                        self.room.id,
                                                                        self.direction)
    

model_list.register(RoomExit)