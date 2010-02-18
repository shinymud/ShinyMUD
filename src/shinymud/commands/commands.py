from shinymud.models.item import  SLOT_TYPES
from shinymud.lib.world import World
from shinymud.data.config import *
from shinymud.commands.emotes import *
from shinymud.commands.attacks import *
from shinymud.commands import *
from shinymud.lib.battle import Battle
import re
import logging
   
# ************************ GENERIC COMMANDS ************************
command_list = CommandRegister()
battle_commands = CommandRegister()
class Quit(BaseCommand):
    help = (
    """Quit (Command)
The quit command logs you out of the game, saving your character in the
process.
\nALIASES:
  exit
    """
    )
    def execute(self):
        self.user.quit_flag = True
    

command_list.register(Quit, ['quit', 'exit'])
command_help.register(Quit.help, ['quit', 'exit'])

class WorldEcho(BaseCommand):
    """Echoes a message to everyone in the world.
    args:
        args = message to be sent to every user in the world.
    """
    required_permissions = ADMIN
    help = (
    """WorldEcho (Command)
WorldEcho echoes a message to all users currently in the world.
\nRequired Permissions: ADMIN
    """
    )
    def execute(self):
        self.world.tell_users(self.args)
    

command_list.register(WorldEcho, ['wecho', 'worldecho'])
command_help.register(WorldEcho.help, ['wecho', 'world echo', 'worldecho'])

class Chat(BaseCommand):
    """Sends a message to every user on the chat channel."""
    help = (
    """Chat (command)
The Chat command will let you send a message to everyone in the world whose
chat channels are on. See "help channel" for help on turning you chat
channel off.
    """
    )
    def execute(self):
        if not self.user.channels['chat']:
            self.user.channels['chat'] = True
            self.user.update_output('Your chat channel has been turned on.\n')
        message = '%s chats, "%s"' % (self.user.fancy_name(), self.args)
        exclude = [user.name for user in self.world.user_list.values() if not user.channels['chat']]
        self.world.tell_users(message, exclude, chat_color)
    

command_list.register(Chat, ['chat', 'c'])
command_help.register(Chat.help, ['chat'])

class Channel(BaseCommand):
    """Toggles communication channels on and off."""
    help = (
"""Channel (command)
The channel command toggles your communication channels on or off.
\nUSAGE:
To see which channels you have on/off, just call channel with no options.
To turn a channel on:
  channel <channel-name> on
To turn a channel off:
  channel <channel-name> off
\nExamples:
If you no longer want to receive chat messages, you can turn your chat channel
off by doing the following:
  channel chat off
\nCHANNELS:
Current channels that can be turned on and off via Channel:
  chat
\nNOTE: If you use a channel that has been turned off (such as trying to send
a chat message after you've turned off your chat channel), it will
automatically be turned back on.
"""
    )
    def execute(self):
        if not self.args:
            chnls = 'Channels:'
            for key, value in self.user.channels.items():
                if value:
                    chnls += '\n  ' + key + ': ' + 'on'
                else:
                    chnls += '\n  ' + key + ': ' + 'off'
            self.user.update_output(chnls)
            return
        toggle = {'on': True, 'off': False}
        args = self.args.split()
        channel = args[0].lower()
        choice = args[1].lower()
        if channel in self.user.channels.keys():
            if choice in toggle.keys():
                self.user.channels[channel] = toggle[choice]
                self.user.update_output('The %s channel has been turned %s.\n' % (channel, choice))
            else:
                self.user.update_output('You can only turn the %s channel on or off.\n' % channel)
        else:
            self.user.update_output('Which channel do you want to change?\n')
    

command_list.register(Channel, ['channel'])
command_help.register(Channel.help, ['channel'])

class Build(BaseCommand):
    """Activate or deactivate build mode."""
    required_permissions = BUILDER
    help = (
"""Build (Command)
The build command allows builders (players with the BUILDER permission) to
access BuildMode, which allows them to construct areas, rooms, items, etc.
\nRequired Permissions: BUILDER
\nUSAGE:
To enter BuildMode:
  build [<area_name>]
To exit BuildMode:
  build exit
To enter BuildMode and edit your current location:
  build here
\nFor a list of BuildCommands, see "help build commands".
"""
    )
    def execute(self):
        if not self.args:
            # User wants to enter BuildMode
            self.enter_build_mode()
        elif self.args == 'exit':
            if self.user.get_mode() == 'BuildMode':
                self.user.set_mode('normal')
                self.user.update_output('Exiting BuildMode.')
            else:
                self.user.update_output('You\'re not in BuildMode right now.')
        elif self.args == 'here':
            # Builder wants to start building at her current location
            if self.user.location:
                if self.user.get_mode() != 'BuildMode':
                    self.enter_build_mode()
                self.edit(self.user.location.area, self.user.location)
            else:
                self.user.update_output('You\'re in the void; there\'s nothing to build.')
        else:
            area = self.world.get_area(self.args)
            if not area:
                self.user.update_output('Area "%s" doesn\'t exist.' % self.args)
                self.user.update_output('See "help buildmode" for help with this command.')
            self.edit(area)
    
    def enter_build_mode(self):
        """The user should enter BuildMode."""
        if self.user.get_mode() == 'BuildMode':
            self.user.update_output('To exit BuildMode, type "build exit".')
        else:
            self.user.set_mode('build')
            self.user.update_output('Entering BuildMode.')
    
    def edit(self, area, room=None):
        """Initialize the user's edit_area (and possible edit_object.). This
        is super hackish, as I'm reproducing code from the BuildCommand Edit.
        I just didn't want to create an import cycle for the sake of accessing
        one command and was too lazy to change things around to work better.
        Should probably clean this up in the future.
        """
        if (self.user.name in area.builders) or (self.user.permissions & GOD):
            self.user.mode.edit_area = area
            self.user.mode.edit_object = None
            if room:
                self.user.mode.edit_object = room
                self.user.update_output('Now editing room %s in area "%s".' %
                                        (room.id, area.name))
            else:
                self.user.update_output('Now editing area "%s".' % area.name)
        else:
            self.user.update_output('You can\'t edit someone else\'s area.')

command_list.register(Build, ['build'])
command_help.register(Build.help, ['build', 'build mode'])

