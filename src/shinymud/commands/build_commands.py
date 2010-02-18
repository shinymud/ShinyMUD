from shinymud.models.area import Area
from shinymud.models.room import Room
from shinymud.models.item import Item, SLOT_TYPES
from shinymud.models.npc import Npc
from shinymud.lib.world import World
from shinymud.lib.sport import *
from shinymud.commands import *
import re
import logging

build_list = CommandRegister()

class Create(BaseCommand):
    """Create a new item, npc, or area."""
    required_permissions = BUILDER
    def execute(self):
        object_types = ['item', 'npc', 'room', 'script']
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
command_help.register(Create.help, ['create', 'new'])

class Edit(BaseCommand):
    """Edit an area, object, npc, or room."""
    required_permissions = BUILDER
    help = (
    """Edit (BuildCommand)
\nThe Edit command allows you to edit areas and their rooms, npcs, and items. 
Remember, you must be editing an area before you can edit the rooms, npcs and
items associated with it!
You will only be able to edit areas if you are on that area's Builder's List.
You will be automatically added to the Builder's List on any area you
personally create (see "help create"). If you want permission to edit an area
that someone else has created, you will have to ask the creator to add you to
their area's Builder's List.
\nRequired Permissions: BUILDER
\nUSAGE:
To start editing an area:
  edit <area-name>
Once you are editing an area, you may use the following to edit its contents:
  edit npc <npc-id>
  edit room <room-id>
  edit item <item-id>
    """
    )
    def execute(self):
        help_message = 'Type "help edit" to get help using this command.'
        if not self.args:
            self.user.update_output(help_message)
            return
        args = [arg.strip().lower() for arg in self.args.split()]
        if len(args) < 2:
            self.user.update_output(help_message)
            return
        if args[0] == 'area':
            area = self.world.get_area(args[1])
            if area:
                self.edit_area(area)
            else:
                self.user.update_output('That area doesn\'t exist.' +\
                                        'You should create it first.')
                
        elif args[0] in ['room', 'npc', 'item', 'script']:
            self.edit_object(args[0], args[1])
        else:
            self.user.update_output('You can\'t edit that.\n')
    
    def edit_area(self, area):
        if (self.user.name in area.builders) or (self.user.permissions & GOD):
            self.user.mode.edit_area = area
            # Make sure to clear any objects they were working on in the 
            # old area
            self.user.mode.edit_object = None
            self.user.update_output('Now editing area "%s".' % area.name)
        else:
            self.user.update_output('You aren\'t allowed to edit someone ' +\
                                    'else\'s area.')
    
    def edit_object(self, obj_type, obj_id):
        if self.user.mode.edit_area:
            obj = getattr(self.user.mode.edit_area, obj_type + 's').get(obj_id)
            if obj:
                self.user.mode.edit_object = obj
                self.user.update_output(str(self.user.mode.edit_object))
            else:
                noexist = ('That ' + obj_id + ' doesn\'t exist. ' +\
                           'Type "list '+ obj_id +'s" to see all the '+\
                           obj_id +'s in your area.'
                          )
                self.user.update_output(noexist) 
        else:
            self.user.update_output('You need to be editing an area before '+\
                                    'you can edit its contents.')
    

build_list.register(Edit, ['edit'])
command_help.register(Edit.help, ['edit'])

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
    required_permissions = BUILDER
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
            exp = r'(?P<func>(area)|(npc)|(item)|(room)|(script))s?([ ]+(?P<id>\d+))?([ ]+in)?([ ]*area)?([ ]+(?P<area_name>\w+))?'
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
command_help.register(List.help, ['list'])

class Set(BaseCommand):
    required_permissions = BUILDER
    help = (
    """Set (BuildCommand)
Set allows you to set attributes of whatever object you are editing. If you
wish to set your character attributes, you must exit BuildMode first.
    """
    )
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
                    message = (getattr(obj, 'set_' + func)(arg, self.user))
                
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
# command_help.register(Set.help, ['set', 'bset'])

