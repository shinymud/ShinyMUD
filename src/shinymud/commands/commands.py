from shinymud.lib.world import World
from shinymud.data.config import *
from shinymud.commands.emotes import *
from shinymud.commands.attacks import *
from shinymud.commands import *
from shinymud.lib.battle import Battle

import re
   
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
        self.pc.quit_flag = True
    

command_list.register(Quit, ['quit', 'exit'])
command_help.register(Quit.help, ['quit', 'exit'])

class WorldEcho(BaseCommand):
    """Echoes a message to everyone in the world.
    args:
        args = message to be sent to every player in the world.
    """
    required_permissions = ADMIN
    help = (
    """WorldEcho (Command)
WorldEcho echoes a message to all players currently in the world.
\nRequired Permissions: ADMIN
    """
    )
    def execute(self):
        self.world.tell_players(self.args)
    

command_list.register(WorldEcho, ['wecho', 'worldecho'])
command_help.register(WorldEcho.help, ['wecho', 'world echo', 'worldecho'])

class RoomEcho(BaseCommand):
    """Echoes a message to everyone in a specific room.
    args - message to be sent to the room
    """
    required_permissions = DM | ADMIN
    help = (
    """<title>Room Echo (Command)</title>
The RoomEcho command (or, recho) sends a "disembodied" message to everyone at your
current room location.
\nREQUIRED PERMISSIONS: DM or ADMIN
\nUSAGE:
  recho <message>
    """
    )
    def execute(self):
        if not self.pc.location:
            self.pc.update_output('Your message echoes faintly off into the void.')
            return
        if not self.args:
            self.pc.update_output('Usage: recho <message>. See "help recho" for details.')
            return
        self.pc.location.tell_room(self.args)
    

command_list.register(RoomEcho, ['recho', 'room echo', 'roomecho'])
command_help.register(RoomEcho.help, ['recho', 'room echo', 'roomecho'])

class Chat(BaseCommand):
    """Sends a message to every player on the chat channel."""
    help = (
    """Chat (command)
The Chat command will let you send a message to everyone in the world whose
chat channels are on. See "help channel" for help on turning you chat
channel off.
    """
    )
    def execute(self):
        if not self.args:
            self.pc.update_output("What do you want to chat?")
            return
        if not self.pc.channels['chat']:
            self.pc.channels['chat'] = True
            self.pc.update_output('Your chat channel has been turned on.\n')
        exclude = [player.name for player in self.world.player_list.values() if not player.channels['chat']]
        if 'drunk' in self.pc.effects:
            self.args = self.pc.effects['drunk'].filter_speech(self.args)
        message = '%s chats, "%s"' % (self.pc.fancy_name(), self.args)
        self.world.tell_players(message, exclude, chat_color)
    

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
            for key, value in self.pc.channels.items():
                if value:
                    chnls += '\n  ' + key + ': ' + 'on'
                else:
                    chnls += '\n  ' + key + ': ' + 'off'
            self.pc.update_output(chnls)
            return
        toggle = {'on': True, 'off': False}
        args = self.args.split()
        channel = args[0].lower()
        choice = args[1].lower()
        if channel in self.pc.channels.keys():
            if choice in toggle.keys():
                self.pc.channels[channel] = toggle[choice]
                self.pc.update_output('The %s channel has been turned %s.\n' % (channel, choice))
            else:
                self.pc.update_output('You can only turn the %s channel on or off.\n' % channel)
        else:
            self.pc.update_output('Which channel do you want to change?\n')
    

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
            # Player wants to enter BuildMode
            self.enter_build_mode()
        elif self.args == 'exit':
            if self.pc.get_mode() == 'BuildMode':
                self.pc.set_mode('normal')
                self.pc.update_output('Exiting BuildMode.')
            else:
                self.pc.update_output('You\'re not in BuildMode right now.')
        elif self.args == 'here':
            # Builder wants to start building at her current location
            if self.pc.location:
                self.edit(self.pc.location.area, self.pc.location)
            else:
                self.pc.update_output('You\'re in the void; there\'s nothing to build.')
        else:
            area = self.world.get_area(self.args)
            if not area:
                self.pc.update_output('Area "%s" doesn\'t exist.' % self.args)
                self.pc.update_output('See "help buildmode" for help with this command.')
            else:
                self.edit(area)
    
    def enter_build_mode(self):
        """The player should enter BuildMode."""
        if self.pc.get_mode() == 'BuildMode':
            self.pc.update_output('To exit BuildMode, type "build exit".')
        else:
            self.pc.set_mode('build')
            self.pc.update_output('Entering BuildMode.')
    
    def edit(self, area, room=None):
        """Initialize the player's edit_area (and possible edit_object.). This
        is super hackish, as I'm reproducing code from the BuildCommand Edit.
        I just didn't want to create an import cycle for the sake of accessing
        one command and was too lazy to change things around to work better.
        Should probably clean this up in the future.
        """
        if self.pc.get_mode() != 'BuildMode':
            self.enter_build_mode()
        if (self.pc.name in area.builders) or (self.pc.permissions & GOD):
            self.pc.mode.edit_area = area
            self.pc.mode.edit_object = None
            if room:
                self.pc.mode.edit_object = room
                self.pc.update_output('Now editing room %s in area "%s".' %
                                        (room.id, area.name))
            else:
                self.pc.update_output('Now editing area "%s".' % area.name)
        else:
            self.pc.update_output('You can\'t edit someone else\'s area.')
    

command_list.register(Build, ['build'])
command_help.register(Build.help, ['build', 'build mode', 'buildmode'])

class Look(BaseCommand):
    """Look at a room, item, npc, or PC."""
    help = (
    """<title>Look (Command)</title>
The Look command allows a player to examine a room, item, or npc in detail.
\nUSAGE:
To look at your current location:
  look
To look at something in your current location or inventory:
  look [at] <npc/item-keyword> [in <room/inventory>]
\nEXAMPLES:
Most of the time it's enough just to use "look <npc/item>", which will look for
the item (or npc) in your current location first, then in your inventory if an
item can't be found in your surroundings:
  look at dagger
  look at bernie the shopkeeper
If there happens to be a dagger in your current room and a dagger in your
inventory, you might want to be more specific as to which place you look in:
  look at dagger in inventory
  look at dagger in room
    """
    )
    def execute(self):
        message = 'You don\'t see that here.\n'
        if not self.args:
            # if the player didn't specify anything to look at, just show them the
            # room they're in.
            message = self.look_at_room()
        else:
            exp = r'(at[ ]+)?((?P<thing1>(\w|[ ])+)([ ]in[ ](?P<place>(room)|(inventory)|)))|((at[ ]+)?(?P<thing2>(\w|[ ])+))'
            match = re.match(exp, self.args, re.I)
            if match:
                thing1, thing2, place = match.group('thing1', 'thing2', 'place')
                thing = thing1 or thing2
                thing = thing.strip()
                # just in case someone thought they needed to be uber specific
                # to look at their room...
                if thing == 'room':
                    message = self.look_at_room()
                else:
                    if place:
                        obj_desc = getattr(self, 'look_in_' + place)(thing)
                    else:
                        obj_desc = self.look_in_room(thing) or self.look_in_inventory(thing)
                    if obj_desc:
                        message = obj_desc
        
        self.pc.update_output(message)
    
    def look_at_room(self):
        if self.pc.location:
            return self.pc.look_at_room()
        else:
            return 'You see a dark void.'
    
    def look_in_room(self, keyword):
        if self.pc.location:
            obj = self.pc.location.check_for_keyword(keyword)
            if obj:
                if self.alias == 'read':
                    return obj.description
                message = "You look at %s:\n%s" % (obj.name, obj.description)
                # This is a bit hackish -- npcs don't have a has_type attr, so we're making sure
                # we have an item by process of elimination. If we have an item, and
                # that item has a container type, we should display its contents.
                if hasattr(obj, 'has_type') and obj.has_type('container'):
                    message += '\n' + obj.item_types.get('container').display_inventory()
                return message
        return None
    
    def look_in_inventory(self, keyword):
        item = self.pc.check_inv_for_keyword(keyword)
        if item:
            message = "You look at %s:\n%s" % (item.name, item.description)
            if item.has_type('container'):
                message += '\n' + item.item_types.get('container').display_inventory()
            return message
        return None
    

command_list.register(Look, ['look', 'read'])
command_help.register(Look.help, ['look', 'read'])

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
            self.pc.update_output('Where did you want to go to?')
            return
        exp = r'((room)?([ ]?(?P<room_id>\d+))(([ ]+in)?([ ]+area)?([ ]+(?P<area>\w+)))?)|(?P<name>\w+)'
        match = re.match(exp, self.args.strip())
        message = 'Type "help goto" for help with this command.'
        if not match:
            self.pc.update_output(message)
            return
        name, area_name, room_id = match.group('name', 'area', 'room_id')
        # They're trying to go to the same room as another player
        if name:
            # go to the same room that player is in
            per = self.world.get_player(name)
            if per:
                if per.location:
                    self.pc.go(per.location, self.pc.goto_appear, 
                                 self.pc.goto_disappear)
                else:
                    self.pc.update_output('You can\'t reach %s.\n' % per.fancy_name())
            else:
                self.pc.update_output('That person doesn\'t exist.\n')
        # They're trying to go to a specific room
        elif room_id:
            # See if they specified an area -- if they did, go there
            if area_name:
                area = self.world.get_area(area_name)
                if not area:
                    self.pc.update_output('Area "%s" doesn\'t exist.' % area_name)
                    return
            else:
                if not self.pc.location:
                    self.pc.update_output(message)
                    return
                area = self.pc.location.area
            room = area.get_room(room_id)
            if room:
                self.pc.go(room, self.pc.goto_appear, 
                             self.pc.goto_disappear)
            else:
                self.pc.update_output('Room "%s" doesn\'t exist in area %s.' % (room_id, area.name))
        else:
            self.pc.update_output(message)
    