class Look(BaseCommand):
    """Look at a room, item, npc, or PC."""
    def execute(self):
        message = 'You don\'t see that here.\n'
        if not self.args:
            # if the user didn't specify anything to look at, just show them the
            # room they're in.
            message = self.look_at_room()
        else:
            exp = r'(at[ ]+)?((?P<thing1>(\w|[ ])+)([ ]in[ ](?P<place>(room)|(inventory)|)))|(?P<thing2>(\w|[ ])+)'
            match = re.match(exp, self.args, re.I)
            if match:
                thing1, thing2, place = match.group('thing1', 'thing2', 'place')
                thing = thing1 or thing2
                if place:
                    obj_desc = getattr(self, 'look_in_' + place)(thing)
                else:
                    obj_desc = self.look_in_room(thing) or self.look_in_inventory(thing)
                if obj_desc:
                    message = obj_desc
        
        self.user.update_output(message)
    
    def look_at_room(self):
        if self.user.location:
            return self.user.look_at_room()
        else:
            return 'You see a dark void.'
    
    def look_in_room(self, keyword):
        if self.user.location:
            obj = self.user.location.check_for_keyword(keyword)
            if obj:
                if self.alias == 'read':
                    return obj.description
                message = "You look at %s:\n%s" % (obj.name, obj.description)
                if hasattr(obj, 'is_container') and obj.is_container():
                    message += '\n' + obj.item_types.get('container').display_inventory()
                return message
        return None
    
    def look_in_inventory(self, keyword):
        item = self.user.check_inv_for_keyword(keyword)
        if item:
            message = "You look at %s:\n%s" % (item.name, item.description)
            if item.is_container():
                message += '\n' + item.item_types.get('container').display_inventory()
            return message
        return None
    

command_list.register(Look, ['look', 'read'])

class Goto(BaseCommand):
    """Go to a location."""
    required_permissions = BUILDER | DM | ADMIN
    help = (
    """Goto (Command)
The goto command will transport your character to a specific location.
\nUSAGE:
To go to the same room as a specific player:
  goto <player-name>
To go to a room in the same area you're in:
  goto [room] <room-id>
To go to a room in a different area:
  goto [room] <room-id> [in area] <area-name>
    """
    )
    def execute(self):
        if not self.args:
            self.user.update_output('Where did you want to go to?')
            return
        exp = r'((room)?([ ]?(?P<room_id>\d+))(([ ]+in)?([ ]+area)?([ ]+(?P<area>\w+)))?)|(?P<name>\w+)'
        match = re.match(exp, self.args.strip())
        message = 'Type "help goto" for help with this command.'
        if not match:
            self.user.update_output(message)
            return
        name, area_name, room_id = match.group('name', 'area', 'room_id')
        # They're trying to go to the same room as another user
        if name:
            # go to the same room that user is in
            per = self.world.get_user(name)
            if per:
                if per.location:
                    self.user.go(per.location, self.user.goto_appear, 
                                 self.user.goto_disappear)
                else:
                    self.user.update_output('You can\'t reach %s.\n' % per.fancy_name())
            else:
                self.user.update_output('That person doesn\'t exist.\n')
        # They're trying to go to a specific room
        elif room_id:
            # See if they specified an area -- if they did, go there
            if area_name:
                area = self.world.get_area(area_name)
                if not area:
                    self.user.update_output('Area "%s" doesn\'t exist.' % area_name)
                    return
            else:
                if not self.user.location:
                    self.user.update_output(message)
                    return
                area = self.user.location.area
            room = area.get_room(room_id)
            if room:
                self.user.go(room, self.user.goto_appear, 
                             self.user.goto_disappear)
            else:
                self.user.update_output('Room "%s" doesn\'t exist in area %s.' % (room_id, area.name))
        else:
            self.user.update_output(message)
    

command_list.register(Goto, ['goto'])
command_help.register(Goto.help, ['goto', 'go to'])

class Go(BaseCommand):
    """Go to the next room in the direction given."""
    def execute(self):
        if self.user.location:
            go_exit = self.user.location.exits.get(self.args)
            if go_exit:
                if go_exit.closed:
                    self.user.update_output('The door is closed.\n')
                else:
                    if go_exit.to_room:
                        if go_exit.linked_exit:
                            tell_new = '%s arrives from the %s.' % (self.user.fancy_name(),
                                                                    go_exit.linked_exit)
                        else:
                            tell_new = '%s suddenly appears in the room.' % self.user.fancy_name()
                        tell_old = '%s leaves to the %s.' % (self.user.fancy_name(),
                                                             go_exit.direction)
                        self.user.go(go_exit.to_room, tell_new, tell_old)
                    else:
                        # SOMETHING WENT BADLY WRONG IF WE GOT HERE!!!
                        # somehow the room that this exit pointed to got deleted without informing
                        # this exit.
                        self.log.critical('EXIT FAIL: Exit %s from room %s in area %s failed to resolve.' % (go_exit.direction, go_exit.room.id, go_exit.room.area.name))
                        # Delete this exit in the database and the room - we don't want it 
                        # popping up again
                        go_exit.destruct()
                        self.user.location.exits[go_exit.direction] = None
                        # Tell the user to ignore the man behind the curtain
                        self.user.location.tell_room('A disturbance was detected in the Matrix: Entity "%s exit" should not exist.\nThe anomaly has been repaired.\n' % self.args)
                        
            else:
                self.user.update_output('You can\'t go that way.\n')
        else:
            self.user.update_output('You exist in a void; there is nowhere to go.\n')
    

command_list.register(Go, ['go'])

class Say(BaseCommand):
    """Echo a message from the user to the room that user is in."""
    def execute(self):
        if self.args:
            if self.user.location:
                message = '%s says, "%s"' % (self.user.fancy_name(), self.args)
                message = say_color + message + clear_fcolor
                self.user.location.tell_room(message, teller=self.user)
            else:
                self.user.update_output('Your words are sucked into the void.\n')
        else:
            self.user.update_output('Say what?\n')
    

command_list.register(Say, ['say'])

class Load(BaseCommand):
    required_permissions = ADMIN | BUILDER | DM
    help = (
    """Load (Command)
Load a specific item or npc by id.  Npcs will be loaded into your room, 
and items will be loaded into your inventory. If you do not specify what area
the item should be loaded from, the item will be loaded from the area you are
currently located in, or the area you are currently editing (if you're editing
one).
\nRequired Permissions: ADMIN, BUILDER, DM
\nUSAGE:
To load an item:
  load item <item-id> [from area <area-name>]
To load an npc:
  load npc <npc-id> [from area <area-name>]
    """
    )
    def execute(self):
        if not self.args:
            self.user.update_output('What do you want to load?\n')
        else:
            help_message = 'Type "help load" for help on this command.\n'
            exp = r'(?P<obj_type>(item)|(npc))([ ]+(?P<obj_id>\d+))(([ ]+from)?([ ]+area)?([ ]+(?P<area_name>\w+)))?'
            match = re.match(exp, self.args, re.I)
            if match:
                obj_type, obj_id, area_name = match.group('obj_type', 'obj_id', 'area_name')
                if not obj_type or not obj_id:
                    self.user.update_output(help_message)
                else:
                    if not area_name and self.user.location:
                        getattr(self, 'load_' + obj_type)(obj_id, self.user.location.area)
                    elif not area_name and self.user.mode.edit_area:
                        getattr(self, 'load_' + obj_type)(obj_id, self.user.mode.edit_area)
                    elif area_name and self.world.area_exists(area_name):
                        getattr(self, 'load_' + obj_type)(obj_id, self.world.get_area(area_name))
                    else:
                        self.user.update_output('You need to specify an area to load from.\n')
            else:
                self.user.update_output(help_message)
    
    def load_npc(self, npc_id, npc_area):
        """Load an npc into the same room as the user."""
        if not self.user.location:
            self.user.update_output('But you\'re in a void!')
            return
        prototype = npc_area.get_npc(npc_id)
        if prototype:
            npc = prototype.load()
            npc.location = self.user.location
            self.user.location.npc_add(npc)
            self.user.update_output('You summon %s into the world.\n' % npc.name)
            if self.alias == 'spawn':
                self.user.location.tell_room('%s summons %s.' % (self.user.fancy_name(), npc.name), 
                                             [self.user.name], self.user)
        else:
            self.user.update_output('That npc doesn\'t exist.')
    
    def load_item(self, item_id, item_area):
        """Load an item into the user's inventory."""
        prototype = item_area.get_item(item_id)
        if prototype:
            item = prototype.load()
            self.user.item_add(item)
            self.user.update_output('You summon %s into the world.\n' % item.name)
            if self.user.location and (self.alias == 'spawn'):
                self.user.location.tell_room('%s summons %s into the world.' % (self.user.fancy_name(), item.name), 
                                                                                [self.user.name], self.user)
        else:
            self.user.update_output('That item doesn\'t exist.\n')
    