class Link(BaseCommand):
    """Link two room objects together through their exits."""
    required_permissions = BUILDER
    help = (
    """Link (BuildCommand)
\nThe Link command links the exits of two rooms, allowing players to move
between them.
\nRequired Permissions: BUILDER
\nUSAGE:
To simultaneously create a new room and link to it:
  link <direction>
To link to a specific room (in the area you're editing):
  link <direction> exit to room <room-id>
To link to a specific room in a different area than the one you're editing:
  link <direction> exit to room <room-id> from area <area-name>
\nEXAMPLES:
The easiest way to use link is just to pass it a direction, like so:
  link north
This creates a new room for you, then links the north exit of the room you're
editing to the south exit of the new room.
If you want to create a link between the room you're editing and a room that
already exists, you could do the following:
  link west exit to room 2
This links the west exit of the room you're editing with the east exit of room
2 from the same area.
Finally, note that Link always links to cardinal opposites -- that is, the
exit of any room you link to will lead back in the opposite direction.
\nNOTE: You can't link to an exit that's already linked (you'll have to unlink
it first). See "help unlink".
    """
    )
    def execute(self):
        this_room = self.user.mode.edit_object
        if this_room and (this_room.__class__.__name__ == 'Room'):
            exp = r'(?P<direct>\w+)(([ ]+exit)?([ ]+to)?([ ]+room)?([ ]+(?P<room>\d+)))?(([ ]+from)?([ ]+area)?([ ]+(?P<area>\w+)))?'
            match = re.match(exp, self.args, re.I)
            if not match:
                self.user.update_output('Type "help link" for help on this command.')
                return
            direction, area_name, room_id = match.group('direct', 'area', 'room')
            if direction not in this_room.exits:
                self.user.update_output('"%s" is not a valid exit direction.' % direction)
                return
            if room_id:
                if area_name:
                    area = self.world.get_area(area_name)
                    if not area:
                        self.user.update_output('Area "%s" doesn\'t exist.' % area_name)
                        return
                else:
                    area = self.user.mode.edit_area
                room = area.get_room(room_id)
                if not room:
                    self.user.update_output('Room "%s" doesn\'t exist in area %s.' % (room_id, area.name))
                    return
                self.user.update_output(this_room.link_exits(direction, room))
            else:
                new_room = this_room.area.new_room()
                self.user.update_output('Room %s created.\n' % new_room.id)
                self.user.update_output(this_room.link_exits(direction, new_room))
        else:
            self.user.update_output('You have to be editing a room to link it to something.')
    

build_list.register(Link, ['link'])
command_help.register(Link.help, ['link'])

class Unlink(BaseCommand):
    """Destroys a linked exit between two linked rooms."""
    required_permissions = BUILDER
    help = (
    """Unlink (BuildCommand)
\nUnlink destroys a linked exit. See "help link" for help on linking exits.
\nRequired Permissions: BUILDER
\nUSAGE:
To unlink an exit of the room you're editing:
  unlink <exit-direction>
    """
    )
    def execute(self):
        if not self.args or self.args.isspace():
            self.user.update_output('Type "help unlink" for help with this '
                                    'command.')
            return
        this_room = self.user.mode.edit_object
        if this_room and (this_room.__class__.__name__ == 'Room'):
            direction = self.args.strip()
            if direction not in this_room.exits:
                self.user.update_output('%s is not a valid direction.' % direction)
            self.user.update_output(this_room.unlink_exits(direction))
        else:
            self.user.update_output('You have to be editing a room to unlink its exits.')
    

build_list.register(Unlink, ['unlink'])
command_help.register(Unlink.help, ['unlink'])

class Add(BaseCommand):
    required_permissions = BUILDER
    def execute(self):
        obj = self.user.mode.edit_object or self.user.mode.edit_area
        if not obj:
            self.user.update_output('You must be editing something to add attributes.\n')
        elif not self.args:
            self.user.update_output('What do you want to add?\n')
        else:
            message = 'You can\'t add that.\n'
            match = re.match(r'\s*(\w+)([ ](.+))?$', self.args, re.I)
            if not match:
                self.user.update_output('Type "help add" for help with this command.\n')
            else:
                func, _, arg = match.groups()
                if hasattr(obj, 'add_' + func):
                    self.user.update_output(getattr(obj, 'add_' + func)(arg))
                elif obj.__class__.__name__ == 'Item':
                    # If we didn't find the add function in the object's native add functions,
                    # but the object is of type Item, then we should search the add functions
                    # of that item's item_types (if it has any)
                    for iType in obj.item_types.values():
                        if hasattr(iType, 'add_' + func):
                            message = getattr(iType, 'add_' + func)(arg)
                            break
                    self.user.update_output(message)
    

build_list.register(Add, ['add'])
command_help.register(Add.help, ['add'])

