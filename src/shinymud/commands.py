from shinymud.models.area import Area
from shinymud.models.room import Room
from shinymud.models.item import Item
from shinymud.models.npc import Npc
from shinymud.world import World
import re
import logging

class CommandRegister(object):
    
    def __init__(self):
        self.commands = {}
    
    def __getitem__(self, key):
        return self.commands.get(key)
    
    def register(self, func, aliases):
        for alias in aliases:
            self.commands[alias] = func
    
# ************************ GENERIC COMMANDS ************************
command_list = CommandRegister()

class BaseCommand(object):
    
    def __init__(self, user, args):
        self.args = args
        self.user = user
        self.world = World.get_world()
        self.log = logging.getLogger('Command')
    
    def personalize(self, actor, target, message):
        """Personalize an action message for a user.
            
        This function replaces certain keywords in generic messages with 
        user-specific data to make the message more personal. Below is a list
        of the keywords that will be replaced if they are found in the message:
            
        #actor - replaced with the name of the actor (user commiting the action)
        #me - replaced with the gender-specific pronoun of the actor
        #my - replace with the gender-specific possessve-pronoun of the actor
            
        #target - replace with the name of the target (user being acted upon)
        #you - replace with the gender-specific pronoun of the target
        #yours - replace with a gender-specific possessive-pronoun of the target
        """
        
        possessive_pronouns = {'female': 'hers', 'male': 'his', 'neutral': 'its'}
        pronouns = {'female': 'her', 'male': 'him', 'neutral': 'it'}
        
        message = message.replace('#actor', actor.get_fancy_name())
        message = message.replace('#me', pronouns.get(actor.gender))
        message = message.replace('#my', possessive_pronouns.get(actor.gender))
        
        # We should always have an actor, but we don't always have a target.
        # Expect them to be able to pass None for the target
        if target:
            message = message.replace('#target', target.get_fancy_name())
            message = message.replace('#your', possessive_pronouns.get(actor.gender))
            message = message.replace('#you', pronouns.get(target.gender))
        
        return message
    
    
class Quit(BaseCommand):
    def execute(self):
        self.user.quit_flag = True
    

command_list.register(Quit, ['quit', 'exit'])

class WorldEcho(BaseCommand):
    """Echoes a message to everyone in the world.
    args:
        args = message to be sent to every user in the wold.
    """
    def execute(self):
        # This should definitely require admin privileges in the future.
        for person in self.world.user_list:
            self.world.user_list[person].update_output(self.args + '\n')
    

command_list.register(WorldEcho, ['wecho', 'worldecho'])

class Apocalypse(BaseCommand):
    """Ends the world. The server gets shutdown."""
    def execute(self):
        # This should definitely require admin privileges in the future.
        message = "%s has stopped the world from turning. Goodbye." % self.user.get_fancy_name()
        WorldEcho(self.user, message).execute()
        
        self.world.shutdown_flag = True
    

command_list.register(Apocalypse, ['apocalypse', 'die'])

class Chat(BaseCommand):
    """Sends a message to every user on the chat channel."""
    def execute(self):
        if not self.user.channels['chat']:
            self.user.channels['chat'] = True
            self.user.update_output('Your chat channel has been turned on.\n')
        message = '%s chats, "%s"\n' % (self.user.get_fancy_name(), self.args)
        for person in self.world.user_list:
            if self.world.user_list[person].channels['chat']:
                self.world.user_list[person].update_output(message)
    

command_list.register(Chat, ['chat', 'c'])

class Channel(BaseCommand):
    """Toggles communication channels on and off."""
    def execute(self):
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

class Build(BaseCommand):
    """Activate or deactivate build mode."""
    def execute(self):
        if self.args == 'exit':
            self.user.set_mode('normal')
            self.user.update_output('Exiting BuildMode.\n')
        else:
            self.user.set_mode('build')
            self.user.update_output('Entering BuildMode.\n')