command_list.register(Load, ['load', 'spawn'])
command_help.register(Load.help, ['load', 'spawn'])

class Inventory(BaseCommand):
    """Show the user their inventory."""
    def execute(self):
        if not self.user.inventory:
            self.user.update_output('Your inventory is empty.\n')
        else:
            i = 'Your inventory consists of:\n'
            for item in self.user.inventory:
                if item not in self.user.isequipped:
                    i += item.name + '\n'
            self.user.update_output(i)

command_list.register(Inventory, ['i', 'inventory'])

class Give(BaseCommand):
    """Give an item to another player or npc."""
    help = (
    """Give (Command)
Give an object to another player or an npc.
\nUSAGE:
give <item-keyword> to <npc/player-name>
    """
    )
    def execute(self):
        exp = r'(?P<thing>.*?)([ ]to[ ])(?P<givee>\w+)'
        match = re.match(exp, self.args, re.I)
        if not match:
            self.user.update_output('Type "help give" for help on this command.\n')
        elif not self.user.location:
            self.user.update_output('You are alone in the void; there\'s no one to give anything to.\n')
        else:
            thing, person = match.group('thing', 'givee')
            givee = self.user.location.get_user(person)
            if not givee:
                givee = self.user.location.get_npc_by_kw(person)
                if not givee:
                    self.user.update_output('%s isn\'t here.' % person.capitalize())
                    return
            item = self.user.check_inv_for_keyword(thing)
            if not item:
                self.user.update_output('You don\'t have %s.' % thing)
            else:
                self.user.item_remove(item)
                givee.item_add(item)
                self.user.update_output('You give %s to %s.' % (item.name, givee.fancy_name()))
                givee.update_output('%s gives you %s.' % (self.user.fancy_name(), item.name))
                self.user.location.tell_room('%s gives %s to %s.' % (self.user.fancy_name(),
                                                                      item.name,
                                                                      givee.fancy_name()),
                                            [self.user.name, givee.name])
                if givee.is_npc():
                    givee.notify('given_item', {'giver': self.user, 
                                                'item': item})
    

command_list.register(Give, ['give'])
command_help.register(Give.help, ['give'])

class Drop(BaseCommand):
    """Drop an item from the user's inventory into the user's current room."""
    def execute(self):
        if not self.args:
            self.user.update_output('What do you want to drop?\n')
        else:
            item = self.user.check_inv_for_keyword(self.args)
            if item:
                self.user.item_remove(item)
                self.user.update_output('You drop %s.\n' % item.name)
                if self.user.location:
                    self.user.location.item_add(item)
                    self.user.location.tell_room('%s drops %s.\n' % (self.user.fancy_name(), 
                                                                     item.name), [self.user.name])
                else:
                    self.user.update_output('%s disappears into the void.\n' % item.name)
                    item.destruct()
            else:
                self.user.update_output('You don\'t have that.\n')
    

command_list.register(Drop, ['drop'])

class Get(BaseCommand):
    """Get an item and store it in the user's inventory."""
    help = (
    """Get (Command)
The Get command is used to transfer an item from the room into your inventory,
or from a containing item into your inventory. 
\nUSAGE:
To get an item you see in a room:
  get <item-keyword>
To get an item from a container (the container can exist in the room, or
can be in your inventory):
  get <item-keyword> from <container-item-keyword>
\nEXAMPLES:
Let's say you see a loot bag sitting in your room. You could take it by typing:
  get loot bag
Let's say you were to look at the loot bag (using the Look command) and see
that it contained a golden ring. You could transfer that ring from the loot
bag into your inventory by typing:
  get ring from loot bag
You could have also gotten the ring out of the loot bag, using the same method
just mentioned, even if you hadn't gotten the loot bag from the room first
(i.e, you don't have to get the loot bag before you can take the ring from
it).
\nNOTE: Containers must be open before you can see anything inside them, or
take anything out of them. For help with opening containers, see "help open".
    """
    )
    def execute(self):
        if not self.args:
            self.user.update_output('What do you want to get?\n')
            return
        exp = r'((?P<target_kw>(\w|[ ])+)([ ]+from)([ ]+(?P<source_kw>(\w|[ ])+)))|((?P<item_kw>(\w|[ ])+))'
        match = re.match(exp, self.args, re.I)
        if not match:
            self.user.update_output('Type "help get" for help with this command.')
            return
        target_kw, source_kw, item_kw = match.group('target_kw', 'source_kw', 
                                                    'item_kw')
        if source_kw:
            message = self.get_item_from_container(source_kw, target_kw)
        else:
            message = self.get_item_from_room(item_kw)
        self.user.update_output(message)
    
    def get_item_from_container(self, source_kw, target_kw):
        c_item = self.user.location.check_for_keyword(source_kw) or \
                    self.user.check_inv_for_keyword(source_kw)
        if not c_item:
            return '"%s" doesn\'t exist.' % source_kw
        if not c_item.is_container():
            return 'That\'s not a container.'
        container = c_item.item_types.get('container')
        if container.closed:
            return '%s is closed.' % c_item.name.capitalize()
        item = container.get_item_by_kw(target_kw)
        if not item:
            return '%s doesn\'t exist.' % target_kw.capitalize()
        if item.carryable or (self.user.permissions & GOD):
            container.item_remove(item)
            self.user.item_add(item)
            if self.user.location:
                room_tell = '%s gets %s from %s.\n' % (self.user.fancy_name(),
                                                       item.name, c_item.name)
                self.user.location.tell_room(room_tell, [self.user.name])
            return 'You get %s.' % item.name
        else:
            return 'You can\'t take that.'
    
    def get_item_from_room(self, item_kw):
        if not self.user.location:
            return 'Only cold blackness exists in the void. ' +\
                   'It\'s not the sort of thing you can take.'
        item = self.user.location.get_item_by_kw(item_kw)
        if not item:
            return '%s doesn\'t exist.' % item_kw
        if item.carryable or (self.user.permissions & GOD):
            self.user.location.item_remove(item)
            self.user.item_add(item)
            room_tell = '%s gets %s.' % (self.user.fancy_name(), item.name)
            self.user.location.tell_room(room_tell, [self.user.name])
            return 'You get %s.' % item.name
        else:
            return 'You can\'t take that.'
    

