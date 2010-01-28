from shinymud.data.config import *
from shinymud.commands import *
from shinymud.commands.commands import *
from shinymud.modes.init_mode import InitMode
from shinymud.modes.build_mode import BuildMode
from shinymud.modes.text_edit_mode import TextEditMode
from shinymud.lib.world import World
from shinymud.models.item import InventoryItem, SLOT_TYPES
import re
import logging

class User(object):
    """This is a basic user object."""
        
    def __init__(self, conn_info):
        self.conn, self.addr = conn_info
        self.name = self.conn
        self.inq = []
        self.outq = []
        self.quit_flag = False
        self.log = logging.getLogger('User')
        self.mode = InitMode(self)
        self.last_mode = None
        self.dbid = None
        self.world = World.get_world()
        self.channels = {'chat': False}
    
    def userize(self, **args):
        self.name = str(args.get('name'))
        self.password = args.get('password', None)
        self.description = str(args.get('description','You see nothing special about this person.'))
        self.title = str(args.get('title', ''))
        self.gender = str(args.get('gender', 'neutral'))
        self.strength = args.get('strength', 0)
        self.intelligence = args.get('intelligence', 0)
        self.dexterity = args.get('dexterity', 0)
        self.hp = args.get('hp', 0)
        self.mp = args.get('mp', 0)
        self.max_mp = args.get('max_mp', 0)
        self.max_hp = args.get('max_hp', 20)
        self.speed = args.get('speed', 0)
        self.email = str(args.get('email'))
        self.permissions = int(args.get('permissions', 1))
        self.dbid = args.get('dbid')
        self.goto_appear = args.get('goto_appear', 
            '%s appears in the room.' % self.fancy_name())
        self.goto_disappear = args.get('goto_disappear', 
            '%s disappears in a cloud of smoke.' % self.fancy_name())
        if 'channels' in args:
            self.channels = dict([_.split('=') for _ in args['channels'].split(',')])
        else:
            self.channels = {'chat': True}
        self.inventory = []
        self.equipped = {} #Stores current weapon in each slot from SLOT_TYPES
        for i in SLOT_TYPES.keys():
            self.equipped[i] = ''
        self.isequipped = [] #Is a list of the currently equipped weapons
        rows = self.world.db.select('* FROM inventory WHERE owner=?', [self.dbid])
        if rows:
            for row in rows:
                item = InventoryItem(**row)
                self.inventory.append(item)
        self.location = args.get('location')
        if self.location:
            loc = args.get('location').split(',')
            self.log.debug(loc)
            try:
                self.location = self.world.get_area(loc[0]).get_room(loc[1])
            except:
                # This should only EVER happen if for some reason the location
                # of the user was deleted while they were offline.  This probably
                # shouldn't happen often. Also, instead of being None, this should
                # be the Default starting location when that becomes
                # applicable
                self.location = None
            
    
    def to_dict(self):
        d = {}
        d['channels'] = ",".join([str(key) + '=' + str(val) for key, val in self.channels.items()])
        d['name'] = self.name
        d['password'] = self.password
        d['strength'] = self.strength
        d['intelligence'] = self.intelligence
        d['dexterity'] = self.dexterity
        d['hp'] = self.hp
        d['mp'] = self.mp
        d['max_hp'] = self.max_hp
        d['max_mp'] = self.max_mp
        d['speed'] = self.speed
        d['description'] = self.description
        d['gender'] = self.gender
        d['permissions'] = self.permissions
        d['goto_appear'] = self.goto_appear
        d['goto_disappear'] = self.goto_disappear
        d['title'] = self.title
        if self.email:
            d['email'] = self.email
        if self.dbid:
            d['dbid'] = self.dbid
        if self.location:
            d['location'] = '%s,%s' % (self.location.area.name, self.location.id)
        
        return d
    
    def save(self, save_dict=None):
        if self.dbid:
            if save_dict:
                save_dict['dbid'] = self.dbid
                self.world.db.update_from_dict('user', save_dict)
            else:    
                self.world.db.update_from_dict('user', self.to_dict())
        else:
            self.dbid = self.world.db.insert_from_dict('user', self.to_dict())
    
    def update_output(self, data, terminate_ln=True, strip_nl=True):
        """Helpfully inserts data into the user's output queue."""
        if strip_nl:
            # Since we need to terminate with lf and cr for telnet anyway,
            # we might as well strip all extra newlines off the end of
            # everything anyway. If for some reason the output needs to have
            # extra newlines at the end, pass strip_nl=False
            data = data.rstrip('\n')
        if terminate_ln:
            # If you want the user to enter input on the same line as the
            # last output, pass terminate_ln=False. Otherwise the line will
            # be terminated and a prompt will be added.
            data += '\r\n'
        self.outq.append(data)
    
    def get_input(self):
        """Gets raw input from the user and queues it for later processing."""
        try:
            new_stuff = self.conn.recv(256)
            self.inq.append(new_stuff.replace('\n', '').replace('\r', ''))
        except Exception, e:
            pass
    
    def send_output(self):
        """Sends all data from the user's output queue to the user."""
        try:
            sent_output = ''
            while len(self.outq) > 0:
                self.conn.send(self.outq[0])
                sent_output = self.outq[0]
                del self.outq[0]
            if sent_output.endswith('\r\n'):
                self.conn.send(self.get_prompt())
        except Exception, e:
            # If we die here, it's probably because we got a broken pipe.
            # In this case, we should disconnect the user
            self.user_logout(True)
            print str(e)
    
    def get_prompt(self):
        default = '>'
        if not self.mode:
            return default
        elif self.mode.name == 'BuildMode':
            prompt = '<Build'
            if self.mode.edit_area:
                prompt += ' ' + self.mode.edit_area.name
            if self.mode.edit_object:
                prompt += ' ' + self.mode.edit_object.__class__.__name__ + ' ' + str(self.mode.edit_object.id)
            prompt += '>'
            return prompt
        else:
            return default
    
    def parse_command(self):
        """Parses the lines in the user's input buffer and then calls
        the appropriate commands (if they exist)"""
        
        while len(self.inq) > 0:
            raw_string = self.inq.pop(0)
            match = re.search(r'\s*(\w+)([ ](.+))?$', raw_string)
            if match:
                cmd_name, _, args = match.groups()
                cmd = command_list[cmd_name]
                if cmd:
                    cmd(self, args, cmd_name).run()
                else:
                    # The command the user sent was invalid... tell them so
                    self.update_output("I don't understand \"%s\"\n" % raw_string)
    
    def do_tick(self):
        """What should happen to the user everytime the world ticks."""
        if self.quit_flag:
            self.user_logout()
        else:
            self.get_input()
            if not self.mode:
                self.parse_command()
            elif self.mode.active:
                self.mode.state()
                if not self.mode.active:
                    if self.last_mode:
                        self.mode = self.last_mode
                    else:
                        self.mode = None
    
    def user_logout(self, broken_pipe=False):
        self.world.db.update_from_dict('user', self.to_dict())
        if not broken_pipe:
            self.conn.send('Bye!\n')
        self.conn.close()
        if self.location:
            self.location.user_remove(self)
        self.world.user_remove(self.name)
        self.world.tell_users("%s has left the world." % self.fancy_name())
    
    def fancy_name(self):
        return self.name.capitalize()
    
    def set_mode(self, mode):
        if mode == 'build':
            self.mode = BuildMode(self)
        elif mode == 'normal':
            self.mode.active = False
    
    def set_email(self, email):
        if not email:
            return 'What do you want to set your email address to?'
        self.email = email
        self.save({'email': self.email})
        return 'Your e-mail address is now "%s".' % email
    
    def set_description(self, description):
        """Set the description for this user."""
        self.last_mode = self.mode
        self.mode = TextEditMode(self, self, 'description', self.description)
        return 'ENTERING TextEditMode: type "@help" for help.'
    
    def set_title(self, title):
        if not title:
            return 'What do you want your title to be?'
        if len(title) > 30:
            return ('That\'s too long for a title. '
                    'Try something under 30 characters.')
        self.title = title
        self.save({'title': self.title})
        return 'Your title is now "%s".' % self.title
    
    def set_goto_appear(self, appear):
        if self.permissions & (DM | ADMIN | BUILDER | GOD):
            if not appear:
                return 'What do you want to set your goto_appear message to?'
            self.goto_appear = appear
            self.save({'goto_appear': self.goto_appear})
            return 'Goto-appear message set.'
        else:
            return 'You don\'t have the permissions to set that.'
    
    def set_goto_disappear(self, disappear):
        if self.permissions & (DM | ADMIN | BUILDER | GOD):
            if not disappear:
                return 'What do you want to set your goto_disappear message to?'
            self.goto_disappear = disappear
            self.save({'goto_disappear': self.goto_disappear})
            return 'Goto-disappear message set.'
        else:
            return 'You don\'t have the permissions to set that.'
    
    def item_add(self, item):
        """Add an item to the user's inventory."""
        item.owner = self.dbid
        item.save({'owner': item.owner})
        self.inventory.append(item)
    
    def item_remove(self, item):
        """Remove an item from the user's inventory."""
        if item in self.inventory:
            item.owner = None
            item.save({'owner': item.owner})
            self.inventory.remove(item)
    
    def go(self, room, tell_new=None, tell_old=None):
        """Go to a specific room."""
        if self.location:
            if tell_old:
                self.location.tell_room(tell_old, [self.name])
            self.location.user_remove(self)
        if self.location and self.location == room:
            self.update_output('You\'re already there.\n')
        else:
            self.location = room
            self.location.user_add(self)
            if tell_new:
                self.location.tell_room(tell_new, [self.name])
            self.update_output(self.look_at_room())
    
    def check_inv_for_keyword(self, keyword):
        """Check all of the items in a user's inventory for a specific keyword.
        
        Return the item that matches that keyword, else return None."""
        for item in self.inventory:
            if keyword in item.keywords:
                return item
        return None
    
    def look_at_room(self):
        """Return this user's view of the room they are in."""
        title = room_title_color + self.location.name + clear_fcolor
        if self.mode and self.mode.name == 'BuildMode':
            title = '%s[id: %s]%s %s%s%s' % (room_id_color, 
            self.location.id, clear_fcolor, room_title_color,
            self.location.name, clear_fcolor)
        exit_list = [key for key, value in self.location.exits.items() if value != None]
        xits = 'exits: None'
        if exit_list:
            xits = 'exits: ' + ', '.join(exit_list)
        xits = room_exit_color + xits + clear_fcolor
        users = ''
        for user in self.location.users.values():
            if user.name != self.name:
                users += user_color + user.fancy_name() + ' is here.' +\
                         clear_fcolor + '\n'
        npcs = ''
        for npc in self.location.npcs:
            npcs += npc_color + npc.title + clear_fcolor + '\n'
        items = ''
        for item in self.location.items:
            items += item_color + item.title + clear_fcolor + '\n'
        desc = room_body_color + self.location.description + clear_fcolor
        look = """%s\n%s\n%s\n%s%s%s""" % (title, xits, desc, users, npcs, items)
        return look
    