command_list.register(Build, ['build'])

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
            return 'You see a dark void.\n'
    
    def look_in_room(self, keyword):
        if self.user.location:
            obj = self.user.location.check_for_keyword(keyword)
            if obj:
                return "You look at %s:\n%s\n" % (obj.name, obj.description)
        return None
    
    def look_in_inventory(self, keyword):
        item = self.user.check_inv_for_keyword(keyword)
        if item:
            return "You look at %s:\n%s\n" % (item.name, item.description)
        return None
    

command_list.register(Look, ['look'])

class Goto(BaseCommand):
    """Go to a location."""
    def execute(self):
        if self.args:
            exp = r'((room)?([ ]?(?P<room_id>\d+))(([ ]+in)?([ ]+area)?([ ]+(?P<area>\w+)))?)|(?P<name>\w+)'
            match = re.match(exp, self.args)
            message = 'Type "help goto" for help with this command.\n'
            if match:
                name, area_name, room = match.group('name', 'area', 'room_id')
                if name:
                    # go to the same room that user is in
                    per = self.world.user_list.get(name)
                    if per:
                        if per.location:
                            self.user.go(self.world.user_list.get(name).location)
                        else:
                            self.user.update_output('You can\'t reach %s.\n' % per.get_fancy_name())
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
                            self.user.go(room)
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
                        self.user.go(go_exit.to_room)
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
                message = '%s says, "%s"\n' % (self.user.get_fancy_name(), self.args)
                self.user.location.tell_room(message)
            else:
                self.user.update_output('Your words are sucked into the void.\n')
        else:
            self.user.update_output('Say what?\n')
    

command_list.register(Say, ['say'])

class Load(BaseCommand):
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
        self.user.update_output('Npc\'s don\'t exist yet.\n')
    
    def load_item(self, item_id, item_area):
        """Load an item into the user's inventory."""
        prototype = item_area.get_item(item_id)
        if prototype:
            item = prototype.load_item()
            self.user.item_add(item)
            self.user.update_output('You summon %s into the world.\n' % item.name)
            if self.user.location:
                self.user.location.tell_room('%s summons %s into the world.\n' % (self.user.get_fancy_name(), item.name), 
                                                                                self.user.name)
        else:
            self.user.update_output('That item doesn\'t exist.\n')
    

command_list.register(Load, ['load'])

class Inventory(BaseCommand):
    """Show the user their inventory."""
    def execute(self):
        if not self.user.inventory:
            self.user.update_output('Your inventory is empty.\n')
        else:
            i = 'Your inventory consists of:\n'
            for item in self.user.inventory:
                i += item.name + '\n'
            self.user.update_output(i)

command_list.register(Inventory, ['i', 'inventory'])

class Give(BaseCommand):
    """Give an item to another player."""
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
            item = self.user.check_inv_for_keyword(thing)
            if not givee:
                self.user.update_output('%s isn\'t here.\n' % person.capitalize())
            elif not item:
                self.user.update_output('You don\'t have %s.\n' % thing)
            else:
                self.user.item_remove(item)
                givee.item_add(item)
                self.user.update_output('You give %s to %s.\n' % (item.name, givee.get_fancy_name()))
                givee.update_output('%s gives you %s.\n' % (self.user.get_fancy_name(), item.name))
                self.user.location.tell_room('%s gives %s to %s\n.' % (self.user.get_fancy_name(),
                                                                      item.name,
                                                                      givee.get_fancy_name()),
                                            [self.user.name, givee.name])
    