command_list.register(Get, ['get', 'take'])
command_help.register(Get.help, ['get', 'take'])

class Put(BaseCommand):
    """Put an object inside a container."""
    help = (
    """Put (Command)
\nThe put command allows you to put an item inside a container. If you are
just looking to get rid of an inventory item or leave an item in a room, try
the Drop command.
\nUSAGE:
To put an item inside a container:
  put <item> in <container>
\nThe preposition (the word "in") is required, but can also be replaced with
"inside" or "on". To get an item out of a container, see "help get".
    """
    )
    def execute(self):
        if not self.args:
            self.user.update_output('Put what where?')
            return
        exp = r'(?P<target_kw>(\w|[ ])+)([ ]+(?P<prep>(in)|(inside)|(on)))(?P<container>(\w|[ ])+)'
        match = re.match(exp, self.args.lower().strip())
        if not match:
            self.user.update_output('Type "help put" for help with this command.')
            return
        target_kw, preposition, cont_kw = match.group('target_kw', 
                                                      'prep', 
                                                      'container')
        target = self.user.check_inv_for_keyword(target_kw)
        if not target:
            self.user.update_output('You don\'t have "%s".' % target_kw)
            return
        container = self.user.check_inv_for_keyword(cont_kw)
        if not container:
            if self.user.location:
                container = self.user.location.get_item_by_kw(cont_kw)
                if not container:
                    self.user.update_output('%s isn\'t here.' % cont_kw)
                    return
        # We should have a container by now!
        if not container.is_container():
            self.user.update_output('%s is not a container.' % 
                                    container.name.capitalize())
            return
        if container.item_types['container'].item_add(target):
            self.user.update_output('You put %s %s %s.' % (target.name,
                                                           preposition,
                                                           container.name))
            if self.user.location:
                tr = '%s puts %s %s %s.' % (self.user.fancy_name(), 
                                            target.name, preposition,
                                            container.name)
        else:
            self.user.update_output('%s won\'t fit %s %s.' % (target.name.capitalize(),
                                                              preposition,
                                                              container.name))
    

command_list.register(Put, ['put'])
command_help.register(Put.help, ['put'])

class Equip(BaseCommand):
    """Equip an item from the user's inventory."""
    def execute(self):
        message = ''
        if not self.args:
            #Note: Does not output slot types in any order.
            message = 'Equipped items:'
            for i, j in self.user.equipped.iteritems():
                message += '\n' + i + ': '
                if j:
                    message += j.name
                else:
                    message += 'None.'
            message += '\n'
        else:
            item = self.user.check_inv_for_keyword(self.args)
            if not item:
                message = 'You don\'t have it.\n'
            elif self.user.equipped.get(item.equip_slot, None) == None: #if item has a slot that exists.
                message = 'You can\'t equip that!\n'
            else:
                if self.user.equipped[item.equip_slot]: #if slot not empty
                    self.user.isequipped.remove(item)   #remove item in slot
                self.user.equipped[item.equip_slot] = item
                self.user.isequipped += [item]
                message = SLOT_TYPES[item.equip_slot].replace('#item', item.name) + '\n'
        self.user.update_output(message)  
    

command_list.register(Equip, ['equip'])

class Unequip(BaseCommand):
    """Unequip items."""
    def execute(self):
        item = self.user.check_inv_for_keyword(self.args)
        message = ''
        if not self.args:
            message = 'What do you want to unequip?\n'
        elif not item: 
            message = 'You don\'t have that!\n'
        elif not self.user.equipped[item.equip_slot]:
            message = 'You aren\'t using anything in that slot.\n'
        else:
            self.user.equipped[item.equip_slot] = ''
            self.user.isequipped.remove(item)
            message = 'You remove ' + item.name + '.\n'
        self.user.update_output(message)
            

command_list.register(Unequip, ['unequip'])

class Who(BaseCommand):
    """Return a list of names comprised of users who are currently playing the game."""
    help = (
    """Who (Command)
The Who command returns a list of all the players currently in the game.
\nUSAGE:
  who
    """
    )
    def execute(self):
        persons = [per for per in self.world.user_list.values() if isinstance(per.name, str)]
        message = 'Currently Online'.center(50, '-') + '\n'
        for per in persons:
            if per.permissions > PLAYER:
                # We want to list the permissions of the people who have perms
                # higher than player so other players know where they can go
                # for help
                perm_list = get_permission_names(per.permissions)
                # Everyone's a player -- don't bother listing that one
                if 'Player' in perm_list:
                    perm_list.remove('Player')
                # God trumps everything else...
                if 'God' in perm_list:
                    perms = 'God'
                else:
                    perms = ', '.join(perm_list)
                message += '%s (%s) - %s\n' % (per.fancy_name(), perms, per.title)
            else:
                message += '%s - %s\n' % (per.fancy_name(), per.title)
        message += '-'.center(50, '-')
        self.user.update_output(message)
    

command_list.register(Who, ['who'])
command_help.register(Who.help, ['who'])

class Enter(BaseCommand):
    """Enter a portal."""
    def execute(self):
        if not self.args:
            self.user.update_output('Enter what?\n')
        # elif not self.user.location:
        #     self.user.update_output('You are in a void, there is nowhere to go.\n')
        else:
            if self.user.location:
                # Check the room for the portal object first
                obj = self.user.location.get_item_by_kw(self.args)
                if obj:
                    if 'portal' in obj.item_types:
                        self.go_portal(obj.item_types['portal'])
                    else:
                        self.user.update_output('That\'s not a portal...\n')
            else:
                # If the portal isn't in the room, check their inventory
                obj = self.user.check_inv_for_keyword(self.args)
                if obj:
                    if 'portal' in obj.item_types:
                        # If the portal is in their inventory, make them drop it first
                        # (a portal can't go through itself)
                        Drop(self.user, self.args, 'drop').execute()
                        self.go_portal(obj.item_types['portal'])
                    else:
                        self.user.update_output('That\'s not a portal...\n')
                else:
                    # We've struck out an all counts -- the user doesn't have a portal
                    self.user.update_output('You don\'t see that here.\n')
    
    def go_portal(self, portal):
        """Go through a portal."""
        if portal.location:
            if self.user.location: 
                self.user.location.tell_room(self.personalize(portal.leave_message, self.user), 
                                             [self.user.name])
            self.user.update_output(self.personalize(portal.entrance_message, self.user))
            self.user.go(portal.location)
            self.user.location.tell_room(self.personalize(portal.emerge_message, self.user), 
                                         [self.user.name])
        else:
            self.user.update_output('Nothing happened. It must be a dud.\n')

command_list.register(Enter, ['enter'])