class Remove(BaseCommand):
    required_permissions = BUILDER
    def execute(self):
        obj = self.user.mode.edit_object or self.user.mode.edit_area
        if not obj:
            self.user.update_output('You must be editing something to remove attributes.\n')
        elif not self.args:
            self.user.update_output('What do you want to remove?\n')
        else:
            match = re.match(r'\s*(\w+)([ ](.+))?$', self.args, re.I)
            message = 'You can\'t remove that.\n'
            if not match:
                self.user.update_ouput('Type "help remove" for help with this command.\n')
            else:
                func, _, args = match.groups()
                if hasattr(obj, 'remove_' + func):
                    self.user.update_output(getattr(obj, 'remove_' + func)(args))
                elif obj.__class__.__name__ == 'Item':
                    # If we didn't find the set function in the object's native set functions,
                    # but the object is of type Item, then we should search the set functions
                    # of that item's item_types (if it has any)
                    for iType in obj.item_types.values():
                        if hasattr(iType, 'set_' + func):
                            message = getattr(iType, 'set_' + func)(args)
                            break
                    self.user.update_output(message)
    

build_list.register(Remove, ['remove'])
command_help.register(Remove.help, ['remove'])

class Destroy(BaseCommand):
    """Destroy an area, room, npc, or item, permanently removing it from the system.
    
    NOTE: Player avatars should not be able to be deleted using this."""
    required_permissions = BUILDER
    def execute(self):
        message = 'Type "help destroy" to get help using this command.\n'
        if not self.args:
                # Don't ever let them destroy something if they haven't been specific about 
                # what they want destroyed (i.e, they haven't given us any arguments)
                message = self.user.update_output('You should be more specific. This command could really cause some damage.\n')
                return
        exp = r'(?P<func>(area)|(npc)|(item)|(room))([ ]+(?P<id>\d+))?([ ]+in)?([ ]*area)?([ ]+(?P<area_name>\w+))?'
        match = re.match(exp, self.args, re.I)
        message = 'Type "help destroy" to get help using this command.\n'
        if match:
            func, obj_id, area_name = match.group('func', 'id', 'area_name')
            if not area_name:
                area = self.user.mode.edit_area
            else:
                area = self.world.get_area(area_name)
                if not area:
                    self.user.update_output('That area doesn\'t exist.\n')
                    return
                elif not ((self.user.permissions & GOD) or (self.user.name in area.builders)):
                    self.user.update_output('You\'re not allowed to destroy someone else\'s area.\n')
                    return
            if func == 'area':
                message = self.world.destroy_area(area_name, self.user.name)
            elif area and hasattr(area, 'destroy_' + func):
                message = getattr(area, 'destroy_' + func)(obj_id)
            else:
                message = 'You can\'t destroy something that does\'t exist.'
            # The destroy function will set the id of whatever it deleted to None
            # so that any other objects with references will know they should terminate
            # their reference. If the user destroyed the object they're working on,
            # make sure that we clear it from their edit_object, and therefore ther prompt 
            # so they don't try and edit it again before it gets wiped.
            if self.user.mode.edit_object and self.user.mode.edit_object.id == None:
                self.user.mode.edit_object = None
            if self.user.mode.edit_area and self.user.mode.edit_area.name == None:
                self.user.mode.edit_area = None
        self.user.update_output(message)
    

build_list.register(Destroy, ['destroy'])
command_help.register(Destroy.help, ['destroy'])

class Export(BaseCommand):
    required_permissions = BUILDER
    def execute(self):
        if not self.args:
            self.user.update_output('Try: "export <area-name>"')
        else:
            area = self.world.get_area(self.args)
            if area:
                self.user.update_output('Exporting area %s. This may take a moment.' % area.name)
                try:
                    result = SPort().export_to_shiny(area)
                except SPortExportError, e:
                    self.user.update_output(e)
                else:
                    self.user.update_output(result)
            else:
                self.user.update_output('That area doesn\'t exist.')
    

build_list.register(Export, ['export'])
command_help.register(Export.help, ['export'])

class Import(BaseCommand):
    required_permissions = BUILDER
    def execute(self):
        if not self.args:
            self.user.update_output(SPort.list_importable_areas())
        else:
            area = self.world.get_area(self.args)
            if area:
                self.user.update_output('That area already exists in your world.\n' +\
                                        'You\'ll need to destroy it in-game before you try importing it.\n')
            else:
                try:
                    result = SPort().import_from_shiny(self.args)
                except SPortImportError, e:
                    self.user.update_output(str(e))
                else:
                    self.user.update_output(result)
    

build_list.register(Import, ['import'])
command_help.register(Import.help, ['import'])