command_list.register(Goto, ['goto'])
command_help.register(Goto.help, ['goto', 'go to'])

class Go(BaseCommand):
    """Go to the next room in the direction given."""
    help = (
    """<title>Go (Command)</title>
The Go command and its aliases allows a player to travel in a given direction.
\nUSAGE:
  go <direction>
Or just give the direction you want to go:
  <direction>
\nDirections and their shorthands:
  north (n)
  west (w)
  east (e)
  south (s)
  up (u)
  down (d)
    """
    )
    def execute(self):
        dir_map = {'n': 'north', 's': 'south', 'e': 'east', 'w': 'west',
                   'u': 'up', 'd': 'down'
                  }
        if self.alias == 'go':
            if not self.args:
                self.pc.update_output('Go in which direction?')
                return
            if self.args in dir_map:
                direction = dir_map[self.args]
            else:
                direction = self.args
        else:
            if self.alias in dir_map:
                direction = dir_map[self.alias]
            else:
                direction = self.alias
        
        if self.pc.location:
            go_exit = self.pc.location.exits.get(direction)
            if go_exit:
                if go_exit._closed:
                    self.pc.update_output('The door is closed.\n')
                else:
                    if go_exit.to_room:
                        if go_exit.linked_exit:
                            arrives = {'up': 'above', 'down': 'below', 'north': 'the north',
                                       'south': 'the south', 'east': 'the east', 'west': 'the west'}
                            tell_new = '%s arrives from %s.' % (self.pc.fancy_name(),
                                                                    arrives.get(go_exit.linked_exit))
                        else:
                            tell_new = '%s suddenly appears in the room.' % self.pc.fancy_name()
                        tell_old = '%s leaves %s.' % (self.pc.fancy_name(),
                                                             go_exit.direction)
                        self.pc.go(go_exit.to_room, tell_new, tell_old)
                    else:
                        # SOMETHING WENT BADLY WRONG IF WE GOT HERE!!!
                        # somehow the room that this exit pointed to got deleted without informing
                        # this exit.
                        self.world.log.critical('EXIT FAIL: Exit %s from room %s in area %s failed to resolve.' % (go_exit.direction, go_exit.room.id, go_exit.room.area.name))
                        # Delete this exit in the database and the room - we don't want it 
                        # popping up again
                        go_exit.destruct()
                        self.pc.location.exits[go_exit.direction] = None
                        # Tell the player to ignore the man behind the curtain
                        self.pc.location.tell_room('A disturbance was detected in the Matrix: Entity "%s exit" should not exist.\nThe anomaly has been repaired.\n' % self.args)
                        
            else:
                self.pc.update_output('You can\'t go that way.\n')
        else:
            self.pc.update_output('You exist in a void; there is nowhere to go.\n')
    

command_list.register(Go, ['go', 'move', 'north', 'n', 'south', 's', 'east', 'e',
                           'west', 'w', 'up', 'down', 'u', 'd'])
command_help.register(Go.help, ['go', 'move', 'north', 'east', 'south', 'west', 'up',
                                'down', 'u', 'd', 'n', 'e', 's', 'w'])

class Say(BaseCommand):
    """Echo a message from the player to the room that player is in."""
    help = (
    """Say (Command)
The Say command sends a message to everyone in the same room (and only the
people in the same room). Players that are asleep will not hear things that
are said while they are sleeping.
\nUSAGE:
  say <message>
    """
    )
    def execute(self):
        if self.args:
            if self.pc.location:
                if 'drunk' in self.pc.effects:
                    self.args = self.pc.effects['drunk'].filter_speech(self.args)
                message = '%s says, "%s"' % (self.pc.fancy_name(), self.args)
                message = say_color + message + clear_fcolor
                self.pc.location.tell_room(message, teller=self.pc)
            else:
                self.pc.update_output('Your words are sucked into the void.')
        else:
            self.pc.update_output('Say what?')
    

command_list.register(Say, ['say'])
command_help.register(Say.help, ['say'])

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
            self.pc.update_output('What do you want to load?\n')
        else:
            help_message = 'Type "help load" for help on this command.\n'
            exp = r'(?P<obj_type>(item)|(npc))([ ]+(?P<obj_id>\d+))(([ ]+from)?([ ]+area)?([ ]+(?P<area_name>\w+)))?'
            match = re.match(exp, self.args, re.I)
            if match:
                obj_type, obj_id, area_name = match.group('obj_type', 'obj_id', 'area_name')
                if not obj_type or not obj_id:
                    self.pc.update_output(help_message)
                else:
                    if not area_name and self.pc.location:
                        getattr(self, 'load_' + obj_type)(obj_id, self.pc.location.area)
                    elif not area_name and self.pc.mode.edit_area:
                        getattr(self, 'load_' + obj_type)(obj_id, self.pc.mode.edit_area)
                    elif area_name and self.world.area_exists(area_name):
                        getattr(self, 'load_' + obj_type)(obj_id, self.world.get_area(area_name))
                    else:
                        self.pc.update_output('You need to specify an area to load from.\n')
            else:
                self.pc.update_output(help_message)
    
    def load_npc(self, npc_id, npc_area):
        """Load an npc into the same room as the player."""
        if not self.pc.location:
            self.pc.update_output('But you\'re in a void!')
            return
        prototype = npc_area.get_npc(npc_id)
        if prototype:
            npc = prototype.load()
            npc.location = self.pc.location
            self.pc.location.add_char(npc)
            self.pc.update_output('You summon %s into the world.\n' % npc.name)
            if self.alias == 'spawn':
                self.pc.location.tell_room('%s summons %s.' % (self.pc.fancy_name(), npc.name), 
                                             [self.pc.name], self.pc)
        else:
            self.pc.update_output('That npc doesn\'t exist.')
    
    def load_item(self, item_id, item_area):
        """Load an item into the player's inventory."""
        prototype = item_area.get_item(item_id)
        if prototype:
            item = prototype.load()
            self.pc.item_add(item)
            self.pc.update_output('You summon %s into the world.\n' % item.name)
            if self.pc.location and (self.alias == 'spawn'):
                self.pc.location.tell_room('%s summons %s into the world.' % (self.pc.fancy_name(), item.name), 
                                                                                [self.pc.name], self.pc)
        else:
            self.pc.update_output('That item doesn\'t exist.\n')

        
    

command_list.register(Load, ['load', 'spawn'])
command_help.register(Load.help, ['load', 'spawn'])

class Inventory(BaseCommand):
    """Show the player their inventory."""
    help = (
    """<title>Inventory (command)</title>
The Inventory command shows a player to see a list of items in their inventory.
\nALIASES: i, inv
\nUSAGE:
  inventory
    """
    )
    def execute(self):
        i = 'You have %s %s.\n' % (str(self.pc.currency), CURRENCY)
        if not self.pc.inventory:
            i += 'Your inventory is empty.'
        else:
            i += 'Your inventory consists of:\n'
            for item in self.pc.inventory:
                if item not in self.pc.isequipped:
                    i += item.name + '\n'
        self.pc.update_output(i)
    

command_list.register(Inventory, ['i', 'inventory', 'inv'])
command_help.register(Inventory.help, ['i', 'inv', 'inventory'])

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
        if not self.args:
            self.pc.update_output('Try: "give <item> to <person>", or type "help give".')
            return
        exp = r'(?P<amount>\d+)?([ ]+)?(?P<thing>.*?)([ ]+)(to[ ]+)?(?P<givee>\w+)'
        match = re.match(exp, self.args, re.I)
        if not match:
            self.pc.update_output('Try: "give <item> to <person>", or type "help give".')
        elif not self.pc.location:
            self.pc.update_output('You are alone in the void; there\'s no one to give anything to.\n')
        else:
            amount, thing, person = match.group('amount', 'thing', 'givee')
            #check that the person we're giving to exists
            givee = self.pc.location.get_player(person)
            if not givee:
                givee = self.pc.location.get_npc_by_kw(person)
                if not givee:
                    self.pc.update_output('%s isn\'t here.' % person.capitalize())
                    return
            #check for giving an item
            thing_name = 'something'
            item = self.pc.check_inv_for_keyword(thing)
            if item:
                self.pc.item_remove(item)
                givee.item_add(item)
                thing_name = item.name
            #check for giving currency
            elif not item and thing == CURRENCY:
                if not amount:
                    amount = 1
                else:
                    amount = int(amount)
                if self.pc.currency < amount:
                    self.pc.update_output('You don\'t have that much ' + CURRENCY + '.')
                    return
                else:
                    self.pc.currency -= amount
                    givee.currency += amount
                    thing_name = str(amount) + ' ' + CURRENCY
            else:
                self.pc.update_output('You don\'t have %s.' % thing)
                return
                
            #We've completed the giving process, now tell everyone about it.
            self.pc.update_output('You give %s to %s.' % (thing_name, givee.fancy_name()))
            givee.update_output('%s gives you %s.' % (self.pc.fancy_name(), thing_name))
            self.pc.location.tell_room('%s gives %s to %s.' % (self.pc.fancy_name(),
                                                                  thing_name,
                                                                  givee.fancy_name()),
                                        [self.pc.name, givee.name])
            if item and givee.is_npc():
                givee.notify('given_item', {'giver': self.pc, 
                                            'item': item})
    def give_currency(self, amount, givee):
        if self.pc.currency < amount:
            self.pc.update_output('You don\'t have that much ' + CURRENCY + '.')
        else:
            self.pc.currency -= amount
            givee.currency += amount
            curr = 'some ' + CURRENCY
    