class Purge(BaseCommand):
    """Purge all of the items and npc's in the room."""
    required_permissions = BUILDER | DM | ADMIN
    help = (
    """Purge (Command)
Purge will destroy all items and npcs in your room or in your inventory. Purge
cannot, however, destroy players or prototype items/npcs (see "help
prototypes" if this is confusing).
USAGE:
Calling purge without any options will purge the room by default.
To purge your inventory:
  purge inventory/i
    """
    )
    def execute(self):
        if not self.args:
            # If they specified nothing, just purge the room
            if self.user.location:
                self.user.location.purge_room()
                self.user.update_output('The room has been purged.\n')
            else:
                self.user.update_output('You\'re in a void, there\'s nothing to purge.\n')
        elif self.args in ['i', 'inventory']:
            # Purge their inventory!
            for i in range(len(self.user.inventory)):
                item = self.user.inventory[0]
                self.user.item_remove(item)
                item.destruct()
            self.user.update_output('Your inventory has been purged.\n')
        else:
            # Purge a specific npc or item based on keyword
            self.user.update_output('Someone didn\'t endow me with the functionality to purge that for you.\n')
    

command_list.register(Purge, ['purge'])
command_help.register(Purge.help, ['purge'])

class Areas(BaseCommand):
    help = (
    """Areas (Command)
The Areas command gives a list of all the areas in the game along with a
suggested level range.
    """
    )
    def execute(self):
        """Give a list of areas in the world, as well as their level ranges."""
        the_areas = ['%s (level range: %s) ' % (area.title, area.level_range) \
                     for area in self.world.areas.values()]
        message = ' Areas '.center(50, '-') + '\n'
        if not the_areas:
            message += 'Sorry, God has taken a day off. There are no areas yet.'
        else:
            message += '\n'.join(the_areas)
        message += '\n' + ('-' * 50)
        self.user.update_output(message)
    

command_list.register(Areas, ['areas'])
command_help.register(Areas.help, ['areas'])

class Emote(BaseCommand):
    """Emote to another player or ones self. (slap them, cry hysterically, etc.)"""
    help = (
    """Emote (Command)
\nThe emote command allows your character express actions in the third person.
There are also many pre-defined emotes. For a list of actions you can type to
initiate a pre-defined emote, see "help emote list".
\nUSAGE:
To express a custom emote:
  emote <emote-text>
To use a predefined emote:
  <emote-action> [<target-player-name>]
\nEXAMPLES:
If Bob wished to express his severe doubt at Steven's battle plans with
actions instead of words, he could type:
  emote facepalms at Steven's epic ineptitude.
Anyone in the same room would then see the following:
  Bob facepalms at Steven's epic ineptitude.
    """
    )
    elist = "The following is the list of emote actions: \n" +\
            '\n'.join(EMOTES.keys())
    aliases = ['emote']
    aliases.extend(EMOTES.keys())
    def execute(self):
        if not self.user.location:
            self.user.update_output('You try, but the action gets sucked into the void. The void apologizes.\n')
        elif self.alias == 'emote':
            self.user.location.tell_room('%s %s' % (self.user.fancy_name(),
                                                    self.args), 
                                         teller=self.user)
        else:
            emote_list = EMOTES[self.alias]
            # The person didn't specify a target -- they want to do the emote
            # action by themself
            if not self.args:
                self.single_person_emote(emote_list)
            # If this emote doesn't have an option for a double emote,
            # just ignore the args and do a single-person emote
            elif self.args and not emote_list[1]:
                self.single_person_emote(emote_list)
            else:
                victim = self.user.location.get_user(self.args.lower()) or\
                         self.user.location.get_npc_by_kw(self.args.lower()) or\
                         self.world.get_user(self.args.lower())
                if not victim:
                    # victim = self.world.get_user(self.args.lower())
                    # if not victim:                        
                    self.user.update_output('%s isn\'t here.' % 
                                            self.args.capitalize())
                elif victim == self.user:
                    self.single_person_emote(emote_list)
                else:
                    self.double_person_emote(emote_list, victim)
    
    def single_person_emote(self, emote_list):
        """A player wishes to emote an action alone."""
        actor_m = self.personalize(emote_list[0][0], self.user)
        room_m = self.personalize(emote_list[0][1], self.user)
        self.user.update_output(actor_m)
        self.user.location.tell_room(room_m, [self.user.name])
    
    def double_person_emote(self, emote_list, victim):
        """A player wishes to emote an action on a target."""
        # We got this far, we know the victim exists in the world
        actor = self.personalize(emote_list[1][0], self.user, victim)
        victimm = self.personalize(emote_list[1][1], self.user, victim)
        if victim.location == self.user.location:
            room_m = self.personalize(emote_list[1][2], self.user, victim)
            self.user.update_output(actor)
            victim.update_output(victimm)
            self.user.location.tell_room(room_m, [self.user.name, victim.name])
        else:
            self.user.update_output('From far away, ' + actor)
            victim.update_output('From far away, ' + victimm)
        if victim.is_npc():
            victim.notify('emoted', {'emote': self.alias, 'emoter': self.user})
    

command_list.register(Emote, Emote.aliases)
command_help.register(Emote.help, ['emote', 'emotes'])
command_help.register(Emote.elist, ['emote list'])

class Bestow(BaseCommand):
    """Bestow a new class of permissions on a PC."""
    required_permissions = GOD
    help = (
    """Bestow (Command)
Bestow allows you to extend a player's permissions by giving them another
permission group.
\nRequired Permissions: GOD
\nUSAGE:
  bestow <permission-group> [upon] <player-name>
\nPermission Groups:
  player
  dm
  admin
  god
\nTo revoke permissions, see "help revoke". For more information on
permissions and permission groups, see "help permissions".
    """
    )
    def execute(self):
        if not self.args:
            self.user.update_output('Bestow what authority upon whom?\n')
            return
        exp = r'(?P<permission>(god)|(dm)|(builder)|(admin))[ ]?(to)?(on)?(upon)?([ ]+(?P<player>\w+))'
        match = re.match(exp, self.args.lower(), re.I)
        if not match:
            self.user.update_output('Type "help bestow" for help on this command.\n')
            return
        perm, player = match.group('permission', 'player')
        user = self.world.get_user(player)
        permission = globals().get(perm.upper())
        if not user:
            self.user.update_output('That player isn\'t on right now.\n')
            return
        if not permission:
            self.user.update_output('Valid permission types are: god, dm, builder, and admin.\n')
            return
        if user.permissions & permission:
            self.user.update_output('%s already has that authority.\n' % user.fancy_name())
            return
        user.permissions = user.permissions | permission
        self.user.update_output('%s now has the privilige of being %s.\n' % (user.fancy_name(), perm.upper()))
        user.update_output('%s has bestowed the authority of %s upon you!' % (self.user.fancy_name(), perm.upper()))
        self.world.tell_users('%s has bestowed the authority of %s upon %s!' %
                              (self.user.fancy_name(), perm.upper(), user.fancy_name()),
                              [self.user.name, user.name])
    

command_list.register(Bestow, ['bestow'])
command_help.register(Bestow.help, ['bestow'])

