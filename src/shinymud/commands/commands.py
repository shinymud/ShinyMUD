from shinymud.models.area import Area
from shinymud.models.room import Room
from shinymud.models.item import Item, SLOT_TYPES
from shinymud.models.npc import Npc
from shinymud.lib.world import World
from shinymud.data.config import *
from shinymud.commands.emotes import *
from shinymud.commands import *
import re
import logging
   
# ************************ GENERIC COMMANDS ************************
command_list = CommandRegister()

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

class Apocalypse(BaseCommand):
    """Ends the world. The server gets shutdown."""
    required_permissions = GOD
    def execute(self):
        # This should definitely require admin privileges in the future.
        message = "%s has stopped the world from turning. Goodbye." % self.user.fancy_name()
        self.world.tell_users(message)
        self.world.shutdown_flag = True
    

command_list.register(Apocalypse, ['apocalypse', 'die'])

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
  build
To exit BuildMode:
  build exit
\nFor a list of BuildCommands, see "help build commands".
"""
    )
    def execute(self):
        if self.args == 'exit':
            self.user.set_mode('normal')
            self.user.update_output('Exiting BuildMode.\n')
        else:
            self.user.set_mode('build')
            self.user.update_output('Entering BuildMode.\n')

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
    

command_list.register(Look, ['look'])

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
        if self.args:
            exp = r'((room)?([ ]?(?P<room_id>\d+))(([ ]+in)?([ ]+area)?([ ]+(?P<area>\w+)))?)|(?P<name>\w+)'
            match = re.match(exp, self.args)
            message = 'Type "help goto" for help with this command.\n'
            if match:
                name, area_name, room = match.group('name', 'area', 'room_id')
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
                elif room:
                    # See if they specified an area -- if they did, go there
                    area = self.world.get_area(area_name)
                    # if they didn't, lets try to take them to that room number in the area
                    # they are currently in
                    if not area and self.user.location:
                        area = self.user.location.area
                    if area:
                        room = area.get_room(room)
                        if room:
                            self.user.go(room, self.user.goto_appear, 
                                         self.user.goto_disappear)
                        else:
                            self.user.update_output('That room doesn\'t exist.\n')
                    else:
                        self.user.update_output(message)
                else:
                    self.user.update_output('You can\'t get there.\n')
            else:
                self.user.update_output(message)
        else:
            self.user.update_output('Where did you want to go?\n')
    

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
                self.user.location.tell_room(message)
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
            self.user.location.npc_add(npc)
            self.user.update_output('You summon %s into the world.\n' % npc.name)
        else:
            self.user.update_output('That npc doesn\'t exist.')
    
    def load_item(self, item_id, item_area):
        """Load an item into the user's inventory."""
        prototype = item_area.get_item(item_id)
        if prototype:
            item = prototype.load()
            self.user.item_add(item)
            self.user.update_output('You summon %s into the world.\n' % item.name)
            if self.user.location:
                self.user.location.tell_room('%s summons %s into the world.\n' % (self.user.fancy_name(), item.name), 
                                                                                self.user.name)
        else:
            self.user.update_output('That item doesn\'t exist.\n')
    

command_list.register(Load, ['load'])
command_help.register(Load.help, ['load'])

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
            givee = self.user.location.get_user_by_kw(person) or self.user.location.get_npc_by_kw(person)
            item = self.user.check_inv_for_keyword(thing)
            if not givee:
                self.user.update_output('%s isn\'t here.' % person.capitalize())
            elif not item:
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
    """Get an item that exists in the user's current room."""
    def execute(self):
        if not self.args:
            self.user.update_output('What do you want to get?\n')
        else:
            exp = r'((?P<target_kw>(\w|[ ])+)([ ]+from)([ ]+(?P<source_kw>(\w|[ ])+)))|((?P<item_kw>(\w|[ ])+))'
            match = re.match(exp, self.args, re.I)
            if not match:
                self.user.update_output('Type "help get" for help with this command.\n')
                return
            target_kw, source_kw, item_kw = match.group('target_kw', 'source_kw', 'item_kw')
            if source_kw:
                source = self.user.location.check_for_keyword(source_kw) or \
                         self.user.check_inv_for_keyword(source_kw)
                if not source:
                    self.user.update_output('"%s" doesn\'t exist.\n' % source_kw)
                    return
                if not source.is_container():
                    self.user.update_output('That\'s not a container.\n')
                    return
                source = source.item_types.get('container')
                item = source.get_item_by_kw(target_kw)
            else:
                if not self.user.location:
                    self.user.update_output('Only cold blackness exists in the void. ' +\
                                            'It\'s not the sort of thing you can take.\n')
                    return
                source = self.user.location
                item = source.get_item_by_kw(item_kw)
            if item:
                if item.carryable or (self.user.permissions & GOD):
                    source.item_remove(item)
                    self.user.item_add(item)
                    self.user.update_output('You get %s.\n' % item.name)
                    if self.user.location:
                        if source_kw:
                            room_tell = '%s gets %s from %s.\n' % (self.user.fancy_name(), item.name,
                                                                   source.item.name)
                        else:
                            room_tell = '%s gets %s.\n' % (self.user.fancy_name(), item.name)
                        self.user.location.tell_room((room_tell), [self.user.name])
                else:
                    self.user.update_output('You can\'t take that.\n')
            else:
                self.user.update_output('That doesn\'t exist.\n')
                