command_list.register(Give, ['give'])
command_help.register(Give.help, ['give'])

class Drop(BaseCommand):
    """Drop an item from the player's inventory into the player's current room."""
    help = (
    """<title>Drop (Command)</title>
The Drop command allows you to drop an item from your inventory onto the ground.
\nUSAGE:
  drop <item-name>
    """
    )
    def execute(self):
        if not self.args:
            self.pc.update_output('What do you want to drop?\n')
        else:
            item = self.pc.check_inv_for_keyword(self.args)
            if item:
                self.pc.item_remove(item)
                self.pc.update_output('You drop %s.\n' % item.name)
                if self.pc.location:
                    self.pc.location.item_add(item)
                    self.pc.location.tell_room('%s drops %s.\n' % (self.pc.fancy_name(), 
                                                                     item.name), [self.pc.name])
                else:
                    self.pc.update_output('%s disappears into the void.\n' % item.name)
                    item.destruct()
            else:
                self.pc.update_output('You don\'t have that.\n')
    

command_list.register(Drop, ['drop'])
command_help.register(Drop.help, ['drop'])

class Get(BaseCommand):
    """Get an item and store it in the player's inventory."""
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
            self.pc.update_output('What do you want to get?\n')
            return
        exp = r'(up[ ]+)?((?P<target_kw>(\w|[ ])+)([ ]+from)([ ]+(?P<source_kw>(\w|[ ])+)))|((up[ ]+)?(?P<item_kw>(\w|[ ])+))'
        match = re.match(exp, self.args, re.I)
        if not match:
            self.pc.update_output('Type "help get" for help with this command.')
            return
        target_kw, source_kw, item_kw = match.group('target_kw', 'source_kw', 
                                                    'item_kw')
        if source_kw:
            message = self.get_item_from_container(source_kw, target_kw)
        else:
            message = self.get_item_from_room(item_kw)
        self.pc.update_output(message)
    
    def get_item_from_container(self, source_kw, target_kw):
        c_item = self.pc.location.get_item_by_kw(source_kw) or \
                    self.pc.check_inv_for_keyword(source_kw)
        if not c_item:
            return 'There\'s no "%s" containers here.' % source_kw
        if not c_item.has_type('container'):
            return 'That\'s not a container.'
        container = c_item.item_types.get('container')
        if container.closed:
            return '%s is closed.' % c_item.name.capitalize()
        item = container.get_item_by_kw(target_kw)
        if not item:
            return '%s doesn\'t exist.' % target_kw.capitalize()
        if item.carryable or (self.pc.permissions & GOD):
            container.item_remove(item)
            self.pc.item_add(item)
            if self.pc.location:
                room_tell = '%s gets %s from %s.' % (self.pc.fancy_name(),
                                                       item.name, c_item.name)
                self.pc.location.tell_room(room_tell, [self.pc.name])
            return 'You get %s.' % item.name
        else:
            return 'You can\'t take that.'
    
    def get_item_from_room(self, item_kw):
        if not self.pc.location:
            return 'Only cold blackness exists in the void. ' +\
                   'It\'s not the sort of thing you can take.'
        item = self.pc.location.get_item_by_kw(item_kw)
        if not item:
            return '%s doesn\'t exist.' % item_kw
        if item.carryable or (self.pc.permissions & GOD):
            self.pc.location.item_remove(item)
            self.pc.item_add(item)
            room_tell = '%s gets %s.' % (self.pc.fancy_name(), item.name)
            self.pc.location.tell_room(room_tell, [self.pc.name])
            return 'You get %s.' % item.name
        else:
            return 'You can\'t take that.'
    

command_list.register(Get, ['get', 'take', 'pick'])
command_help.register(Get.help, ['get', 'take', 'pick'])

class Put(BaseCommand):
    """Put an object inside a container."""
    help = (
    """<title>Put (Command)</title>
\nThe put command allows you to put an item inside a container. If you are
just looking to get rid of an inventory item or leave an item in a room, try
the Drop command.
\nUSAGE:
To put an item inside a container:
  put <item-name> in <container-name>
\nThe preposition (the word "in") is required, but can also be replaced with
"inside" or "on". To get an item out of a container, see "help get".
    """
    )
    def execute(self):
        if not self.args:
            self.pc.update_output('Put what where?')
            return
        exp = r'(?P<target_kw>(\w|[ ])+)([ ]+(?P<prep>(in)|(inside)|(on)))(?P<container>(\w|[ ])+)'
        match = re.match(exp, self.args.lower().strip())
        if not match:
            self.pc.update_output('Type "help put" for help with this command.')
            return
        target_kw, preposition, cont_kw = match.group('target_kw', 
                                                      'prep', 
                                                      'container')
        target = self.pc.check_inv_for_keyword(target_kw)
        if not target:
            self.pc.update_output('You don\'t have "%s".' % target_kw)
            return
        container = self.pc.check_inv_for_keyword(cont_kw)
        # Make sure the container object exists
        if not container:
            if self.pc.location:
                container = self.pc.location.get_item_by_kw(cont_kw)
                if not container:
                    self.pc.update_output('%s isn\'t here.' % cont_kw)
                    return
        # Make sure it's a container
        if not container.has_type('container'):
            self.pc.update_output('%s is not a container.' % 
                                    container.name.capitalize())
            return
        c_type = container.item_types['container']
        if c_type.closed:
            self.pc.update_output('It\'s closed.')
            return
        if c_type.item_add(target):
            self.pc.update_output('You put %s %s %s.' % (target.name,
                                                           preposition,
                                                           container.name))
            if self.pc.location:
                tr = '%s puts %s %s %s.' % (self.pc.fancy_name(), 
                                            target.name, preposition,
                                            container.name)
                self.pc.location.tell_room(tr, [self.pc.name])
        else:
            self.pc.update_output('%s won\'t fit %s %s.' % (target.name.capitalize(),
                                                              preposition,
                                                              container.name))
    

command_list.register(Put, ['put'])
command_help.register(Put.help, ['put'])

class Equip(BaseCommand):
    """Equip an item from the player's inventory."""
    help = (
    """<title>Equip (Command)</title>
The equip command allows you to wear or hold an item that can be worn or held. 
Weapons, armor, clothing, and jewelry for example, can all be equipped. You have
a number of places where you may wear/hold equipped items, such as on your head
(for hats) or on your feet (for shoes or boots). 
\n<b>USAGE</b>:
To just see a list of currently equipped items, type
  <b>equip</b>
To equip an item in your inventory, type
  <b>equip <item></b>
\nFor removing items, see <b>help unequip</b>.
    """)
    def execute(self):
        message = ''
        if not self.args:
            #Note: Does not output slot types in any order.
            message = 'Equipped items:'
            for i, j in self.pc.equipped.iteritems():
                message += '\n' + i + ': '
                if j:
                    message += j.name
                else:
                    message += 'None.'
            message += '\n'
        else:
            item = self.pc.check_inv_for_keyword(self.args)
            if not item:
                message = 'You don\'t have it.\n'
            else:
                equip_type = item.item_types.get('equippable')
                if not equip_type:
                    message = 'You can\'t equip that!\n'
                elif equip_type.equip_slot not in EQUIP_SLOTS:
                    message = 'How do you equip that?'
                else:
                    if self.pc.equipped.get(equip_type.equip_slot): #if slot not empty
                        self.pc.isequipped.remove(item)   #remove item in slot
                    self.pc.equipped[equip_type.equip_slot] = item
                    self.pc.isequipped += [item]
                    equip_type.on_equip()
                    message = EQUIP_SLOTS[equip_type.equip_slot].replace('#item', item.name) + '\n'
        self.pc.update_output(message)  
    

command_list.register(Equip, ['equip', 'wear', 'wield'])
command_help.register(Equip.help, ['equip', 'wear', 'wield'])

class Unequip(BaseCommand):
    """Unequip items."""
    help = (
    """<title>Unequip (Command)</title>
Removes an equipped item and places it back in your inventory.
<b>USAGE:</b>
To remove an item that is currently equipped, try
  <b>unequip <item></b>
To equip items, or to see a list of currently equipped items,
see <b>help equip</b>
    """
    )
    def execute(self):
        item = self.pc.check_inv_for_keyword(self.args)
        message = ''
        if not self.args:
            message = 'What do you want to unequip?\n'
        elif not item: 
            message = 'You don\'t have that!\n'
        equip_type = item.item_types.get('equippable')
        if not equip_type:
            message = 'That item is not equippable.\n'
        elif not self.pc.equipped[equip_type.equip_slot]:
            message = 'You aren\'t using anything in that slot.\n'
        else:
            self.pc.equipped[equip_type.equip_slot] = ''
            self.pc.isequipped.remove(item)
            equip_type.on_unequip()
            message = 'You remove ' + item.name + '.\n'
        self.pc.update_output(message)
    

command_list.register(Unequip, ['unequip'])
command_help.register(Unequip.help, ['unequip'])

class Who(BaseCommand):
    """Return a list of names comprised of players who are currently playing the game."""
    help = (
    """Who (Command)
The Who command returns a list of all the players currently in the game.
\nUSAGE:
  who
    """
    )
    def execute(self):
        persons = [per for per in self.world.player_list.values() if isinstance(per.name, basestring)]
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
        self.pc.update_output(message)
    

command_list.register(Who, ['who'])
command_help.register(Who.help, ['who'])