class Revoke(BaseCommand):
    """Revoke permission privilges for a PC."""
    required_permissions = GOD
    def execute(self):
        if not self.args:
            self.user.update_output('Revoke whose authority over what?\n')
            return
        exp = r'(?P<permission>(god)|(dm)|(builder)|(admin))[ ]?(on)?(for)?([ ]+(?P<player>\w+))'
        match = re.match(exp, self.args.lower(), re.I)
        if not match:
            self.user.update_output('Type "help revoke" for help on this command.\n')
            return
        perm, player = match.group('permission', 'player')
        user = self.world.get_user(player)
        permission = globals().get(perm.upper())
        if not user:
            self.user.update_output('That player isn\'t on right now.\n')
            return
        if not permission:
            self.user.update_output('Valid permission types are: god, dm, builder, and admin.\n')
            return
        if not (user.permissions & permission):
            self.user.update_output('%s doesn\'t have that authority anyway.\n' % user.fancy_name())
            return
        user.permissions = user.permissions ^ permission
        self.user.update_output('%s has had the privilige of %s revoked.\n' % (user.fancy_name(), perm))
        user.update_output('%s has revoked your %s priviliges.\n' % (self.user.fancy_name(), perm))
    

command_list.register(Revoke, ['revoke'])
command_help.register(Revoke.help, ['revoke'])

class Reset(BaseCommand):
    """The command for resetting a room or area."""
    required_permissions = DM | BUILDER | ADMIN
    help = ("Reset (command)\n"
    """The reset command is used to force a room to respawn all of the items 
and npcs on its reset list. If you call reset on an entire area, all of the
rooms in that area will be told to reset.\n
USAGE:
To reset the room you are in, just call reset without any options. If you need
to reset a room without being inside it (or you want to reset a whole area),
use one of the following:
To reset a room:
    reset [room] <room-id> [in area] <area-name>
To reset an area:
    reset [area] <area-name>\n
Permissions:
This command requires DM, BUILDER, or ADMIN permissions.\n
Adding Resets to Rooms
For help on adding items and npcs to a room's reset list, 
see "help room resets".""")
    
    def execute(self):
        if not self.args:
            # Reset the room the user is in
            if self.user.location:
                self.user.location.reset()
                self.user.update_output('Room %s has been reset.\n' % self.user.location.id)
            else:
                self.user.update_output('That\'s a pretty useless thing to do in the void.\n')
        else:
            exp = r'(room[ ]+(?P<room_id>\d+)([ ]+in)?([ ]+area)?([ ]+(?P<room_area>\w+))?)|(area[ ]+(?P<area>\w+))'
            match = re.match(exp, self.args, re.I)
            if not match:
                self.user.update_output('Type "help resets" to get help with this command.\n')
                return
            room_id, room_area, area = match.group('room_id', 'room_area', 'area')
            if area:
                # reset an entire area
                reset_area = self.world.get_area(area)
                if reset_area:
                    reset_area.reset()
                    self.user.update_output('Area %s has been reset.\n' % reset_area.name)
                    return
                else:
                    self.user.update_output('That area doesn\'t exist.\n')
                    return
            # Reset a single room
            if room_area:
                area = self.world.get_area(room_area)
                if not area:
                    self.user.update_output('That area doesn\'t exist.\n')
                    return
            else:
                if self.user.location:
                    area = self.user.location.area
                else:
                    self.user.update_output('Type "help resets" to get help with this command.\n')
                    return
            room = area.get_room(room_id)
            if not room:
                self.user.update_output('Room %s doesn\'t exist in area %s.\n' % (room_id, 
                                                                                  area.name))
            room.reset()
            self.user.update_output('Room %s in area %s has been reset.\n' % (room.id, area.name))
    

command_list.register(Reset, ['reset'])
command_help.register(Reset.help, ['reset', 'resets'])

class Help(BaseCommand):
    help = ("Try 'help <command-name>' for help with a command.\n"
            "For example, 'help go' will give details about the go command."
    )
    def execute(self):
        # get the help parameter and see if it matches a command_help alias
        #     if so, send user the help string
        #     return
        # else, look up in database
        #     if there is a match, send the help string to the user
        #     return
        # else, send "I can't help you with that" string to user
        # return
        if not self.args:
            self.user.update_output(self.help)
            return
        help = command_help[self.args]
        if help:
            # This should probably be replaced with a better color parsing
            # function when we decide to have better use of colors
            help = help.replace('<b>', BOLD)
            help = help.replace('<title>', help_title).replace('</title>',
                                                               CLEAR + '\n')
            help = re.sub(r'</\w+>', CLEAR, help)
            self.user.update_output(help)
        else:
            self.user.update_output("Sorry, I can't help you with that.\n")
    

command_list.register(Help, ['help', 'explain', 'describe'])
command_help.register(Help.help, ['help', 'explain', 'describe'])

class Clear(BaseCommand):
    """Clear the user's screen and give them a new prompt."""
    help = (
    """Clear (command)
Clears your screen of text and gives you a new prompt.
    """
    )
    def execute(self):
        # First send the ANSI command to clear the entire screen, then
        # send the ANSI command to move the cursor to the "home" position 
        # (the upper left position in the terminal)
        self.user.update_output('\x1b[2J' + '\x1b[H')
    

command_list.register(Clear, ['clear'])
command_help.register(Clear.help, ['clear'])

class Set(BaseCommand):
    """Set a (settable) player attribute."""
    help = (
    """Set (Command)
The Set command allows you to set details and options about your character.
\nUSAGE:
set <option> <argument>
Options you can set:
  email - your e-mail address
  title - the title of your character
  description - your character's description
    """
    )
    def execute(self):
        if not self.args:
            self.user.update_output('What do you want to set?\n')
        else:
            match = re.match(r'\s*(\w+)([ ](.+))?$', self.args, re.I)
            if not match:
                message = 'Type "help set" for help with this command.\n'
            else:
                func, _, arg = match.groups()
                message = 'You can\'t set that.\n'
                if hasattr(self.user, 'set_' + func):
                    message = (getattr(self.user, 'set_' + func)(arg))
                self.user.update_output(message)
    

command_list.register(Set, ['set', 'cset'])
command_help.register(Set.help, ['set'])

class ToggleOpen(BaseCommand):
    """Open/Close doors and containers."""
    help = (
    """Open, Close (Command)
The open and close commands can be used to open/close doors or containers.
\nUSAGE:
To open a door:
  open <door-direction> [door]
To open a container:
  open <container-keyword>
To close a door or container, use the same syntax as above, but replace "open"
with "close."
    """
    )
    def execute(self):
        if not self.args:
            self.user.update_output('Open what?')
            return
        exp = r'(?P<dir>(north)|(south)|(east)|(west))|(?P<kw>(\w|[ ])+)'
        match = re.match(exp, self.args.lower(), re.I)
        if not match:
            self.user.update_output('Type "help open" for help with this command.')
            return
        direction, kw = match.group('dir', 'kw')
        if direction:
            message = self.toggle_door(direction, self.alias)
        elif kw:
            message = self.toggle_container(kw, self.alias)
        self.user.update_output(message)
    
    def toggle_door(self, direction, toggle):
        if not self.user.location:
            return 'There aren\'t any doors in the void.'
        exit = self.user.location.exits.get(direction)
        if not exit:
            return 'There isn\'t a door there.'
        if toggle == 'open':
            return exit.open_me(self.user.fancy_name())
        else:
            return exit.close_me(self.user.fancy_name())
    
    def toggle_container(self, kw, toggle):
        obj = self.user.check_inv_for_keyword(kw)
        # if nothing in inventory, check room
        if not obj:
            obj = self.user.location.get_item_by_kw(kw)
            if not obj:
                return 'You don\'t see that here.'
        if not obj.is_container():
            return 'That\'s not a container.'
        container = obj.item_types.get('container')
        if toggle == 'close':
            if not container.openable:
                return '%s defies your attempts to close it.' % obj.name.capitalize()
            if container.closed:
                return 'It\'s already closed.'
            container.closed = True
            return 'You close %s.' % obj.name
        else:
            if not container.openable:
                return '%s defies your attempts to open it.' % obj.name.capitalize()
            if not container.closed:
                return 'It\'s already open.'
            container.closed = False
            return 'You open %s.' % obj.name
    