class Log(BaseCommand):
    help = (
    """Log (BuildCommand)
Npc's receive the same feedback for preforming actions (commands) as a player
character, but since they can't read, their feedback gets accumulated in an
action log rather than being output to a screen. The Log command allows you to
read the action log (and memory) of an npc to help you debug scripting errors.
\nUSAGE:
  log <npc-name>
    """
    )
    def execute(self):
        if not self.args:
            self.user.update_output('Type "help log" for help with this command.')
            return
        if not self.user.location:
            self.user.update_output('There aren\'t any npcs in the void to log.')
            return
        npc = self.user.location.get_npc_by_kw(self.args.lower().strip())
        if not npc:
            self.user.update_output('That npc doesn\'t exist.')
            return
        string = (' Log for %s ' % npc.name).center(50, '-') + '\n'
        if npc.remember:
            string += 'REMEMBERS: '
            string += ', '.join(npc.remember) + '\n'
        else:
            string += 'REMEMBERS: This npc doesn\'t remember any users.\n'
        string += 'ACTION LOG:\n'
        if npc.actionq:
            string += '\n'.join([a.strip('\n').strip('\r') for a in npc.actionq])
        else:
            string += 'Action log is empty.'
        string += '\n' + ('-' * 50)
        self.user.update_output(string)
    

build_list.register(Log, ['log'])
command_help.register(Log.help, ['log'])

# Defining Extra Build-related help pages:
command_help.register(("<title>Build Commands (BuildMode)</title>"
"""The following are the commands available during BuildMode:
%s
See 'help <command-name> for help on any one of these commands.
""" % ('\n'.join([cmd.__name__.lower() for cmd in build_list.commands.values()]))
), ['build commands', 'build command'])

command_help.register(("<title>Room Resets (Room Attribute)</title>"
"""Every room has a list of "room resets". A room reset is an object that
keeps track of an item or npc and a spawn point. When a room is told to Reset
itself (see "help reset"), it goes through its list of room resets and spawns
each room reset's item or npc into the place designated by the room reset's
spawn point. You can only add room resets to a room while you are editing that
room during BuildMode.\n
USAGE:
<object-type> can be "npc" or "item".
To add a room reset:
    add reset [for] <object-type> <object-id> [[from area] <object-area>]
To remove a room reset:
  remove reset <reset-id>\n
Examples:
    add reset for item 1
    add reset for npc 5 from area bar
If we list the attributes of the room we were editing, we should see something
like the following under room resets:
  [1] Item - a treasure chest (1:foo) - spawns in room
  [2] Npc - Shiny McShinerson (5:bar) - spawns in room\n
The first number in brackets is the room reset id. This is how we identify a
particular reset (so we can remove it, for example). Next we have the object
type, which tells us if this room reset spawns an item or an npc. Then we have
the name of the item/npc to be spawned, with its item/npc id and area-name in
parenthesis next to it. Finally, the last part is the spawn point for the room
reset's object. We can see here that the default is 'in room', which means
both the item and the npc will appear inside the room when the room is told to
Reset. To learn how to set a spawn point so that you can nest room resets (for
example, tell a dagger to spawn inside of a chest), see "help nested resets".
"""
), ['room resets', 'room reset'])

command_help.register(("<title>Nested Resets (Room Attribute)</title>"
"""A nested reset is when we have a room reset that tells an item to spawn
inside a container item, or inside an npc's inventory.
USAGE:
  add reset [for] item <item-id> [in/inside] [reset] <container-reset-id>\n
Examples:
Let's say that when a room gets Reset, we want to spawn a chest with a dagger
inside. First, we need to add a room reset for the containing item (the
chest), which happens to have an item id of 5:
  add reset for item 5\n
Next we add a reset for the dagger, telling it to spawn into the object that
room reset #1 spawns:
  add reset for item 2 into reset 1
If you list the room's attributes, under resets you should see something like
the following:
  [1] Item - a treasure chest (5:bar) - spawns in room
  [2] Item - a dagger (2:bar) - spawns into a treasure chest (R:1)\n
The (R:1) on the end of the second room reset clarifies that the dagger is
spawned into reset 1's item.\n
NOTE: Only items can be nested resets (npcs can't be spawned inside other
items or npcs). Also, an item can only be spawned into another item if the
second item is of type container.
"""
), ['nested resets', 'nested reset'])

command_help.register(("<title>NPC Events (NPC Attribute)</title>"
"""NPC events are what trigger an npc to perform a scripted action. 
\nUSAGE:
To add an event to an npc:
  add event <event-trigger> '<condition>' call <script_id> [<probability>]
To remove an event from an npc:
  remove event <event-trigger>
\nFor a list of event triggers, see "help triggers".
"""
), ['npc event', 'event', 'events'])

