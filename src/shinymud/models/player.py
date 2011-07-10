from shinymud.data.config import *
from shinymud.commands import *
from shinymud.commands.commands import *
from shinymud.modes.init_mode import InitMode
from shinymud.modes.build_mode import BuildMode
from shinymud.modes.battle_mode import BattleMode
from shinymud.modes.text_edit_mode import TextEditMode
from shinymud.modes.passchange_mode import PassChangeMode
from shinymud.models import Model, Column, model_list
from shinymud.models.shiny_types import *
from shinymud.models.item import GameItem
from shinymud.models.character import Character

import re
from socket import error as socket_error


class Player(Character):
    """Represents a player character."""
    char_type = 'player'
    db_table_name = 'player'
    db_columns = Character.db_columns + [
        Column('name', null=False, unique=True),
        Column('channels', read=read_channels, write=write_dict, default=lambda: dict(chat=True)),
        Column('password', null=False),
        Column('permissions', type="INTEGER", read=int, write=int, null=False, default=1),
        Column('email'),
        Column('location', read=read_location, write=write_location),
        Column('goto_appear'),
        Column('goto_disappear'),
        Column('title',default='a %s player.' % GAME_NAME)
    ]
    
    def __init__(self, connection):
        self.conn = connection
        self.win_size = (None, None)
        self.name = self.conn
        self.inq = []
        self.outq = []
        self.quit_flag = False
        self.mode = InitMode(self)
        self.last_mode = None
        self.dbid = None
        self.channels = {'chat': False}
    
    def playerize(self, args={}):
        self.characterize(args)
        if not self.goto_appear:
            self.goto_appear = '%s appears in the room.' % str(self)
        if not self.goto_disappear:
            self.goto_disappear = '%s disappears in a cloud of smoke.' % str(self)
        self.load_inventory()
    
    def load_inventory(self):
        rows = self.world.db.select('* FROM game_item WHERE owner=?', [self.dbid])
        if rows:
            for row in rows:
                item = GameItem(row)
                item.owner = self
                if item.has_type('equippable'):
                    equip_type = item.item_types['equippable']
                    if equip_type.is_equipped:
                        self.equipped[equip_type.equip_slot] = item
                        self.isequipped.append(item)
                        equip_type.on_equip()
                if item.has_type('container'):
                    item.item_types['container'].load_inventory()
                self.inventory.append(item)
    
    def update_output(self, data):
        """Helpfully inserts data into the player's output queue."""
        if isinstance(data, basestring):
            self.outq.append(data)
        
        elif isinstance(data, list):
            self.outq += data
    
    def get_input(self):
        """Gets raw input from the player and queues it for later processing."""
        data = self.conn.recv()
        if data:
            if isinstance(data, basestring):
                self.inq.append(data)

            elif isinstance(data, list):
                self.inq += data
        
        elif data is None:
            self.player_logout(True)
    
    def send_output(self):
        """Sends all data from the player's output queue to the player."""
        if (len(self.outq) > 0):
            self.enqueue_prompt()
            alive = self.conn.send(self.outq)
        
            if not alive:
                # Sending failed - the connection is no longer alive. We should log
                # the player out
                self.player_logout(True)
    
    def enqueue_prompt(self):
        """Get a prompt for the player."""
        if hasattr(self, 'hp'):
            default = '<HP:%s/%s MP:%s/%s> ' % (str(self.hp), str(self.max_hp), str(self.mp), str(self.max_mp))
        else:
            default = '> '
            
        if not self.mode:
            self.outq.append(default)
        
        elif self.mode.name == 'BuildMode':
            prompt = '<Build'
            if self.mode.edit_area:
                prompt += ' ' + self.mode.edit_area.name
            if self.mode.edit_object:
                prompt += ' ' + self.mode.edit_object.__class__.__name__ + ' ' + str(self.mode.edit_object.id)
            prompt += '> '
            self.outq.append(prompt)
            
        elif self.mode.name == 'TextEditMode':
            self.outq.append('> ')
        elif self.mode.name == 'PassChangeMode':
            self.outq.append('> ')
    
    
    def parse_command(self):
        """Parses the lines in the player's input buffer and then calls
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
                    # The command the player sent was invalid... tell them so
                    self.update_output("I don't understand \"%s\"\n" % raw_string)
    
    def do_tick(self):
        """What should happen to the player everytime the world ticks."""
        if self.quit_flag:
            self.player_logout()
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
    
    def player_logout(self, broken_pipe=False):
        # If this player doesn't have a dbid, that means this player got
        # disconnected before they made it through the character creation
        # process. Don't save the incomplete data.
        if self.dbid:
            self.save()
            
            if not broken_pipe:
                self.world.play_log.info('%s has exited.' % self.fancy_name())
            else:
                self.world.play_log.info('%s has been disconnected (broken pipe).' % self.fancy_name())
            self.conn.close()
            if hasattr(self, 'location') and self.location:
                self.location.remove_char(self)
            self.world.player_remove(self.name)
            self.world.tell_players("%s has left the world." % self.fancy_name())
        else:
            # If they didn't make it through the CC process, just close the connection
            self.conn.close()
            self.world.player_remove(self.name)
            self.world.log.debug("Logging out an unnamed player.")
    
    def set_mode(self, mode):
        if mode == 'build':
            self.mode = BuildMode(self)
        elif mode == 'normal':
            self.mode.active = False
        elif mode == 'battle':
            self.mode = BattleMode(self)
        elif mode == 'passwd':
            self.mode = PassChangeMode(self)
    
    def get_mode(self):
        """Returns the name of the mode the player is in, or empty string if the
        player isn't in a special mode.
        """
        if not self.mode:
            return ''
        else:
            return self.mode.name
    
    def set_email(self, email):
        if not email:
            return 'What do you want to set your email address to?'
        self.email = email
        self.save()
        return 'Your e-mail address is now "%s".' % email
    
    def set_description(self, description):
        """Set the description for this player."""
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
        self.save()
        return 'Your title is now "%s".' % self.title
    
    def set_goto_appear(self, appear):
        if self.permissions & (DM | ADMIN | BUILDER | GOD):
            if not appear:
                return 'What do you want to set your goto_appear message to?'
            self.goto_appear = appear
            self.save()
            return 'Goto-appear message set.'
        else:
            return 'You don\'t have the permissions to set that.'
    
    def set_goto_disappear(self, disappear):
        if self.permissions & (DM | ADMIN | BUILDER | GOD):
            if not disappear:
                return 'What do you want to set your goto_disappear message to?'
            self.goto_disappear = disappear
            self.save()
            return 'Goto-disappear message set.'
        else:
            return 'You don\'t have the permissions to set that.'
    
    def fancy_name(self):
        """Return a capitalized version of the player's name."""
        return self.name.capitalize()
    
    def look_at_room(self):
        """Return this player's view of the room they are in."""
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
        players = ''
        for player in self.location.players.values():
            if player.name != self.name:
                position = ' is here.'
                if player.position[0] == 'sleeping':
                    if player.position[1]:
                        position = ' is here, sleeping on %s.' % player.position[1].name
                    else:
                        position = ' is here, sleeping on the floor.'
                elif player.position[0] == 'sitting':
                    if player.position[1]:
                        position = ' is here, sitting on %s.' % player.position[1].name
                    else:
                        position = ' is here, sitting on the floor.'
                players += player_color + player.fancy_name() + position +\
                         clear_fcolor + '\n'
        npcs = ''
        for npc in self.location.npcs:
            npcs += npc_color + npc.title + clear_fcolor + '\n'
        items = ''
        for item in self.location.items:
            if item.title:
                items += item_color + item.title + clear_fcolor + '\n'
        desc = room_body_color + '  ' + self.location.description + clear_fcolor
        look = """%s\n%s\n%s\n%s%s%s""" % (title, xits, desc, items, npcs, players)
        return look
    
    def cycle_effects(self):
        for name in self.effects.keys():
            if self.effects[name].duration > 0:
                self.effects[name].execute()
            else:
                self.effects[name].end()
                del self.effects[name]
    
    def effects_add(self, effect_list):
        """Add a list of character effects to the player."""
        self.world.log.debug(effect_list)
        for effect in effect_list:
            effect.char = self
            if effect.name in self.effects:
                self.effects[effect.name].combine(effect)
                self.world.log.debug(effect.duration)
            else:
                self.effects[effect.name] = effect
                self.world.log.debug(effect.duration)
            
            self.effects[effect.name].begin()
    
    def effect_remove(self, effect):
        """Remove an effect from this player."""
        if effect.name in self.effects:
            del self.effects[effect.name]
    
    def death(self):
        # Send character to the default location, with 1 hp.
        self.hp = 1
        self.world.log.debug("%s has died." % self.fancy_name())
        self.update_output('You Died.')
        self.go(self.world.get_location(DEFAULT_LOCATION[0], DEFAULT_LOCATION[1]))
    
    def destruct(self):
        for item in self.inventory:
            item.destruct()
        Character.destruct(self)
    

model_list.register(Player)
