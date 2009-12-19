from models.area import Area
from shinymud.models.room import Room
from shinymud.world import World
import re

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
    """Look at a room, item, or npc."""
    def execute(self):
        if not self.args:
            self.look_room()
        else:
            self.user.update_output('You don\'t see that here.\n')
    
    def look_room(self):
        if self.user.location:
            message = self.user.look()
        else:
            message = 'You see a dark void.\n'
        self.user.update_output(message)
    

command_list.register(Look, ['look'])

class Goto(BaseCommand):
    """Go to a location."""
    def execute(self):
        if self.args:
            exp = r'((?P<area>\w+)[ ]+(?P<room>\d+))|(?P<name>\w+)'
            name, area, room = re.match(exp, self.args).group('name', 'area', 'room')
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
            elif area:
                # go to the room in the area specified.
                area = self.world.get_area(area)
                message = 'Type "help goto" for help with this command.\n'
                if area:
                    room = area.get_room(room)
                    if room:
                        self.user.go(room)
                    else:
                        self.user.update_output(message)
                else:
                    self.user.update_output(message)
            else:
                self.user.update_output('You can\'t get there.\n')
        else:
            self.user.update_output('Where did you want to go?\n')
    

command_list.register(Goto, ['goto'])

class Go(BaseCommand):
    """Go to the next room in the direction given."""
    def execute(self):
        if self.user.location:
            go_exit = self.user.location.exits.get(self.args)
            if go_exit:
                self.user.go(go_exit.to_room)
            else:
                self.user.update_output('You can\'t go that way.\n')
        else:
            self.user.update_output('You exist in a void; there is no where to go.\n')
    

command_list.register(Go, ['go'])

class Say(BaseCommand):
    """Echo a message from the user to the room that user is in."""
    def execute(self):
        if self.args:
            if self.user.location:
                message = '%s says, "%s"\n' % (self.user.get_fancy_name(), self.args)
                self.user.location.tell_room(message)
        else:
            self.user.update_output('Say what?\n')
    

command_list.register(Say, ['say'])
# ************************ BUILD COMMANDS ************************
# TODO: Each list of commands should probably be in their own file for extensibility's sake
build_list = CommandRegister()

class Create(BaseCommand):
    """Create a new item, npc, or area."""
    def execute(self):
        if not self.args:
            self.user.update_output('What do you want to create?\n')
        else:
            args = self.args.lower().split()
            if args[0] == 'area':
                # Areas need to be created with a name argument -- make sure the user has passed one
                if len(args) > 1 and args[1]:
                    new_area = Area.create(args[1])
                    if type(new_area) == str:
                        self.user.update_output(new_area)
                    else:
                        self.user.mode.edit_area = new_area
                        new_area.add_builder(self.user.name)
                        self.user.mode.edit_object = None
                        self.user.update_output('New area "%s" created.\n' % new_area.name)
                else:
                    self.user.update_output('You can\'t create a new area without a name.\n')
            elif args[0] == 'room':
                if not self.user.mode.edit_area:
                    self.user.update_output('You need to be editing an area first.\n')
                else:
                    new_room = Room.create(self.user.mode.edit_area)
                    if type(new_room) == str:
                        self.user.update_output(new_room)
                    else:
                        self.user.mode.edit_object = new_room
                        self.user.update_output('New room number %s created.\n' % new_room.id)
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
            elif args[0] == 'room':
                if self.user.mode.edit_area:
                    if args[1] in self.user.mode.edit_area.rooms.keys():
                        self.user.mode.edit_object = self.user.mode.edit_area.rooms.get(args[1])
                        self.user.update_output(str(self.user.mode.edit_object))
                    else:
                        self.user.update_output('That room doesn\'t exist. Type "list rooms" to see all the rooms in your area.\n')
                else:
                    self.user.update_output('You need to be editing an area before you can edit its contents.\n')
            else:
                self.user.update_ouput('You can\'t edit that.\n')
    

build_list.register(Edit, ['edit'])

class List(BaseCommand):
    """List the attributes of the object or area currently being edited."""
    def execute(self):
        message = 'Type "help list" to get help using this command.\n'
        list_funcs = ['room', 'npc', 'area', 'item']
        if not self.args:
            # The user didn't give a specific item to be listed; show them the current one,
            # if there is one
            if self.user.mode.edit_object:
                message = str(self.user.mode.edit_object)
            elif self.user.mode.edit_area:
                message = str(self.user.mode.edit_area)
            else:
                message = self.user.update_output('You\'re not editing anything right now.\n')
        else:
            exp = r'(?P<func>(area)|(npc)|(item)|(room))s?([ ]+(?P<id>\d+))?([ ]+in)?([ ]*area)?([ ]+(?P<area_name>\w+))?'
            func, obj_id, area_name = re.match(exp, self.args, re.I).group('func', 'id', 'area_name')
            if func in list_funcs:
                message = getattr(self, 'list_' + func)(obj_id, area_name)
            else:
                message = 'You can\'t list that.\n'
        self.user.update_output(message)
        
    def list_area(self, obj_id, area_name):
        if area_name:
            area = self.world.get_area(area_name)
            if area:
                return str(area)
            else:
                return 'That area doesn\'t exist.\n'
        else:
            return self.world.list_areas()
    
    def list_room(self, obj_id, area_name):
        # if there is an area
        if area_name:
            area = self.world.get_area(area_name)
            if not area:
                return 'Area "%s" doesn\'t exist.' % area_name
        else:
            area = self.user.mode.edit_area
            if not area:
                return 'What area do you want to list rooms for?\n'
        
        if obj_id:
            room = area.rooms.get(obj_id)
            if room:
                return str(room)
            else:
                return 'Room "%s" doesn\'t exist in area "%s".' % (obj_id, area.name)
        else:
            return area.list_rooms()
    
    def list_item(self, obj_id, area_name):
        return 'There aren\'t any yet.\n'
    
    def list_npc(self, obj_id, area_name):
        return 'There aren\'t any yet.\n'
    

build_list.register(List, ['list'])

class Set(BaseCommand):
    def execute(self):
        obj = self.user.mode.edit_object or self.user.mode.edit_area
        if not obj:
            self.user.update_output('You must be editing something to set its attributes.\n')
        elif not self.args:
            self.user.update_output('What do you want to set?\n')
        else:
            func, _, arg = re.match(r'\s*(\w+)([ ](.+))?$', self.args, re.I).groups()
            if hasattr(obj, 'set_' + func):
                self.user.update_output(getattr(obj, 'set_' + func)(arg))
            else:
                self.user.update_output('You can\'t set that.\n')
    

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
                        new_room = Room.create(this_room.area)
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
                if self.user.mode.edit_object.id == None:
                    self.user.mode.edit_object = None
        self.user.update_output(message)
    

build_list.register(Destroy, ['destroy'])