class Enter(BaseCommand):
    """Enter a portal."""
    help = (
    """<title>Enter (Command)</title>
The Enter Command allows a character to enter a portal object.
\nUSAGE:
  enter <portal-name>
    """
    )
    def execute(self):
        if not self.args:
            self.pc.update_output('Enter what?\n')
            return
        fail = 'You don\'t see "%s" here.' % self.args
        if self.pc.location:
            # Check the room for the portal object first
            obj = self.pc.location.get_item_by_kw(self.args)
            if obj:
                if 'portal' in obj.item_types:
                    self.go_portal(obj.item_types['portal'])
                else:
                    self.pc.update_output('%s is not a portal.' % obj.name.capitalize())
            else:
                # If the portal isn't in the room, check their inventory
                obj = self.pc.check_inv_for_keyword(self.args)
                if obj:
                    if 'portal' in obj.item_types:
                        # If the portal is in their inventory, make them drop it first
                        # (a portal can't go through itself)
                        Drop(self.pc, self.args, 'drop').execute()
                        self.go_portal(obj.item_types['portal'])
                    else:
                        self.pc.update_output('%s is not a portal.' % obj.name.capitalize())
                else:
                    # We've struck out an all counts -- the player doesn't have a portal
                    self.pc.update_output(fail)
    
    def go_portal(self, portal):
        """Go through a portal."""
        if portal.location:
            if self.pc.location: 
                self.pc.location.tell_room(self.personalize(portal.leave_message, self.pc), 
                                             [self.pc.name])
            self.pc.update_output(self.personalize(portal.entrance_message, self.pc))
            self.pc.go(portal.location)
            self.pc.location.tell_room(self.personalize(portal.emerge_message, self.pc), 
                                         [self.pc.name])
        else:
            self.pc.update_output('Nothing happened. It must be a dud.')
    

command_list.register(Enter, ['enter'])
command_help.register(Enter.help, ['enter'])

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
            if self.pc.location:
                self.pc.location.purge_room()
                self.pc.update_output('The room has been purged.\n')
            else:
                self.pc.update_output('You\'re in a void, there\'s nothing to purge.\n')
        elif self.args in ['i', 'inventory']:
            # Purge their inventory!
            for i in range(len(self.pc.inventory)):
                item = self.pc.inventory[0]
                self.pc.item_remove(item)
                item.destruct()
            self.pc.update_output('Your inventory has been purged.\n')
        else:
            # Purge a specific npc or item based on keyword
            self.pc.update_output('Someone didn\'t endow me with the functionality to purge that for you.\n')
    

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
        self.pc.update_output(message)
    

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
        if not self.pc.location:
            self.pc.update_output('You try, but the action gets sucked into the void. The void apologizes.')
        elif self.alias == 'emote':
            self.pc.location.tell_room('%s %s' % (self.pc.fancy_name(),
                                                    self.args), 
                                         teller=self.pc)
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
                victim = self.pc.location.get_player(self.args.lower()) or\
                         self.pc.location.get_npc_by_kw(self.args.lower()) or\
                         self.world.get_player(self.args.lower())
                if not victim:
                    # victim = self.world.get_player(self.args.lower())
                    # if not victim:                        
                    self.pc.update_output('%s isn\'t here.' % 
                                            self.args.capitalize())
                elif victim == self.pc:
                    self.single_person_emote(emote_list)
                else:
                    self.double_person_emote(emote_list, victim)
    
    def single_person_emote(self, emote_list):
        """A player wishes to emote an action alone."""
        actor_m = self.personalize(emote_list[0][0], self.pc)
        room_m = self.personalize(emote_list[0][1], self.pc)
        self.pc.update_output(actor_m)
        self.pc.location.tell_room(room_m, [self.pc.name])
    
    def double_person_emote(self, emote_list, victim):
        """A player wishes to emote an action on a target."""
        # We got this far, we know the victim exists in the world
        actor = self.personalize(emote_list[1][0], self.pc, victim)
        victimm = self.personalize(emote_list[1][1], self.pc, victim)
        if victim.location == self.pc.location:
            room_m = self.personalize(emote_list[1][2], self.pc, victim)
            self.pc.update_output(actor)
            victim.update_output(victimm)
            self.pc.location.tell_room(room_m, [self.pc.name, victim.name])
        else:
            self.pc.update_output('From far away, ' + actor)
            victim.update_output('From far away, ' + victimm)
        if victim.is_npc():
            victim.notify('emoted', {'emote': self.alias, 'emoter': self.pc})
    

command_list.register(Emote, Emote.aliases)
command_help.register(Emote.help, ['emote', 'emotes'])
command_help.register(Emote.elist, ['emote list'])

class Bestow(BaseCommand):
    """Bestow a new class of permissions on a PC."""
    required_permissions = GOD
    help = (
    """<title>Bestow (Command)</title>
Bestow allows you to extend a player's permissions by giving them another
permission group.
\nRequired Permissions: GOD
\nUSAGE:
To bestow a privilege upon a player:
  bestow <permission-group> [upon] <player-name>
To bestow a privilege upon a player:
  bestow <permission-group> [upon] npc <player-name>
\nPermission Groups:
  player
  dm
  admin
  god
\n<b>BEWARE!!!!!
Bestowing privileges beyond DM upon npcs can be very dangerous. Since npcs can
be controlled by scripts, it is possible for other builders to run commands
above their authority level through this npc if they have access to this npc's
build area (they are on the area's BuildersList). You might want to make sure
you're the only one with builder privileges to the area of the npc you're giving
escalated privileges to.</b>
\nTo revoke permissions, see "help revoke". For more information on
permissions and permission groups, see "help permissions".
    """
    )
    def execute(self):
        if not self.args:
            self.pc.update_output('Bestow what authority upon whom?\n')
            return
        exp = r'(?P<permission>(god)|(dm)|(builder)|(admin))[ ]?(to)?(on)?(upon)?([ ]+(?P<npc>npc))?([ ]+(?P<player>\w+))'
        match = re.match(exp, self.args.lower(), re.I)
        if not match:
            self.pc.update_output('Type "help bestow" for help on this command.')
            return
        perm, npc, player = match.group('permission', 'npc', 'player')
        if npc:
            error = 'Npc doesn\'t exist.'
            if not self.pc.location:
                self.pc.update_output(error)
                return
            player = self.pc.location.get_npc_by_kw(player)
            self.pc.update_output('WARNING: giving npcs wider permissions can be dangerous. See "help bestow".')
        else:
            player = self.world.get_player(player)
        permission = globals().get(perm.upper())
        if not player:
            self.pc.update_output('That player isn\'t on right now.')
            return
        if not permission:
            self.pc.update_output('Valid permission types are: god, dm, builder, and admin.')
            return
        if player.permissions & permission:
            self.pc.update_output('%s already has that authority.' % player.fancy_name())
            return
        player.permissions = player.permissions | permission
        if not player.is_npc():
            player.save()
        self.world.play_log.info('%s bestowed the authority of %s upon %s.' % (
                    self.pc.fancy_name(), perm.upper(), player.fancy_name()))
        self.pc.update_output('%s now has the privilige of being %s.' % (player.fancy_name(), perm.upper()))
        player.update_output('%s has bestowed the authority of %s upon you!' % (self.pc.fancy_name(), perm.upper()))
        self.world.tell_players('%s has bestowed the authority of %s upon %s!' %
                              (self.pc.fancy_name(), perm.upper(), player.fancy_name()),
                              [self.pc.name, player.name])
    

command_list.register(Bestow, ['bestow'])
command_help.register(Bestow.help, ['bestow'])

class Revoke(BaseCommand):
    """Revoke permission privilges for a PC."""
    required_permissions = GOD
    help = (
    """<title>Revoke (Command)</title>
The revoke command allows you to revoke the priviliges of other players.
\nRequired Permissions: GOD
\nUSAGE:
  revoke <permission-group> [from/for] <player-name>
\nPermission Groups:
  player
  dm
  admin
  god
\nTo bestow permissions, see "help bestow". For more information on
permissions and permission groups, see "help permissions".
    """
    )
    def execute(self):
        if not self.args:
            self.pc.update_output('Revoke whose authority over what?\n')
            return
        exp = r'(?P<permission>(god)|(dm)|(builder)|(admin))[ ]?(from)?(on)?(for)?([ ]+(?P<player>\w+))'
        match = re.match(exp, self.args.lower(), re.I)
        if not match:
            self.pc.update_output('Type "help revoke" for help on this command.')
            return
        perm, player = match.group('permission', 'player')
        if self.pc.location:
            npc = self.pc.location.get_npc_by_kw(player)
        player = self.world.get_player(player) or npc
        permission = globals().get(perm.upper())
        if not player:
            self.pc.update_output('That player isn\'t on right now.')
            return
        if not permission:
            self.pc.update_output('Valid permission types are: god, dm, builder, and admin.')
            return
        if not (player.permissions & permission):
            self.pc.update_output('%s doesn\'t have that authority anyway.' % player.fancy_name())
            return
        player.permissions = player.permissions ^ permission
        self.world.play_log.info('%s revoked %s\'s %s authority.' % (
                    self.pc.fancy_name(), player.fancy_name(), perm.upper()))
        self.pc.update_output('%s has had the privilige of %s revoked.' % (player.fancy_name(), perm))
        player.update_output('%s has revoked your %s priviliges.' % (self.pc.fancy_name(), perm))
        if not player.is_npc():
            player.save()
            if player.get_mode() == 'BuildMode':
                player.set_mode('normal')
                player.update_output('You have been kicked from BuildMode.')
    

command_list.register(Revoke, ['revoke'])
command_help.register(Revoke.help, ['revoke'])