command_list.register(ToggleOpen, ['open', 'close'])
command_help.register(ToggleOpen.help, ['open', 'close'])

class Version(BaseCommand):
    """Display the credits and the version of ShinyMUD currently running."""
    help = (
    """** ShinyMUD, version %s **
\nDeveloped by (and copyright):
  Jess Coulter (Surrey) 
  Patrick Murphy (Murph)
  Nickolaus Saint (Nick)""" % VERSION
    )
    
    def execute(self):
        self.user.update_output(self.help)
    

command_list.register(Version, ['version', 'credit', 'credits'])
command_help.register(Version.help, ['version', 'credit', 'credits'])

class Sit(BaseCommand):
    """Change the player's position to sitting."""
    def execute(self):
        if self.user.position[0].find(self.alias) != -1:
            self.user.update_output('You are already sitting.')
            return
        if not self.args:
            if self.user.position[0] == 'sleeping':
                self.user.update_output('You wake and sit up.')
                if self.user.location:
                    self.user.location.tell_room('%s wakes and sits up.' % self.user.fancy_name(), [self.user.name], self.user)
                self.user.change_position('sitting', self.user.position[1])
            else:
                self.user.update_output('You sit down.')
                if self.user.location:
                    self.user.location.tell_room('%s sits down.' % self.user.fancy_name(), [self.user.name], self.user)
                self.user.change_position = ('sitting')
        else:
            if not self.user.location:
                self.user.update_output('The void is bereft of anything to sit on.')
                return
            exp = r'((on)|(in))?([ ]?)?(?P<furn>(\w|[ ])+)'
            furn_kw = re.match(exp, self.args.lower().strip()).group('furn')
            furn = self.user.location.get_item_by_kw(furn_kw)
            if not furn:
                self.user.update_output('You don\'t see that here.')
                return
            f_obj = furn.item_types.get('furniture')
            if not f_obj:
                self.user.update_output('That\'s not a type of furniture.')
                return
            if not f_obj.user_add(self.user):
                self.user.update_output('It\'s full right now.')
                return
            else:
                if self.user.position[1]:
                    self.user.position[1].item_types['furniture'].user_remove(self.user)
                f_obj.user_add(self.user)
                self.user.position = ('sitting', furn)
                self.user.update_output('You sit down on %s.' % furn.name)
                self.user.location.tell_room('%s sits down on %s.' % (self.user.fancy_name(), furn.name), 
                                             [self.user.name], self.user)
    

command_list.register(Sit, ['sit'])
command_help.register(Sit.help, ['sit'])

class Stand(BaseCommand):
    """Change the player's position to standing."""
    def execute(self):
        if self.user.position[0].find(self.alias) != -1:
            self.user.update_output('You are already standing.')
            return
        if self.user.position[0] == 'sleeping':
            self.user.update_output('You wake and stand up.')
            if self.user.location:
                self.user.location.tell_room('%s wakes and stands up.' % self.user.fancy_name(), [self.user.name], self.user)
        else:
            self.user.update_output('You stand up.')
            if self.user.location:
                self.user.location.tell_room('%s stands up.' % self.user.fancy_name(), [self.user.name], self.user)
        self.user.change_position('standing')
    

command_list.register(Stand, ['stand'])
command_help.register(Stand.help, ['stand'])

class Sleep(BaseCommand):
    """Change the player's position to sleeping."""
    def execute(self):
        if self.user.position[0].find(self.alias) != -1:
            self.user.update_output('You are already sleeping.')
            return
        
        if not self.args:
            self.user.update_output('You go to sleep.')
            if self.user.location:
                self.user.location.tell_room('%s goes to sleep.' % self.user.fancy_name(), [self.user.name], self.user)
            # If they were previously sitting on furniture before they went to
            # sleep, we might as well maintain their position on that 
            # furniture when they go to sleep
            self.user.change_position('sleeping', self.user.position[1])
        else:
            if not self.user.location:
                self.user.update_output('The void is bereft of anything to sleep on.')
                return
            exp = r'((on)|(in))?([ ]?)?(?P<furn>(\w|[ ])+)'
            furn_kw = re.match(exp, self.args.lower().strip()).group('furn')
            furn = self.user.location.get_item_by_kw(furn_kw)
            if not furn:
                self.user.update_output('You don\'t see that here.')
                return
            f_obj = furn.item_types.get('furniture')
            if not f_obj:
                self.user.update_output('That\'s not a type of furniture.')
                return
            if not f_obj.user_add(self.user):
                self.user.update_output('It\'s full right now.')
                return
            else:
                self.user.change_position('sleeping', furn)
                self.user.update_output('You go to sleep on %s.' % furn.name)
                self.user.location.tell_room('%s goes to sleep on %s.' % (self.user.fancy_name(), furn.name), 
                                             [self.user.name], self.user)
    

command_list.register(Sleep, ['sleep'])
command_help.register(Sleep.help, ['sleep'])

class Wake(BaseCommand):
    """Change a player's status from sleeping to awake (and standing)."""
    def execute(self):
        if not self.args:
            # Wake up yourself
            if self.user.position[0] != 'sleeping':
                self.user.update_output('You are already awake.')
                return
            self.user.update_output('You wake and stand up.')
            if self.user.location:
                self.user.location.tell_room('%s wakes and stands up.' % self.user.fancy_name(), [self.user.name], self.user)
            self.user.change_position('standing')
        else:
            # Wake up someone else!
            if not self.user.location:
                self.user.update_output('You are alone in the void.')
                return
            sleeper = self.user.location.get_user(self.args.lower().strip())
            if not sleeper:
                self.user.update_output('That person isn\'t here.')
                return
            if sleeper.position[0] != 'sleeping':
                self.user.update_output('%s isn\'t asleep.' % sleeper.fancy_name())
                return
            sleeper.change_position('standing')
            self.user.update_output('You wake up %s.' % sleeper.fancy_name())
            sleeper.update_output('%s wakes you up.' % self.user.fancy_name())
            troom = '%s wakes up %s.' % (self.user.fancy_name(),
                                         sleeper.fancy_name())
            self.user.location.tell_room(troom, [self.user.name, sleeper.name],
                                         self.user)
    