command_help.register(("<title>Event Triggers (NPC Events)</title>"
"""The following are a list of event triggers that can be used to trigger
an npc into executing a script. See "help npc event" for more information
on events.
pc_enter - call script when a player character enters the room.
given_item - call script when the npc is given an item.
hears 'condition' - call script when the npc hears 'condition' text in the 
    room.
"""
), ['event list', 'triggers', 'event triggers'])

command_help.register(("<title>Scripts (BuildMode object)</title>"
"""Scripts are a BuildMode object like items, npcs and rooms. They are
essentially documents containing a set of actions that an npc should preform
when a certain event happens (see "help npc event").
\nSCRIPT ATTRIBUTES:
<b>name - (set name <script-name>)</b> A name to help distinguish this script
from other scripts in this area.
<b>body - (set body, starts TextEditMode)</b> The set of instructions that an
npc should do once the event has been triggered. See "help shiny script" for
help with writing the body of a script.
For more information on writing scripts, see the following help pages:
  "help script example"
  "help shiny script"
  "help script conditionals"
  "help script commands"
"""
), ['scripts', 'script'])

command_help.register(("<title>Example Script (Script Language)</title>"
"""The following is an example of what a typical script could look like:\n
  if remember #target_name
    say Hello #target_name, it's nice to see you again!
  else
    record #target_name
    load item 3 from area new_castle
    give new castle map to #target_name
    say Welcome to New Castle, #target_name. 
  endif
  say Enjoy your day!
\nThe above script, when triggered by an event, will cause an npc to do the
following: If the npc remembers a player (the player has triggered this script
before), then the npc will just give a simple greeting. If the npc doesn't
remember a player, it will record that player in its memory, load a map item
from its current area, then give that map to the player with a welcome
greeting.
"""
), ['script example'])

command_help.register(("<title>ShinyScript (Script Language)</title>"
"""The body of a script is written in a very simple language called
ShinyScript.
ShinyScript conventions:
* Each line of the script body consists of one command, followed by its
  arguments (options), with the exceptions of if-statements, explained below.
* If a command is lengthy and needs to span multiple lines, a '+' symbol can
  be used at the end of a line to denote that the next line is a continuation
  of the first.
* ShinyScript has some extra commands which can only be used in scripts: see
  "help script commands" for a list of script-only commands to make your npc's
  more life-like.
* If-statements can be used to execute different branches of commands
  depending on a conditional (see "help script conditionals" for a list of
  conditionals that can be used in if-statments). The form of the if-statment
  is as follows:\n
  if conditional
    command 1
    command 2
    ...
  else
    command 20
    ...
  endif\n
  If the conditional is true, all of the commands after the if and before the
  else will be executed. If it is false, all the conditions after the else and
  before the endif will be executed. The else is optional, but the endif is
  not. Nested if-statements (if-statements within if-statments) are allowed.
* Whitespace is ignored before and after commands. If you wish to indent, be
  our guest ;)
For an example of a ShinyScript, see "help script example".
"""
), ['shinyscript', 'shiny script'])

command_help.register(("<title>ShinyScript Commands (Script Language)</title>"
"""The following commands are only available in ShinyScript (writing the body
of scripts). Each command is followed by an example of how it should be used,
in parenthesis, and then a short description of what it does.
* record (record #target_name) - Record allows an npc to record a player's
  name in its memory so that it can act differently toward players that it has
  already interacted with. Names that are recorded can be remembered using the
  remember conditional (see "help script conditionals").
"""
), ['script commands'])

command_help.register(("<title>ShinyScript Conditionals (Script Language)</title>"
"""Conditionals are how if-statements get evaluated in ShinyScript. The
following are all of the conditionals you can test in a script:
* remember (if remember #target_name) - Will be true if the npc has the name
  of the target player in its memory. Npcs can store names in their memory by
  using the script command Record (see help "script commands").
* equal (if equal keyword1 keyword2) - Will be true if keyword1 is the same as
  keyword2, false if keyword1 is not the same as keyword2.

"""
), ['script conditional', 'script conditionals'])

command_help.register(("<title>Attributes (BuildMode Object)</title>"
"""Attributes are the individual characteristics of an object. For example,
name and description are both attributes of item and npc objects. During
BuildMode, you can change the attributes of an object that you're editing by
using one, some, or all of the Set, Add, and Remove commands. The command
needed to edit an attribute will always be listed next to that attribute in
paranthesis on the help page for that object.
"""
), ['attributes', 'attribute'])