class Reset(BaseCommand):
    """The command for resetting a room or area."""
    required_permissions = DM | BUILDER | ADMIN
    help = ("Reset (command)\n"
    """The reset command is used to force a room to respawn all of the items 
and npcs on its spawn list. If you call reset on an entire area, all of the
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
For help on adding items and npcs to a room's spawn list, 
see "help spawns".""")
    
    def execute(self):
        if not self.args:
            # Reset the room the player is in
            if self.pc.location:
                self.pc.location.reset()
                self.pc.update_output('Room %s has been reset.\n' % self.pc.location.id)
            else:
                self.pc.update_output('That\'s a pretty useless thing to do in the void.\n')
        else:
            exp = r'(room[ ]+(?P<room_id>\d+)([ ]+in)?([ ]+area)?([ ]+(?P<room_area>\w+))?)|(area[ ]+(?P<area>\w+))'
            match = re.match(exp, self.args, re.I)
            if not match:
                self.pc.update_output('Type "help reset" to get help with this command.\n')
                return
            room_id, room_area, area = match.group('room_id', 'room_area', 'area')
            if area:
                # reset an entire area
                reset_area = self.world.get_area(area)
                if reset_area:
                    reset_area.reset()
                    self.pc.update_output('Area %s has been reset.\n' % reset_area.name)
                    return
                else:
                    self.pc.update_output('That area doesn\'t exist.\n')
                    return
            # Reset a single room
            if room_area:
                area = self.world.get_area(room_area)
                if not area:
                    self.pc.update_output('That area doesn\'t exist.\n')
                    return
            else:
                if self.pc.location:
                    area = self.pc.location.area
                else:
                    self.pc.update_output('Type "help resets" to get help with this command.\n')
                    return
            room = area.get_room(room_id)
            if not room:
                self.pc.update_output('Room %s doesn\'t exist in area %s.\n' % (room_id, 
                                                                                  area.name))
            room.reset()
            self.pc.update_output('Room %s in area %s has been reset.\n' % (room.id, area.name))
    

command_list.register(Reset, ['reset'])
command_help.register(Reset.help, ['reset', 'resets'])

class Help(BaseCommand):
    help = ("Try 'help <command-name>' for help with a command.\n"
            "For example, 'help go' will give details about the go command."
    )
    def execute(self):
        # get the help parameter and see if it matches a command_help alias
        #     if so, send player the help string
        #     return
        # else, look up in database
        #     if there is a match, send the help string to the player
        #     return
        # else, send "I can't help you with that" string to player
        # return
        if not self.args:
            self.pc.update_output(self.help)
            return
        help = command_help[self.args]
        if help:
            # This should probably be replaced with a better color parsing
            # function when we decide to have better use of colors
            help = help.replace('<b>', BOLD)
            help = help.replace('<blink>', BLINK)
            help = help.replace('<title>', help_title).replace('</title>',
                                                               CLEAR + '\n')
            help = re.sub(r'</\w+>', CLEAR, help)
            self.pc.update_output(help)
        else:
            self.pc.update_output("Sorry, I can't help you with that.\n")
    

command_list.register(Help, ['help', 'explain', 'describe'])
command_help.register(Help.help, ['help', 'explain', 'describe'])

class Clear(BaseCommand):
    """Clear the player's screen and give them a new prompt."""
    help = (
    """Clear (command)
Clears your screen of text and gives you a new prompt.
    """
    )
    def execute(self):
        # First send the ANSI command to clear the entire screen, then
        # send the ANSI command to move the cursor to the "home" position 
        # (the upper left position in the terminal)
        self.pc.update_output('\x1b[2J' + '\x1b[H')
    

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
            self.pc.update_output('What do you want to set?\n')
        else:
            match = re.match(r'\s*(\w+)([ ](.+))?$', self.args, re.I)
            if not match:
                message = 'Type "help set" for help with this command.\n'
            else:
                func, _, arg = match.groups()
                message = 'You can\'t set that.\n'
                if hasattr(self.pc, 'set_' + func):
                    message = (getattr(self.pc, 'set_' + func)(arg))
                self.pc.update_output(message)
    

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
            self.pc.update_output('Open what?')
            return
        exp = r'(?P<dir>(north)|(south)|(east)|(west)|(up)|(down))|(?P<kw>(\w|[ ])+)'
        match = re.match(exp, self.args.lower(), re.I)
        if not match:
            self.pc.update_output('Type "help open" for help with this command.')
            return
        direction, kw = match.group('dir', 'kw')
        if direction:
            message = self.toggle_door(direction, self.alias)
        elif kw:
            message = self.toggle_container(kw, self.alias)
        self.pc.update_output(message)
    
    def toggle_door(self, direction, toggle):
        if not self.pc.location:
            return 'There aren\'t any doors in the void.'
        exit = self.pc.location.exits.get(direction)
        if not exit:
            return 'There isn\'t a door there.'
        if toggle == 'open' or toggle == 'unlock':
            return exit.open_me(self.pc)
        else:
            return exit.close_me(self.pc)
    
    def toggle_container(self, kw, toggle):
        obj = self.pc.check_inv_for_keyword(kw)
        # if nothing in inventory, check room
        if not obj:
            obj = self.pc.location.get_item_by_kw(kw)
            if not obj:
                return 'You don\'t see that here.'
        if not obj.has_type('container'):
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
    

command_list.register(ToggleOpen, ['open', 'close', 'unlock'])
command_help.register(ToggleOpen.help, ['open', 'close', 'unlock'])

class Lock(BaseCommand):
    help = (
    """<title>Lock (Command)</title>
Locks a door, only those with a key may unlock it.
<b>USAGE:</b>
to lock (and close) a door, try
    <b>lock <direction></b>""")
    def execute(self):
        if not self.args:
            return "unlock what?"
        dir_map = {'n':'north', 's':'south', 'e':'east', 'w':'west', 'u':'up', 'd':'down'}
        direction = dir_map.get(self.args[0].lower())
        if not direction:
            self.pc.update_output('Try "help lock" for help with this command')
            return
        if self.pc.location.exits[direction]:
            message = self.pc.location.exits[direction].lock_me(self.pc)
            self.pc.update_output(message)
            return
        self.pc.update_output("There is nothing to lock in that direction")
        return

command_list.register(Lock, ['lock'])
command_help.register(Lock.help, ['lock'])

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
        self.pc.update_output(self.help)
    

command_list.register(Version, ['version', 'credit', 'credits'])
command_help.register(Version.help, ['version', 'credit', 'credits'])

class Sit(BaseCommand):
    """Change the player's position to sitting."""
    help = (
    """<title>Sit (Command)</title>
The Sit command changes your position to sitting.
\nUSAGE:
To sit on the floor:
  sit
To sit on furniture:
  sit [on/in] <furniture-name>
    """
    )
    def execute(self):
        if self.pc.position[0].find(self.alias) != -1:
            self.pc.update_output('You are already sitting.')
            return
        if not self.args:
            if self.pc.position[0] == 'sleeping':
                self.pc.update_output('You wake and sit up.')
                if self.pc.location:
                    self.pc.location.tell_room('%s wakes and sits up.' % self.pc.fancy_name(), [self.pc.name], self.pc)
                self.pc.change_position('sitting', self.pc.position[1])
            else:
                self.pc.update_output('You sit down.')
                if self.pc.location:
                    self.pc.location.tell_room('%s sits down.' % self.pc.fancy_name(), [self.pc.name], self.pc)
                self.pc.change_position('sitting')
        else:
            if not self.pc.location:
                self.pc.update_output('The void is bereft of anything to sit on.')
                return
            exp = r'((on)|(in))?([ ]?)?(?P<furn>(\w|[ ])+)'
            furn_kw = re.match(exp, self.args.lower().strip()).group('furn')
            furn = self.pc.location.get_item_by_kw(furn_kw)
            if not furn:
                self.pc.update_output('You don\'t see that here.')
                return
            f_obj = furn.item_types.get('furniture')
            if not f_obj:
                self.pc.update_output('That\'s not a type of furniture.')
                return
            if not f_obj.player_add(self.pc):
                self.pc.update_output('It\'s full right now.')
                return
            else:
                if self.pc.position[1]:
                    self.pc.position[1].item_types['furniture'].player_remove(self.pc)
                f_obj.player_add(self.pc)
                self.pc.position = ('sitting', furn)
                self.pc.update_output('You sit down on %s.' % furn.name)
                self.pc.location.tell_room('%s sits down on %s.' % (self.pc.fancy_name(), furn.name), 
                                             [self.pc.name], self.pc)
    

command_list.register(Sit, ['sit'])
command_help.register(Sit.help, ['sit'])

class Stand(BaseCommand):
    """Change the player's position to standing."""
    help = (
    """<title>Stand (Command)</title>
The Stand command changes your position from sitting or sleeping to standing.
    """
    )
    def execute(self):
        if self.pc.position[0].find(self.alias) != -1:
            self.pc.update_output('You are already standing.')
            return
        if self.pc.position[0] == 'sleeping':
            self.pc.update_output('You wake and stand up.')
            if self.pc.location:
                self.pc.location.tell_room('%s wakes and stands up.' % self.pc.fancy_name(), [self.pc.name], self.pc)
        else:
            self.pc.update_output('You stand up.')
            if self.pc.location:
                self.pc.location.tell_room('%s stands up.' % self.pc.fancy_name(), [self.pc.name], self.pc)
        self.pc.change_position('standing')
    

command_list.register(Stand, ['stand'])
command_help.register(Stand.help, ['stand'])