command_list.register(Get, ['get', 'take'])

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
    def execute(self):
        persons = [name for name in self.world.user_list.keys() if (type(name) == str)]
        message = """Currently Online:\n______________________________________________\n"""
        for person in persons:
            message += person.capitalize() + '\n'
        message += "______________________________________________\n"
        self.user.update_output(message)
    

command_list.register(Who, ['who'])

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
                self.user.location.tell_room(self.personalize(self.user, None, portal.leave_message) + '\n', 
                                             [self.user.name])
            self.user.update_output(self.personalize(self.user, None, portal.entrance_message) + '\n')
            self.user.go(portal.location)
            self.user.location.tell_room(self.personalize(self.user, None, portal.emerge_message) + '\n', 
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
            for item in self.user.inventory:
                self.user.item_remove(item)
                item.destruct()
            self.user.update_output('Your inventory has been purged.\n')
        else:
            # Purge a specific npc or item based on keyword
            self.user.update_output('Someone didn\'t endow me with the functionality to purge that for you.\n')
    

command_list.register(Purge, ['purge'])
command_help.register(Purge.help, ['purge'])

class Areas(BaseCommand):
    def execute(self):
        """Give a list of areas in the world, as well as their level ranges."""
        the_areas = self.world.areas.keys()
        message = 'Area  |  Level Range\n______________________________________________\n'
        if not the_areas:
            message += 'Sorry, God has taken a day off. There are no areas yet.\n'
        for eachone in the_areas:
            message += eachone + '  |  ' + self.world.get_area(eachone).level_range + '\n'
        message += '______________________________________________\n'
        self.user.update_output(message)
        
  

command_list.register(Areas, ['areas'])

class Emote(BaseCommand):
    """Emote to another player or ones self. (slap them, cry hysterically, etc.)"""
    def execute(self):
        if not self.user.location:
            self.user.update_output('You try, but the action gets sucked into the void. The void apologizes.\n')
        else:
            emote_list = EMOTES[self.alias]
            if not self.args:                               #If victim is not specified
                victim = ''
                self.user.update_output(self.personalize(self.user, victim, emote_list[0]) + '\n')
                self.user.location.tell_room(self.personalize(self.user, victim, emote_list[1] + '\n'), [self.user.name])
            else:
                victim = self.user.location.get_user(self.args) #If victim is in room
                if (victim == self.user):
                    victim = ''
                    self.user.update_output(self.personalize(self.user, victim, emote_list[0]) + '\n')
                    self.user.location.tell_room(self.personalize(self.user, victim, emote_list[1] + '\n'), [self.user.name])
                elif victim:
                    emote_list = TARGETEMOTES[self.alias]
                    self.user.update_output(self.personalize(self.user, victim, emote_list[0]) + '\n')
                    victim.update_output(self.personalize(self.user, victim, emote_list[1]) + '\n')
                    self.user.location.tell_room(self.personalize(self.user, victim, emote_list[2] + '\n'),
                                                    [self.user.name, victim.name])
                else:
                    victim = self.world.get_user(self.args) #If victim is in world
                    if (victim):
                        message = 'From far away, '
                        self.user.update_output(message + self.personalize(self.user, victim, emote_list[0]) + '\n')
                        victim.update_output(message + self.personalize(self.user, victim, emote_list[1]) + '\n')
                    else:                                   #If victim is in neither
                        self.user.update_output('You don\'t see %s.\n' % self.args)
                

command_list.register(Emote, EMOTES.keys())

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
        user.update_output('%s has bestowed the authority of %s upon you!\n' % (self.user.fancy_name(), perm.upper()))
    

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
            self.user.update_output(self.help + '\n')
            return
        help = command_help[self.args]
        if help:
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
        # send the ANSI command to move the cursor up to the top of the
        # screen (I just put 1000 here as the number of columns to move up,
        # since once the cursor hits the top of the screen it stops and no
        # one will probably have a screen taller than 1000 columns :)
        self.user.update_output('\x1b[2J' + '\x1b[1000A')
    

command_list.register(Clear, ['clear'])
command_help.register(Clear.help, ['clear'])