command_list.register(Wake, ['wake', 'awake'])
command_help.register(Wake.help, ['wake'])

class Award(BaseCommand):
    """Award an item to a user."""
    required_permissions = required_permissions = DM | ADMIN
    help = (
    """Award (Command)
\nThe Award command allows a DM or an Admin to award an item to a player. Note
that you must have the item you wish to award in your inventory for the Award
command to work, and you must also be in the same room as the person you wish
to award the item to.
\nRequired Permissions: ADMIN, DM
\nUSAGE:
To award an item to a player:
  award <item-keyword> to <player-name> ['<actor-message>':'<room-message>']
\nThe actor-message is the message you want the player to see upon receipt of
your item. The room-message is the message you want everyone else in the same
room to hear upon the player's receipt of the item. Neither message is
required, and if they are not given then the item will be awarded to the
player silently.
\nEXAMPLES:
Say for example that you would like to award the player Jameson a medal to
celebrate the quest he just completed. First you would make sure the medal was
in your inventory (easily done by using the Load command). Then you would type
the following (which would normally be on one line -- in this case it is 
linewrapped for readibility):
  award medal to jameson 'You receive a medal for your fine work.':
  '#actor receives a medal for his fine work.'
\nJameson would have the medal added to his inventory and receive the message
"You receive a medal for your fine work." Anyone else in the room would see
the message "Jameson receives a medal for his fine work."
    """
    )
    def execute(self):
        if not self.args:
            self.user.update_output('Award what to whom?')
            return
        exp = r'(?P<item>(\w+|[ ])+)([ ]+to)([ ]+(?P<user>\w+))([ ]+(?P<actor>\'(.*?)\')(:(?P<room>\'(.*?)\'))?)?'
        match = re.match(exp, self.args, re.I)
        if not match:
            self.user.update_output('Type "help award" for help with this command.')
            return
        item_kw, user_kw, actor, room = match.group('item', 'user', 'actor', 'room')
        user = self.user.location.get_user(user_kw.lower())
        if not user:
            self.user.update_output('Whom do you want to award %s to?' % item_kw)
            return
        item = self.user.check_inv_for_keyword(item_kw)
        if not item:
            self.user.update_output('You don\'t have any %s.' % item_kw)
            return
        self.user.item_remove(item)
        user.item_add(item)
        self.user.update_output('%s has been awarded %s.' % (user.fancy_name(),
                                                             item.name))
        if actor:
            message = self.personalize(actor.strip("\'"), self.user)
            user.update_output(message)
        if room:
            message = self.personalize(room.strip("\'"), self.user, user)
            self.user.location.tell_room(message, [user.name], self.user)
    

command_list.register(Award, ['award'])
command_help.register(Award.help, ['award'])

class Consume(BaseCommand):
    """Consume a food or drink item."""
    help = (
    """Eat, Drink, Use (Command)
\nThe commands Eat, Drink, and Use can all be used interchangeably to consume
an edible food or drink item. Be careful what you eat or drink though;
consuming some items may cause undesirable effects, such as poisoning or
drunkeness.
\nUSAGE:
To consume an edible item:
  eat <item-keyword>
    """
    )
    def execute(self):
        if not self.args:
            self.user.update_output("%s what?" % self.alias.capitalize())
            return
        food = self.user.check_inv_for_keyword(self.args.lower().strip())
        if not food:
            self.user.update_output('You don\'t have any %s.' % self.args)
            return
        food_obj = food.item_types.get('food')
        if not food_obj:
            # Gods have a more robust digestive system -- they can afford to
            # eat objects that aren't edible to mere mortals
            if self.user.permissions & GOD:
                self.user.item_remove(food)
                food.destruct()
                self.user.update_output('You eat %s.' % food.name)
                if self.user.location:
                    self.user.location.tell_room('%s ate %s.' %\
                                                 (self.user.fancy_name(),
                                                  food.name),
                                                [self.user.name], self.user)
                return
            else:
                self.user.update_output('That\'s not edible!')
                return
        # Remove the food object
        self.log.debug(food_obj)
        self.user.item_remove(food)
        food.destruct()
        # Replace it with another object, if applicable
        if food_obj.replace_obj:
            self.user.item_add(food_obj.replace_obj.load())
        # Add this food's effects to the user
        # self.user.effects_add(food_obj.load_effects())
        # Tell the user and the room an "eat" message
        u_tell = self.personalize(food_obj.get_actor_message(), self.user)
        self.user.update_output(u_tell)
        if self.user.location:
            r_tell = self.personalize(food_obj.get_room_message(), self.user)
            self.user.location.tell_room(r_tell, [self.user.name], self.user)
    

command_list.register(Consume, ['eat', 'drink', 'use'])
command_help.register(Consume.help, ['eat', 'drink'])

class Attack(BaseCommand):
    help = (
    """<title>Attack, Kill (Command)</title>
The Attack command causes you to attack another character. 
If you are already in a battle, this will change your target to
the character you specify. If you are not yet in a battle, this 
will start a fight between you and the character you specify. You
must be in the same room as your target to fight them, and can
only attack other players if they have PVP enabled.
\nUSAGE:
To start a fight with a character (or if you are fighting multiple
monsters/characters and want to focus your attacks on a different
character)
  attack <character_name>
    """
    )
    def execute(self):
        #find the target:
        target = self.user.location.get_user(self.args)
        if not target:
            target = self.user.location.get_npc_by_kw(self.args)
            if not target:
                self.user.update_output("Attack whom?")
                return
        # set the users default target.
        self.user.battle_target = target
        if not self.user.battle:
            self.log.debug("Beginning battle between %s and %s" %(self.user, target))
            # Start the battle if it doesn't exist yet.
            self.user.enter_battle()
            b = Battle()
            b.teamA.append(self.user)
            self.user.battle = b
            b.teamB.append(target)
            target.battle = b
            target.enter_battle()
            self.world.battle_add(b)
            target.battle_target = self.user
            self.user.free_attack()
        self.user.update_output("")
    

command_list.register(Attack, ['attack', 'kill'])
command_help.register(Attack.help, ['attack', 'kill'])

class Run(BaseCommand):
    help = (
    """<title>Run, Flee, Escape (Command)</title>
Use Run like the Go command to escape from a battle. 
    """
    )
    def execute(self):
        if self.user.battle:
            def wrapper():
                action = Go(self.user, self.args, 'go')
                action.execute()
            action = Attack_list['run'](self.user, wrapper, self.user.battle)
            self.user.next_action = action
    

battle_commands.register(Run, ['run', 'flee', 'escape', 'go'])
command_help.register(Run.help, ['run', 'flee', 'escape'])

command_help.register(("<title>TextEditMode (Mode)</title>"
"""TextEditMode is a special mode for editing large amounts of text, such as
room or character descriptions. TextEditMode lets you enter text
(line-by-line), until you are finished, letting you replace, delete, and
insert lines as you go. Help for TextEditMode can be accessed by typing @help
at anytime.
"""
), ['TextEditMode', 'text edit mode', 'textedit', 'text edit'])