class Sleep(BaseCommand):
    """Change the player's position to sleeping."""
    help = (
    """<title>Sleep (Command)</title>
The Sleep command changes your character's position to sleeping. NOTE:
sleeping characters are oblivious to things happening around them (in the same
room) and can be more vulnerable to attack. To awake from sleeping, us the
Wake, Sit, or Stand commands.
\nUSAGE:
To sleep on the floor:
  sleep
To sleep on a piece of furniture:
  sleep [on/in] <furniture-name>
    """
    )
    def execute(self):
        if self.pc.position[0].find(self.alias) != -1:
            self.pc.update_output('You are already sleeping.')
            return
        
        if not self.args:
            self.pc.update_output('You go to sleep.')
            if self.pc.location:
                self.pc.location.tell_room('%s goes to sleep.' % self.pc.fancy_name(), [self.pc.name], self.pc)
            # If they were previously sitting on furniture before they went to
            # sleep, we might as well maintain their position on that 
            # furniture when they go to sleep
            self.pc.change_position('sleeping', self.pc.position[1])
        else:
            if not self.pc.location:
                self.pc.update_output('The void is bereft of anything to sleep on.')
                return
            exp = r'((on)|(in))?([ ]?)?(?P<furn>(\w|[ ])+)'
            furn_kw = re.match(exp, self.args.lower().strip()).group('furn')
            furn = self.pc.location.get_item_by_kw(furn_kw)
            if not furn:
                self.pc.update_output('You don\'t see that here.')
                return
            f_obj = furn.item_types.get('furniture')
            if not f_obj:
                self.pc.update_output('That\'s not a type of furniture.')
                return
            if not f_obj.player_add(self.pc):
                self.pc.update_output('It\'s full right now.')
                return
            else:
                self.pc.change_position('sleeping', furn)
                self.pc.update_output('You go to sleep on %s.' % furn.name)
                self.pc.location.tell_room('%s goes to sleep on %s.' % (self.pc.fancy_name(), furn.name), 
                                             [self.pc.name], self.pc)
    

command_list.register(Sleep, ['sleep'])
command_help.register(Sleep.help, ['sleep'])

class Wake(BaseCommand):
    """Change a player's status from sleeping to awake (and standing)."""
    help = (
    """<title>Wake (Command)</title>
Wake can be used to wake yourself or another character from sleeping.
\nUSAGE:
To wake yourself:
  wake
To wake someone else:
  wake <player-name>
    """
    )
    def execute(self):
        if not self.args:
            # Wake up yourself
            if self.pc.position[0] != 'sleeping':
                self.pc.update_output('You are already awake.')
                return
            self.pc.update_output('You wake and stand up.')
            if self.pc.location:
                self.pc.location.tell_room('%s wakes and stands up.' % self.pc.fancy_name(), [self.pc.name], self.pc)
            self.pc.change_position('standing')
        else:
            # Wake up someone else!
            if not self.pc.location:
                self.pc.update_output('You are alone in the void.')
                return
            sleeper = self.pc.location.get_player(self.args.lower().strip())
            if not sleeper:
                self.pc.update_output('That person isn\'t here.')
                return
            if sleeper.position[0] != 'sleeping':
                self.pc.update_output('%s isn\'t asleep.' % sleeper.fancy_name())
                return
            sleeper.change_position('standing')
            self.pc.update_output('You wake up %s.' % sleeper.fancy_name())
            sleeper.update_output('%s wakes you up.' % self.pc.fancy_name())
            troom = '%s wakes up %s.' % (self.pc.fancy_name(),
                                         sleeper.fancy_name())
            self.pc.location.tell_room(troom, [self.pc.name, sleeper.name],
                                         self.pc)
    

command_list.register(Wake, ['wake', 'awake'])
command_help.register(Wake.help, ['wake'])

class Award(BaseCommand):
    """Award an item to a player."""
    required_permissions = required_permissions = DM | ADMIN
    help = (
    """<title>Award (Command)</title>
\nThe Award command allows a DM or an Admin to award an item to a player. Note
that you must have the item you wish to award in your inventory for the Award
command to work, and you must also be in the same room as the person you wish
to award the item to.
\nRequired Permissions: ADMIN, DM
\nUSAGE:
To award an item to a player:
  award <item-keyword> to <player-name> ["<actor-message>":"<room-message>"]
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
  award medal to jameson "You receive a medal for your fine work.":
  "#actor receives a medal for his fine work."
\nJameson would have the medal added to his inventory and receive the message
"You receive a medal for your fine work." Anyone else in the room would see
the message "Jameson receives a medal for his fine work."
    """
    )
    def execute(self):
        if not self.args:
            self.pc.update_output('Award what to whom?')
            return
        exp = r'(?P<item>(\w+|[ ])+)([ ]+to)([ ]+(?P<player>\w+))([ ]+(?P<actor>\"(.*?)\")(:(?P<room>\"(.*?)\"))?)?'
        match = re.match(exp, self.args, re.I)
        if not match:
            self.pc.update_output('Type "help award" for help with this command.')
            return
        item_kw, player_kw, actor, room = match.group('item', 'player', 'actor', 'room')
        player = self.pc.location.get_player(player_kw.lower())
        if not player:
            self.pc.update_output('Whom do you want to award %s to?' % item_kw)
            return
        item = self.pc.check_inv_for_keyword(item_kw)
        if not item:
            self.pc.update_output('You don\'t have any %s.' % item_kw)
            return
        self.pc.item_remove(item)
        player.item_add(item)
        self.pc.update_output('%s has been awarded %s.' % (player.fancy_name(),
                                                             item.name))
        if actor:
            message = self.personalize(actor.strip('\"'), self.pc)
            player.update_output(message)
        if room:
            message = self.personalize(room.strip('\"'), self.pc, player)
            self.pc.location.tell_room(message, [player.name], self.pc)
    

command_list.register(Award, ['award'])
command_help.register(Award.help, ['award'])

class Consume(BaseCommand):
    """Consume a food or drink item."""
    help = (
    """<title>Eat, Drink, Use (Command)</title>
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
            self.pc.update_output("%s what?" % self.alias.capitalize())
            return
        food = self.pc.check_inv_for_keyword(self.args.lower().strip())
        if not food:
            self.pc.update_output('You don\'t have any %s.' % self.args)
            return
        food_obj = food.item_types.get('food')
        if not food_obj:
            # Gods have a more robust digestive system -- they can afford to
            # eat objects that aren't edible to mere mortals
            if self.pc.permissions & GOD:
                self.pc.item_remove(food)
                food.destruct()
                self.pc.update_output('You consume %s.' % food.name)
                if self.pc.location:
                    self.pc.location.tell_room('%s consumed %s.' %\
                                                 (self.pc.fancy_name(),
                                                  food.name),
                                                [self.pc.name], self.pc)
                return
            else:
                self.pc.update_output('That\'s not edible!')
                return
        if 'drunk' in self.pc.effects:
            self.pc.update_output('You\'re too drunk to manage it.')
            return
        # Remove the food object
        self.world.log.debug(food_obj)
        self.pc.item_remove(food)
        food.destruct()
        # Replace it with another object, if applicable
        if food_obj.replace_obj:
            self.pc.item_add(food_obj.replace_obj.load())
        # Tell the player and the room an "eat" message
        u_tell = self.personalize(food_obj.get_actor_message(), self.pc)
        self.pc.update_output(u_tell)
        if self.pc.location:
            r_tell = self.personalize(food_obj.get_room_message(), self.pc)
            self.pc.location.tell_room(r_tell, [self.pc.name], self.pc)
        # Add this food's effects to the player
        self.world.log.debug('Adding effects.')
        self.pc.effects_add(food_obj.load_effects())
    

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
\n<b>USAGE:</b>
To start a fight with a character (or if you are fighting multiple
monsters/characters and want to focus your attacks on a different
character)
  attack <character_name>
    """
    )
    def execute(self):
        #find the target:
        target = self.pc.location.get_player(self.args)
        if not target:
            target = self.pc.location.get_npc_by_kw(self.args)
            if not target:
                self.pc.update_output("Attack whom?")
                return
        # set the players default target.
        self.pc.battle_target = target
        if not self.pc.battle:
            self.world.log.debug("Beginning battle between %s and %s" %(self.pc.fancy_name(), target.fancy_name()))
            # Start the battle if it doesn't exist yet.
            self.pc.enter_battle()
            b = Battle()
            b.teamA.append(self.pc)
            self.pc.battle = b
            b.teamB.append(target)
            target.battle = b
            target.enter_battle()
            self.world.battle_add(b)
            target.battle_target = self.pc
            self.pc.free_attack()
        self.pc.update_output("")
    

#command_list.register(Attack, ['attack', 'kill'])
#command_help.register(Attack.help, ['attack', 'kill'])

class Run(BaseCommand):
    help = (
    """<title>Run, Flee, Escape (Command)</title>
Use Run like the Go command to escape from a battle.
\n<b>USAGE:</b>
If you are in a hurry, you can run away from a battle in a random
direction using
  <b>run</b>
If you want to escape in a specific direction, try
  <b>run <direction></b>
\nFor more info on directions, see <b>help go</b>.
    """
    )
    def execute(self):
        if self.pc.battle:
            direction = self.args.lower()[0] if self.args else None
            if direction == 'e': 
                room = self.pc.location.exits.get('east')
            elif direction == 'w':
                room = self.pc.location.exits.get('west')
            elif direction == 'n':
                room = self.pc.location.exits.get('north')
            elif direction == 's':
                room = self.pc.location.exits.get('south')
            elif direction == 'u':
                room = self.pc.location.exits.get('up')
            elif direction == 'd':
                room = self.pc.location.exits.get('down')
            else:
                room = None
            if not room:
                # just grab one at random
                room = [_ for _ in self.pc.location.exits.values() if _ is not None][0]
            if not room:
                self.pc.update_output('There\'s nowhere to run!')
                return
            action = Action_list['run'](self.pc, (room.to_room.area.name, room.to_room.id), self.pc.battle)
            self.pc.next_action = action
    