command_list.register(Give, ['give'])

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
                    self.user.location.tell_room('%s drops %s.\n' % (self.user.get_fancy_name(), 
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
        elif not self.user.location:
            self.user.update_output('Only cold blackness exists in the void. It\'s not the sort of thing you can take.\n')
        else:
            item = self.user.location.check_for_keyword(self.args)
            if item:
                self.user.location.item_remove(item)
                self.user.item_add(item)
                self.user.update_output('You get %s.\n' % item.name)
                self.user.location.tell_room('%s gets %s\n' % (self.user.get_fancy_name(), item.name), 
                                                             [self.user.name])
            else:
                self.user.update_output('That doesn\'t exist.\n')
                
    

command_list.register(Get, ['get', 'take'])

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
                obj = self.user.location.get_item(self.args)
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
                        Drop(self.user, self.args).execute()
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
            self.user.update_output('Nothing happened.\n')

command_list.register(Enter, ['enter'])

class Purge(BaseCommand):
    """Purge all of the items and npc's in the room."""
    def execute(self):
        # TODO: Finish this function
        if not self.args:
            # If they specified nothing, just purge the room
            if self.user.location:
                pass
            else:
                self.user.update_output('You\'re in a void, there\'s nothing to purge.\n')
        elif self.args in ['i', 'inventory']:
            # Purge their inventory!
            for item in self.user.inventory:
                pass
            self.user.update_output('Your inventory has been purged.\n')
        else:
            self.user.update_output('Someone didn\'t endow me with the functionality to purge that for you.\n')
    


# ************************ BUILD COMMANDS ************************
# TODO: Each list of commands should probably be in their own file for extensibility's sake
build_list = CommandRegister()

class Create(BaseCommand):
    """Create a new item, npc, or area."""
    def execute(self):
        object_types = ['item', 'npc', 'room']
        if not self.args:
            self.user.update_output('What do you want to create?\n')
        else:
            args = self.args.lower().split()
            if args[0] == 'area':
                # Areas need to be created with a name argument -- make sure the user has passed one
                if not len(args) > 1:
                    self.user.update_output('You can\'t create a new area without a name.\n')
                else:
                    new_area = Area.create(args[1])
                    if type(new_area) == str:
                        self.user.update_output(new_area)
                    else:
                        self.user.mode.edit_area = new_area
                        new_area.add_builder(self.user.name)
                        self.user.mode.edit_object = None
                        self.user.update_output('New area "%s" created.\n' % new_area.name)
            
            elif args[0] in object_types:
                if not self.user.mode.edit_area:
                    self.user.update_output('You need to be editing an area first.\n')
                else:
                    new_obj = getattr(self.user.mode.edit_area, 'new_' + args[0])()
                    if type(new_obj) == str:
                        self.user.update_output(new_obj)
                    else:
                        self.user.mode.edit_object = new_obj
                        self.user.update_output('New %s number %s created.\n' % (args[0], 
                                                                                 new_obj.id))
            else:
                self.user.update_output('You can\'t create that.\n')
    

build_list.register(Create, ['create', 'new'])

class Edit(BaseCommand):
    """Edit an area, object, npc, or room."""
    def execute(self):
        args = self.args.lower().split()
        if len(args) < 2:
            self.user.update_output('Type "help edit" to get help using this command.\n')
        else:
            if args[0] == 'area':
                if args[1] in self.world.areas.keys():
                    self.user.mode.edit_area = self.world.areas[args[1]]
                    # Make sure to clear any objects they were working on in the old area
                    self.user.mode.edit_object = None
                    self.user.update_output('Now editing area "%s".\n' % args[1])
                else:
                    self.user.update_output('That area doesn\'t exist. You should create it first.\n')
            elif args[0] in ['room', 'npc', 'item']:
                if self.user.mode.edit_area:
                    obj = getattr(self.user.mode.edit_area, args[0] + 's').get(args[1])
                    if obj:
                        self.user.mode.edit_object = obj
                        self.user.update_output(str(self.user.mode.edit_object))
                    else:
                        self.user.update_output('That %s doesn\'t exist. Type "list %ss" to see all the %ss in your area.\n' % (args[0], args[0], args[0])) 
                else:
                    self.user.update_output('You need to be editing an area before you can edit its contents.\n')
            else:
                self.user.update_output('You can\'t edit that.\n')
    

build_list.register(Edit, ['edit'])

class List(BaseCommand):
    """List allows a builder to "see" all of the areas and objects in the world.
        
    More specifically, list either returns a string representation of a group of objects/areas, 
    or a the attributes of a specific object/area, filtered by the criteria passed by the user. 
    An object-type is one of the following: item, npc, or room.
        
    * With no arguments passed, list will return the attributes of the object currently being edited.
    * If just an object-type is passed, list will return a list of ALL the objects of that type in 
        the working area.
    * If an object-type and an area name are passed, list will return a list of ALL objects 
        of that type in the specified area.
    * If an object-type and a specific id are passed, list will return a list of attributes for 
        that specific object in the working area.
    * If an object-type, a specific id, and an area name are passed, list will return a list of
        attributes for that specific object in the specified area.
        
    examples: 
    "list room 4 in area bilbos_shire" will show the attributes of room number 4 in the 
    area bilbos_shire, regardless if that area or that room are being currently edited.
    "list items" will list all of the items that exist in the working area.
    
    """
    
    def execute(self):
        message = 'Type "help list" to get help using this command.\n'
        if not self.args:
            # The user didn't give a specific item to be listed; show them the current one,
            # if there is one
            if self.user.mode.edit_object:
                message = str(self.user.mode.edit_object)
            elif self.user.mode.edit_area:
                message = str(self.user.mode.edit_area)
            else:
                message = 'You\'re not editing anything right now.\n'
        else:
            # The user wants to see the details of some other object than the one they're editing.
            exp = r'(?P<func>(area)|(npc)|(item)|(room))s?([ ]+(?P<id>\d+))?([ ]+in)?([ ]*area)?([ ]+(?P<area_name>\w+))?'
            match = re.match(exp, self.args, re.I)
            if not match:
                message = 'You can\'t list that.\n'
            else:
                func, obj_id, area_name = match.group('func', 'id', 'area_name')
                if func == 'area':
                    message = self.list_area(obj_id, area_name)
                else:
                    message = self.list_object(func, obj_id, area_name)
        self.user.update_output(message)
        
    def list_area(self, obj_id, area_name):
        if area_name:
            # The user wants to know the details of a specific area
            area = self.world.get_area(area_name)
            if area:
                return str(area)
            else:
                return 'That area doesn\'t exist.\n'
        else:
            # No area_name was passed, therefore we want to give the user a
            # list of all the areas in the world
            return self.world.list_areas()
    
    def list_object(self, obj_type, obj_id, area_name):
        
        area = self.world.get_area(area_name) or self.user.mode.edit_area
        if not area:
            return 'What area do you want to list %ss for?\n' % obj_type
        
        if obj_id:
            # A specific id was passed -- if an object of the specified type with that
            # id exists, show the user the attributes for that particular object.
            obj = getattr(area, obj_type + 's').get(obj_id)
            if obj:
                return str(obj)
            else:
                return '%s "%s" doesn\'t exist in area "%s".' % (obj_type.capitalize(),
                                                                 obj_id, area.name)
        else:
            # Since we got this far, obj_type will be equal to "npc", "room", or "item",
            # which means the following will call one of these three functions:
            # list_rooms(), list_items(), or list_npcs(). Since the user didn't pass us a specific
            # id, they should get a list of all of the objects of the type they specified
            # (for the given area they specified).
            return getattr(area, "list_" + obj_type + "s")()
    

build_list.register(List, ['list'])

class Set(BaseCommand):
    def execute(self):
        obj = self.user.mode.edit_object or self.user.mode.edit_area
        if not obj:
            self.user.update_output('You must be editing something to set its attributes.\n')
        elif not self.args:
            self.user.update_output('What do you want to set?\n')
        else:
            match = re.match(r'\s*(\w+)([ ](.+))?$', self.args, re.I)
            if not match:
                message = 'Type "help set" for help setting attributes.\n'
            else:
                func, _, arg = match.groups()
                message = 'You can\'t set that.\n'
                if hasattr(obj, 'set_' + func):
                    message = (getattr(obj, 'set_' + func)(arg))
                
                elif obj.__class__.__name__ == 'Item':
                    # If we didn't find the set function in the object's native set functions,
                    # but the object is of type Item, then we should search the set functions
                    # of that item's item_types (if it has any)
                    for iType in obj.item_types.values():
                        if hasattr(iType, 'set_' + func):
                            message = getattr(iType, 'set_' + func)(arg)
                            break
                self.user.update_output(message)
    

build_list.register(Set, ['set'])

class Link(BaseCommand):
    """Link two room objects together through their exits."""
    def execute(self):
        this_room = self.user.mode.edit_object
        if this_room and (this_room.__class__.__name__ == 'Room'):
            exp = r'(?P<direct>\w+)([ ]+(?P<area>\w+)([ ]+(?P<room>\d+)))?'
            match = re.match(exp, self.args, re.I)
            if match:
                direction, area, room = match.group('direct', 'area', 'room')
                if direction in this_room.exits:
                    if area and room:
                        link_area = self.world.get_area(area)
                        link_room = link_area.get_room(room)
                        if link_area and link_room:
                            self.user.update_output(this_room.link_exits(direction, link_room))
                        else:
                            self.user.update_output('That area/room combo doesn\'t exist.\n')
                    else:
                        new_room = this_room.area.new_room()
                        self.user.update_output('Room %s created.\n' % new_room.id)
                        self.user.update_output(this_room.link_exits(direction, new_room))
                else:
                    self.user.update_output('That direction doesn\'t exist.\n')
            else:
                self.user.update_output('Type "help link" for help on this command.\n')
        else:
            self.user.update_output('You have to be editing a room to link it to something.\n')
    

build_list.register(Link, ['link'])

class Add(BaseCommand):
    def execute(self):
        obj = self.user.mode.edit_object or self.user.mode.edit_area
        if not obj:
            self.user.update_output('You must be editing something to add attributes.\n')
        elif not self.args:
            self.user.update_output('What do you want to add?\n')
        else:
            func, _, arg = re.match(r'\s*(\w+)([ ](.+))?$', self.args, re.I).groups()
            if hasattr(obj, 'add_' + func):
                self.user.update_output(getattr(obj, 'add_' + func)(arg))
            else:
                self.user.update_output('You can\'t add that.\n')
    

build_list.register(Add, ['add'])

class Remove(BaseCommand):
    def execute(self):
        obj = self.user.mode.edit_object or self.user.mode.edit_area
        if not obj:
            self.user.update_output('You must be editing something to remove attributes.\n')
        elif not self.args:
            self.user.update_output('What do you want to remove?\n')
        else:
            func, _, arg = re.match(r'\s*(\w+)([ ](.+))?$', self.args, re.I).groups()
            if hasattr(obj, 'remove_' + func):
                self.user.update_output(getattr(obj, 'remove_' + func)(arg))
            else:
                self.user.update_output('You can\'t remove that.\n')
    

build_list.register(Remove, ['remove'])

class Destroy(BaseCommand):
    """Destroy an area, room, npc, or item, permanently removing it from the system.
    
    NOTE: Player avatars should not be able to be deleted using this."""
    def execute(self):
        message = 'Type "help destroy" to get help using this command.\n'
        if not self.args:
                # Don't ever let them destroy something if they haven't been specific about 
                # what they want destroyed (i.e, they haven't given us any arguments)
                message = self.user.update_output('You should be more specific. This command could really cause some damage.\n')
        else:
            exp = r'(?P<func>(area)|(npc)|(item)|(room))([ ]+(?P<id>\d+))?([ ]+in)?([ ]*area)?([ ]+(?P<area_name>\w+))?'
            match = re.match(exp, self.args, re.I)
            message = 'Type "help destroy" to get help using this command.\n'
            if match:
                func, obj_id, area_name = match.group('func', 'id', 'area_name')
                area = self.world.get_area(area_name) or self.user.mode.edit_area
                if func == 'area':
                    message = self.world.destroy_area(area)
                elif area and hasattr(area, 'destroy_' + func):
                    message = getattr(area, 'destroy_' + func)(obj_id)
                else:
                    message = 'You can\'t destroy something that does\'t exist.\n'
                # The destroy function will set the id of whatever it deleted to None
                # so that any other objects with references will know they should terminate
                # their reference. If the user destroyed the object they're working on,
                # make sure that we clear it from their edit_object, and therefore ther prompt 
                # so they don't try and edit it again before it gets wiped.
                if self.user.mode.edit_object and self.user.mode.edit_object.id == None:
                    self.user.mode.edit_object = None
        self.user.update_output(message)
    

build_list.register(Destroy, ['destroy'])