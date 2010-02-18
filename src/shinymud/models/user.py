from shinymud.data.config import *
from shinymud.commands import *
from shinymud.commands.commands import *
from shinymud.modes.init_mode import InitMode
from shinymud.modes.build_mode import BuildMode
from shinymud.modes.battle_mode import BattleMode
from shinymud.modes.text_edit_mode import TextEditMode
from shinymud.lib.world import World
from shinymud.models.item import InventoryItem, SLOT_TYPES
from shinymud.models.character import Character
import re
import logging

class User(Character):
    """Represents a player character (user)."""
    char_type = 'user'
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
        self.position = ('standing', None)
    
    def userize(self, **args):
        self.characterize(**args)
        self.name = str(args.get('name'))
        self.password = args.get('password', None)
        self.description = str(args.get('description','You see nothing special about this person.'))
        self.title = str(args.get('title', 'a %s player.' % GAME_NAME))
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
        self.isequipped = [] #Is a list of the currently equipped weapons
        
        self.location = args.get('location')
        if self.location:
            loc = args.get('location').split(',')
            self.log.debug(loc)
            self.location = self.world.get_location(loc[0], loc[1])
        if self.dbid:
            self.load_inventory()
        self.effects = {}
    
    def load_inventory(self):
        rows = self.world.db.select('* FROM inventory WHERE owner=?', [self.dbid])
        if rows:
            for row in rows:
                item = InventoryItem(**row)
                if item.is_container():
                    item.item_types.get('container').load_contents()
                self.inventory.append(item)
    
    def to_dict(self):
        d = Character.to_dict(self)
        d['channels'] = ",".join([str(key) + '=' + str(val) for key, val in self.channels.items()])
        d['name'] = self.name
        d['password'] = self.password
        d['description'] = self.description
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
        elif self.mode.name == 'BattleMode':
            prompt = '<HP:%s/%s MP:%s/%s>' % (str(self.hp), str(self.max_hp), str(self.mp), str(self.max_mp))
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
            if self.dbid:
                self.cycle_effects()
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
            else:
                # If we get here somehow (where the state of this mode is not
                # active, but the mode has not been cleared), just clear the
                # mode.
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
    
    def set_mode(self, mode):
        if mode == 'build':
            self.mode = BuildMode(self)
        elif mode == 'normal':
            self.mode.active = False
        elif mode == 'battle':
            self.mode = BattleMode(self)
    
    def get_mode(self):
        """Returns the name of the mode the user is in, or empty string if the
        user isn't in a special mode.
        """
        if not self.mode:
            return ''
        else:
            return self.mode.name
    
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
    
    def fancy_name(self):
        """Return a capitalized version of the player's name."""
        return self.name.capitalize()
    
    def look_at_room(self):
        """Return this user's view of the room they are in."""
        title = room_title_color + self.location.name + clear_fcolor
        if self.mode and self.mode.name == 'BuildMode':
            title = '%s[id: %s, %s]%s %s%s%s' % (room_id_color, 
            self.location.id, self.location.area.name, clear_fcolor,
            room_title_color, self.location.name, clear_fcolor)
        exit_list = [key for key, value in self.location.exits.items() if value != None]
        xits = 'exits: None'
        if exit_list:
            xits = 'exits: ' + ', '.join(exit_list)
        xits = room_exit_color + xits + clear_fcolor
        users = ''
        for user in self.location.users.values():
            if user.name != self.name:
                position = ' is here.'
                if user.position[0] == 'sleeping':
                    if user.position[1]:
                        position = ' is here, sleeping on %s.' % user.position[1].name
                    else:
                        position = ' is here, sleeping on the floor.'
                elif user.position[0] == 'sitting':
                    if user.position[1]:
                        position = ' is here, sitting on %s.' % user.position[1].name
                    else:
                        position = ' is here, sitting on the floor.'
                users += user_color + user.fancy_name() + position +\
                         clear_fcolor + '\n'
        npcs = ''
        for npc in self.location.npcs:
            npcs += npc_color + npc.title + clear_fcolor + '\n'
        items = ''
        for item in self.location.items:
            if item.title:
                items += item_color + item.title + clear_fcolor + '\n'
        desc = room_body_color + '  ' + self.location.description + clear_fcolor
        look = """%s\n%s\n%s\n%s%s%s""" % (title, xits, desc, items, npcs, users)
        return look
    
    def change_position(self, pos, furniture=None):
        """Change the user's position."""
        if self.position[1]:
            self.position[1].item_types['furniture'].user_remove(self)
        if furniture:
            furniture.item_types['furniture'].user_add(self)
        self.position = (pos, furniture)
    
    def cycle_effects(self):
        for name in self.effects.keys():
            if self.effects[name].duration > 0:
                self.effects[name].execute()
            else:
                self.effects[name].end()
                del self.effects[name]
    
    def effects_add(self, effect_list):
        for effect in effect_list:
            effect.char = self
            if effect.name in self.effects:
                self.effects[effect.name].combine(effect)
            else:
                self.effects[effect.name] = effect
    
    def effect_remove(self, effect):
        if effect.name in self.effects:
            del self.effects[effect.name]
    