#battle_commands.register(Run, ['run', 'flee', 'escape', 'go'])
#command_help.register(Run.help, ['run', 'flee', 'escape'])

class Me(BaseCommand):
    """Get a score card of your player details."""
    help = (
    """<title>Me (Command)</title>
The Me command returns a score-card of your player details.
\nNOTE:
You can set your password via the "password" command. See "help password" for
details.
\nSome of your details are editable using the set command:
<b>title - (set title <title-text>)</b> A title (or status) that's displayed
next to your name in a Who listing.
<b>email - (set email <e-mail-address>)</b> Your email address. It's never displayed
publicly, and its only real purpose will be to help you to reset your password
if you forget it.
<b>description - (set description, starts TextEditMode)</b> The description that's
seen when people Look at you.
\nIf you have authority to use the Goto command, you can also set the following:
<b>goto appear message - (set goto_appear <appear-message>)</b> The message heard in
a room when you use the Goto command to enter it
<b>set goto_disappear - (set goto_disappear <disappear-message)</b> The message heard
in a room when you use the Goto command to leave it
    """
    )
    def execute(self):
        # We aught to be using the player's terminal width, but for now I'm just
        # doing a boring static screen width
        width = 72
        empty_line = '|' + (' ' * (width - 2)) + '|\n'
        
        effects = ', '.join([str(e) for e in self.pc.effects.values()])
        if not effects:
            effects = 'You feel normal.'
        me = '|' + (' %s ' % self.pc.fancy_name()).center(width -2 , '-') + '|\n'
        me += ('| title: ' + self.pc.title).ljust(width - 1) + '|\n'
        me += ('| money: %s %s' % (self.pc.currency, CURRENCY)).ljust(width - 1) + '|\n'
        me += ('| position: ' + self.pc.position[0]).ljust(width - 1) + '|\n'
        me += ('| effects: ' + effects).ljust(width - 1) + '|\n'
        if self.pc.permissions > PLAYER:
            me += '|' + (' Permission Details ').center(width - 2, '-') + '|\n'
            me += ('| permissions: ' +\
                   ', '.join(get_permission_names(self.pc.permissions))).ljust(width - 1) + '|\n'
            me += ('| goto "appear": ' + self.pc.goto_appear).ljust(width - 1) + '|\n'
            me += ('| goto "disappear": ' + self.pc.goto_disappear).ljust(width - 1) + '|\n'
            me += empty_line
        me += '|' + (' Private Details ').center(width - 2, '-') + '|\n'
        me += ('| email: ' + str(self.pc.email)).ljust(width - 1) + '|\n'
        me += '|' + (' Player Stats ').center(width - 2, '-') + '|\n'
        me += ('| hit: ' + str(self.pc.hit.calculate())).ljust(width-1) + '|\n'
        me += ('| evade: ' + str(self.pc.evade.calculate())).ljust(width-1) + '|\n' 
        if self.pc.absorb:
            me += '| absorb: '.ljust(width-1) + '|\n'
            for key, val in self.pc.absorb.calculate().items():
                me += ('|   %s: %s' % (key, val)).ljust(width-1) + '|\n'
        else:
            me += '| absorb: None'.ljust(width-1) + '|\n'
        if self.pc.damage:
            me += '| damage: '.ljust(width-1) + '|\n'
            for t, mn, mx in self.pc.damage.display():
                me += ('|   %s: %s-%s' % (t, mn, mx)).ljust(width-1) + '|\n'
        else:
            me += '| damage: None'.ljust(width-1) + '|\n'
        me += '|' + ('-' * (width - 2)) + '|'         
        self.pc.update_output(me)
    

command_list.register(Me, ['me', 'status', 'stats'])
command_help.register(Me.help, ['me', 'status'])

class Tell(BaseCommand):
    """Tell another character a private message."""
    help = (
    """<title>Tell (Command)</title>
The Tell command sends a private message to a specific character (can be a pc or
npc). However, you can only Tell an npc something if that npc is in the same
room as you are. You can Tell a player character something regardless of where
they are in the world, provided they are online.
\nUSAGE:
  tell <person-name> <message>
\nEXAMPLE:
  tell brian Your princess is in another castle!
    """
    )
    def execute(self):
        #tell target_name message
        syntax_error = 'Try "tell <person> <message>", or see "help tell" for help.'
        if not self.args:
            self.pc.update_output(syntax_error)
            return
        exp = r'(?P<target>.*?)[ ](?P<message>.*)'
        match = re.match(exp, self.args, re.I)
        if not match:
            self.pc.update_output(syntax_error)
            return
        target_name, message = match.group('target', 'message')
        # first, check to see if there is a character in the same room by that keyword
        # if we were only to check the world's list of people, we wouldn't be able to tell npcs
        # anything! However, let's be prudent and only try to tell npcs in the same room...
        if self.pc.location:
            r = self.pc.location
            # prioritize players over npcs, if there are two characters in the same room with the
            # same name. Players only have one keyword in their name, while npcs may have many
            target = r.get_player(target_name) or r.get_npc_by_kw(target_name)
            if target:
                self.tell_msg(target, message)
                return
        # There was nobody in that room who matched the name (or the player is in the void)
        pc = self.world.get_player(target_name)
        if not pc:
            self.pc.update_output('"%s" doesn\'t exist. You\'ll have to tell someone else.' % target_name)
        else:
            self.tell_msg(pc, message)
    
    def tell_msg(self, target_char, message):
        """Tell a target_character a message.
        target_char - the character object to be "telled"
        message - the message to be passed along.
        """
        if target_char.is_npc():
            # TODO: dispatch a 'tell' notification to this npc (the 'tell'
            # npc event hasn't been written as of this comment)
            pass
        self.pc.update_output('You tell %s, "%s"' % (target_char.fancy_name(), message))
        target_char.update_output('%s tells you, "%s"' % (self.pc.fancy_name(), message))
    

command_list.register(Tell, ['tell', 'ask'])
command_help.register(Tell.help, ['tell', 'ask'])

class ChangePassword(BaseCommand):
    """Allow the player to change their password in-game."""
    help = (
    """Password (Command)
The Password command lets you change your password.
\nUSAGE:
  passwd
    """
    )
    def execute(self):
        if self.pc.mode:
            self.pc.last_mode = self.pc.mode
        self.pc.set_mode('passwd')
    

command_list.register(ChangePassword, ['password', 'passwd'])
command_help.register(ChangePassword.help, ['change password', 'passwd', 'password', 'set password'])

class Commands(BaseCommand):
    """Spit out a list of basic commands."""
    help = (
    """<title>Commands (Basic Commands)</title>
Commands are how players interact with the game; in fact, you've just used the
Help command in order to call up this help page (fancy!). A command is a word
(usually a verb) that represents an action you want to do, and is sometimes
followed by one or more words that clarify how that action is being done, or who
that action is being done to.
\n<b>USAGE:</b>
The help pages for commands all come with a USAGE section that explain the
syntax of a command. For example, the USAGE section for the Tell command looks
like this:
  <b>tell <person-name> <message></b>
The angle brackets (<>) mean that the word inside them is a place-holder. In the
Tell example above, I would want to replace <person-name> with the name of the
person I want to send a message to, and <message> with the message I want to
send. Some commands have optional words, like the USAGE for the Look command:
  <b>look [[at] <person-name>]</b>
Anything enclosed in square brackets ([]) is optional. In the example above,
both the words "at" and "<person-name>" are optional. I could type any of the
following and the Look command would work:
  look          (this would make me look at the room by default)
  look brian    (this would make me look at the character Brian)
  look at brian (this would also make me look at the character Brian)
    """
    )
    def execute(self):
        # TODO: This should be cleaned up so it's not just a horrible long list.
        # also, we should probably throw emotes out of this list since they don't 
        # add real actions
        l = 'Type "help <command-name>" for help on that particular command.\n' +\
            'Type "help commands" for help on commands in general.\n' +\
            ('-' * 50) + '\nBasic Commands (some commands may be aliases of another):\n'
        coms = []
        for alias, cmd in command_list.commands.items():
            if cmd.required_permissions & PLAYER:
                coms.append(alias)
        l += '\n'.join(coms)
        self.pc.update_output(l)
    

command_list.register(Commands, ['command', 'commands'])
command_help.register(Commands.help, ['command', 'commands'])

class Buy(BaseCommand):
    help = (
    """<title>Buy (Command)</title>
The Buy command allows you to purchase items from merchants (provided you have
enough money to do so). Money in %s comes in the form of %s, 
and you can check how much you have by using the Inventory or Me commands.
\nUSAGE:
To get a list of items a merchant is selling:
  buy [list]
To buy an item from a merchant:
  buy <item-keyword> [from <merchant-name>]
    """ % (GAME_NAME, CURRENCY)
    )
    def execute(self):
        if not self.pc.location:
            self.pc.update_output('There aren\'t any merchants in the void.')
            return
        # No arguments, or list aliases, display inventory
        if (not self.args) or (self.args == 'list'):
            try:
                merchant = self.verify_merchant(None)
            except SaleFail as e:
                self.pc.update_output(str(e))
            else:
                self.pc.update_output(merchant.ai_packs['merchant'].player_sale_list())
            return
        # transaction handling of buy
        exp = r'(?P<item>.+?)([ ]+from[ ]+(?P<merchant>\w+))?$'
        match = re.match(exp, self.args, re.I)
        if not match:
            self.pc.update_output('Try "help buy" for help on buying items.')
            return
        item_name, merchant_name = match.group('item', 'merchant')
        try:
            merchant = self.verify_merchant(merchant_name)
            item, price = self.verify_item(item_name, merchant)
        except SaleFail as e:
            self.pc.update_output(str(e))
        else:
            self.pc.currency -= price
            self.pc.save()
            self.pc.item_add(item)
            self.pc.update_output('You buy %s from %s for %s %s.' % (item.name,
                                            merchant.name, str(price), CURRENCY))
            self.pc.location.tell_room('%s buys %s from %s.' % (self.pc.fancy_name(),
                                                    item.name, merchant.name),
                                       [self.pc.name])
    
    def verify_item(self, item_name, merchant):
        item_n_price = merchant.ai_packs['merchant'].get_item(item_name)
        if not item_n_price:
            raise SaleFail('%s isn\'t selling any %s.' % (merchant.name, item_name))
        if self.pc.currency < item_n_price[1]:
            self.world.log.debug('pc: %s,%s item: %s,%s' % (str(self.pc.currency),
                                                            str(type(self.pc.currency)),
                                                            str(item_n_price[1]),
                                                            str(type(item_n_price[1]))))
            raise SaleFail('%s costs %s %s. You don\'t have enough %s.' %\
                           (item_n_price[0].name.capitalize(),
                            str(item_n_price[1]), CURRENCY, CURRENCY))
        # Make sure we create a new game item from the merchant's prototype
        item = item_n_price[0].load()
        return [item, item_n_price[1]]
    
    def verify_merchant(self, merchant_name):
        """Return a merchant if there is a valid one, """
        # If the player specified a merchant, try to grab that one
        if merchant_name:
            merchant = self.pc.location.get_npc_by_kw(merchant_name)
            if not merchant:
                raise SaleFail('%s isn\'t here.' % merchant_name)
            elif not merchant.has_ai('merchant'):
                raise SaleFail('%s isn\'t a merchant.' % (merchant.name))
            else:
                return merchant
        # if they didn't list a merchant, grab the first npc merchant you 
        # can find in the room
        else:
            merchant = None
            for npc in self.pc.location.npcs:
                if npc.has_ai('merchant'):
                    merchant = npc
                    break
            if not merchant:
                raise SaleFail('There aren\'t any merchants here to buy from.')
            else:
                return merchant
    

command_list.register(Buy, ['buy'])
command_help.register(Buy.help, ['buy'])

class Sell(BaseCommand):
    help = (
    """<title>Sell (Command)</title>
The Sell command allows a player to sell an item to a merchant. Keep in mind
that not all merchants buys all types of items!
\nUSAGE:
To sell an item:
  sell <item-keyword> [to <merchant-name>]
If you would like to see how much your item is worth to a merchant
before you sell it:
  show <item-keyword> [to <merchant-name>]
    """
    )
    def execute(self):
        if not self.args:
            self.pc.update_output('Sell what? Try "help sell" for help on sale transactions.')
            return
        if not self.pc.location:
            self.pc.update_output('There aren\'t any merchants in the void.')
            return
        #<item> [to <merchant>]
        exp = r'(?P<item>.+?)([ ]+to[ ]+(?P<merchant>\w+))?$'
        match = re.match(exp, self.args, re.I)
        if not match:
            self.pc.update_output('Try "help sell" for help on sale transactions.')
            return
        item_name, merchant_name = match.group('item', 'merchant')
        try:
            item = self.verify_item(item_name)
            merchant = self.verify_merchant(merchant_name)
        except SaleFail as e:
            self.pc.update_output(str(e))
            return
        else:
            if not merchant.ai_packs['merchant'].will_buy(item):
                merchant.perform('tell %s %s' % (self.pc.name,
                                 merchant.ai_packs['merchant'].tell_buy_types()))
                return
            # calculate sale price
            sale_price = int((item.base_value * merchant.ai_packs['merchant'].markup) + 0.5) or 1
            if self.alias in ['show', 'appraise']:
                merchant.perform('tell %s I\'ll give you %s %s for %s.' % (self.pc.fancy_name(),
                                 str(sale_price), CURRENCY, item.name))
                # self.pc.update_output('%s is worth %s %s to %s.' % (item.name.capitalize(),
                #                                                     str(sale_price),
                #                                                     CURRENCY,
                #                                                     merchant.name))
                return
            self.pc.item_remove(item)
            # Just destroy the item for now -- maybe later we'll have merchants resell
            # player-sold items later
            item.destruct()
            self.pc.currency += sale_price
            self.pc.save()
            self.pc.update_output('You sell %s for %s %s to %s.' % (item.name,
                                                              str(sale_price),
                                                              CURRENCY, 
                                                              merchant.name))
            self.pc.location.tell_room('%s sells %s to %s.' % (self.pc.fancy_name(),
                                                               item.name,
                                                               merchant.name),
                                       [self.pc.name])
    
    def verify_item(self, item_name):
        item = self.pc.check_inv_for_keyword(item_name)
        if not item:
            raise SaleFail('You don\'t have "%s".' % item_name)
        return item
    
    def verify_merchant(self, merchant_name):
        """Return a merchant if there is a valid one, """
        # If the player specified a merchant, try to grab that one
        if merchant_name:
            merchant = self.pc.location.get_npc_by_kw(merchant_name)
            if not merchant:
                raise SaleFail('%s isn\'t here.' % merchant_name)
            elif not merchant.has_ai('merchant'):
                raise SaleFail('%s isn\'t a merchant.' % (merchant.name))
            else:
                return merchant
        # if they didn't list a merchant, grab the first npc merchant you 
        # can find in the room
        else:
            merchant = None
            for npc in self.pc.location.npcs:
                if npc.has_ai('merchant'):
                    merchant = npc
                    break
            if not merchant:
                raise SaleFail('There aren\'t any merchants here to sell to.')
            else:
                return merchant
    

command_list.register(Sell, ['sell', 'show', 'appraise'])
command_help.register(Sell.help, ['sell', 'show', 'appraise'])


class Log(BaseCommand):
    required_permissions = BUILDER | DM | ADMIN
    help = (
    """<title>Log (BuildCommand)</title>
Npcs receive the same feedback for preforming actions (commands) as a player
character, but since they can't read, their feedback gets accumulated in an
action log rather than being output to a screen. The Log command allows you to
read the action log (and memory) of an npc to help you debug scripting errors.
\nUSAGE:
  log <npc-name>
You must be in the same room as an npc to log it.
    """
    )
    def execute(self):
        if not self.args:
            self.pc.update_output('Type "help log" for help with this command.')
            return
        if not self.pc.location:
            self.pc.update_output('There aren\'t any npcs in the void to log.')
            return
        npc = self.pc.location.get_npc_by_kw(self.args.lower().strip())
        if not npc:
            self.pc.update_output('That npc doesn\'t exist.')
            return
        string = (' Log for %s ' % npc.name).center(50, '-') + '\n'
        perms = ', '.join(get_permission_names(npc.permissions))
        if npc.remember:
            string += 'REMEMBERS: '
            string += ', '.join(npc.remember) + '\n'
        else:
            string += 'REMEMBERS: This npc doesn\'t remember any players.\n'
        string += 'PERMISSIONS: ' + perms + '\n'
        string += 'ACTION LOG:\n'
        if npc.actionq:
            string += '\n'.join([a.strip('\n').strip('\r') for a in npc.actionq])
        else:
            string += 'Action log is empty.'
        string += '\n' + ('-' * 50)
        self.pc.update_output(string)
    

command_list.register(Log, ['log'])
command_help.register(Log.help, ['log'])


# **************** Command Specific Exceptions *******************
class SaleFail(Exception):
    """Throw this exception if there's an error in the player's sale
    process.
    """
    pass

# **************** Extra Command-related Help pages *******************
command_help.register(("<title>TextEditMode (Mode)</title>"
"""TextEditMode is a special mode for editing large amounts of text, such as
room or character descriptions. TextEditMode lets you enter text
(line-by-line), until you are finished, letting you replace, delete, and
insert lines as you go. Help for TextEditMode commands can be accessed by
typing @help while in TextEditMode.
"""
), ['TextEditMode', 'text edit mode', 'textedit', 'text edit'])

command_help.register(("<title>Newbie Help</title>"
"""Welcome! You've successfully invoked our help system on the "newbie" topic.
Anytime you need help with something, just type "help" and then the name of the
topic you want help with. Try it on the topics below to expand your knowledge of
how to play the game:
\nSee "<b>help commands</b>" for a tutorial on what to type and how to interact
with the game.
\nSee "<b>help go</b>" for a tutorial on how to move around and explore
the game.
\nSee "<b>help talking</b>" for a tutorial on how to communicate with other
players in the game.
\nSee "<b>help mud</b>" to get a better idea of what kind of game a MUD is.
\nHappy MUDding!
"""
), ['newbie', 'newb'])

command_help.register(("<title>Communication</title>"
"""There are lots of ways to get your message across, depending on who you want
to hear it.
<b>Chat</b>
The Chat command will broadcast your message to every player in the game (unless
they have their chat channel turned off). It's meant solely for discussion
between players, and topics may not be relevant to the game. For even more help
with the chat command, type "help chat".
Tutorial - try typing:
  chat I'm testing out the chat command!
\n<b>Say</b>
The Say command will only broadcast your message to people in the same room as
you. Both players and npcs (non-player-characters) can hear a message you send with
the Say command. Type "help say" for help with this command.
Tutorial - try typing:
  say I'm testing out the say command!
\n<b>Tell</b>
The tell command will send a private message to a specific person. It only works
if the player you're trying to Tell is online, or the npc you're trying to tell
is in the same room as you.
Try telling someone near you hello! (just replace <person> below with the name
of the person you want to tell):
  tell <person> Hello!
"""
), ['talking', 'talk', 'communication'])

