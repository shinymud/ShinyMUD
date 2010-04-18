from shinymud.models.area import Area
from shinymud.models.room import Room
from shinymud.models.item import Item, SLOT_TYPES, DAMAGE_TYPES
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
    help = (
    """<title>Create (BuildCommand)</title>
The Create command allows Builders to create new objects and areas.
\nALIASES: new
\nUSAGE:
To create a new area:
  new area <area_name>
To create a new object:
  new <object_type>
\n<object_type> above refers to the following: script, npc, room, item.
    """
    )
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
    """<title>Edit (BuildCommand)</title>
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
  edit script <script-id>
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
                           'Type "list '+ obj_type +'s" to see all the '+\
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
    help = (
    """<title>List (BuildCommand)</title>
The List command is one of the most useful BuildCommands, as it displays the
details about objects and areas.
\nUSAGE:
To view a list of all object types in an area:
  list <object-types> [from area <area-name>]
To get an attribute-by-attribute view of an object:
  list <object-type> <object-id> [from area <area-name>]
To get an attribute-by-attribute view of the object you're editing:
  list
    """
    )
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
    

build_list.register(List, ['list', 'ls'])
command_help.register(List.help, ['list'])

class Set(BaseCommand):
    required_permissions = BUILDER
    def execute(self):
        obj = self.user.mode.edit_object or self.user.mode.edit_area
        if not obj:
            self.user.update_output('You must be editing something to set its attributes.')
        elif not self.args:
            self.user.update_output('What do you want to set?')
        else:
            match = re.match(r'\s*(\w+)([ ](.+))?$', self.args, re.I)
            if not match:
                message = 'Type "help set" for help setting attributes.'
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
# There is already a help file for this under the generic Set command

class Link(BaseCommand):
    """Link two room objects together through their exits."""
    required_permissions = BUILDER
    help = (
    """<title>Link (BuildCommand)</title>
The Link command links the exits of two rooms, allowing players to move
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
    """<title>Unlink (BuildCommand)</title>
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
    help = (
    """<title>Add (BuildCommand)</title>
The Add command is used to add characteristics/options to to an object. To
remove options that have been added using the Add command, see "help remove".
\nUSAGE:
The usage for Add varies depending on the options and object being edited. For
more details about using Add on a specific object, see the help page for the
object you're editing.
    """
    )
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
    help = (
    """<title>Remove (BuildCommand)</title>
The Remove command works opposite the add command ("help add"), in that it
removes options that have been previously Added to an object.
\nUSAGE:
The usage is typically unique to the attribute that's being removed. See the
help file for the object you're editing for more details.
    """
    )
    def execute(self):
        obj = self.user.mode.edit_object or self.user.mode.edit_area
        if not obj:
            self.user.update_output('You must be editing something to remove attributes.')
        elif not self.args:
            self.user.update_output('What do you want to remove?')
        else:
            match = re.match(r'\s*(\w+)([ ](.+))?$', self.args, re.I)
            message = 'You can\'t remove that.'
            if not match:
                self.user.update_ouput('Type "help remove" for help with this command.')
            else:
                func, _, args = match.groups()
                if hasattr(obj, 'remove_' + func):
                    self.user.update_output(getattr(obj, 'remove_' + func)(args))
                elif obj.__class__.__name__ == 'Item':
                    # If we didn't find the remove function in the object's native remove functions,
                    # but the object is of type Item, then we should search the remove functions
                    # of that item's item_types (if it has any)
                    for iType in obj.item_types.values():
                        if hasattr(iType, 'remove_' + func):
                            message = getattr(iType, 'remove_' + func)(args)
                            break
                    self.user.update_output(message)
    

build_list.register(Remove, ['remove'])
command_help.register(Remove.help, ['remove'])

class Destroy(BaseCommand):
    """Destroy an area, room, npc, or item, permanently removing it from the system.
    
    NOTE: Player avatars should not be able to be deleted using this."""
    required_permissions = BUILDER
    help = (
    """<title>Destroy (BuildCommand)</title>
The Destroy command allows a builder to destroy an area, npc, script, item, or
room.
<blink>************** BEWARE ***************</blink>
The effects of the Destroy command cannot be undone. Once something is
destroyed it is permanently gone. Also, DESTROYING AN AREA WILL DESTROY
EVERYTHING IN THAT AREA! Moral of the story: be VERY sure you want to delete
something before you whip out the Destroy command. If in doubt, export your
area before you destroy it (see "help export")!
\nUSAGE:
To PERMANENTLY delete an object:
  destroy <object-type> <object-id>
To PERMANENTLY delete an area:
  destroy area <area-name>
\n<object_type> in the usage above refers to the following: room, npc, item,
or script.
    """
    )
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
            # The destroy function will set the id of whatever it deleted to
            # None so that any other objects with references will know they
            # should terminate their reference. If the user destroyed the object
            # they're working on, make sure that we clear it from their
            # edit_object, and therefore ther prompt so they don't try and edit
            # it again before it gets GC'd.
            if self.user.mode.edit_object and self.user.mode.edit_object.id == None:
                self.user.mode.edit_object = None
            if self.user.mode.edit_area and self.user.mode.edit_area.name == None:
                self.user.mode.edit_area = None
        self.user.update_output(message)
    

build_list.register(Destroy, ['destroy'])
command_help.register(Destroy.help, ['destroy'])

class Export(BaseCommand):
    required_permissions = BUILDER
    help = (
    """<title>Export (Build Command)</title>
The Export Command allows Builders to export their areas to text files.
\nUSAGE:
  export [area] <area-name>
\nExported areas can be found in your AREAS_EXPORT_DIR, which is listed in your
config file. To import an area that has been exported to a text file, see
"help import".
    """
    )
    def execute(self):
        if not self.args:
            self.user.update_output('Try: "export <area-name>"')
        else:
            if self.args.startswith('area '):
                self.args = self.args[5:]
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
    help = (
    """<title>Import (BuildCommand)</title>
The Import command allows Builders to import areas from text files.
\nUSAGE:
To get a list of areas in your area-import-directory:
  import
To import an area:
  import [area] <area-name>
To import the built-in areas that came pre-packaged with this MUD:
  import built-in
\n The <area-name> should be the same as the file-name without the
file-extension. For example, if the name of the file you're trying to import
is foo.txt, you should type:
    import foo
The area-import-directory path is listed in your config file.
To export areas to text-files, see "help export".
    """
    )
    def execute(self):
        if not self.args:
            self.user.update_output(SPort.list_importable_areas())
        elif self.args.startswith('built-in'):
            # Import all of areas in the PREPACK directory
            self.user.update_output(' Importing Built-In Areas '.center(50, '-'))
            result = SPort(PREPACK).import_list('all')
            self.user.update_output(result + ('-' * 50))
        else:
            # Import the desired area
            if self.args.startswith('area '):
                self.args = self.args[5:]
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
    """<title>Log (BuildCommand)</title>
Npc's receive the same feedback for preforming actions (commands) as a player
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
See "help <command-name>" for help on any one of these commands.
""" % ('\n'.join([cmd.__name__.lower() for cmd in build_list.commands.values()]))
), ['build commands', 'build command'])

command_help.register(("<title>Spawns (Room Attribute)</title>"
"""Every room has a list of "spawns". A spawn is an object that keeps track of
an item or npc and where should be loaded. When a room is told to Reset itself
(see "help reset"), it goes through its list of spawns and loads their items and
npcs into the place designated by the spawn's spawn point. You can only add
spawns to a room while you are editing that room during BuildMode.
\n<b>USAGE:</b>
NOTE: <object-type> can be "npc" or "item".
To add a spawn:
    add spawn [for] <object-type> <object-id> [[from area] <object-area>]
To remove a spawn:
  remove spawn <spawn-id>
\n<b>EXAMPLES:</b>
  add spawn for item 1
  add spawn for npc 5 from area bar
\nFor a more detailed explanation of spawns, see "help spawn example".
For help on nesting spawns (loading an item inside of a container item), see
"help nested spawns".
"""
), ['spawn', 'spawns'])

command_help.register(("<title>Spawn Example</title>"
"""Let's start by adding a couple of example spawns:
  add spawn for item 1
  add spawn for npc 5 from area bar
\nIf we list the attributes of the room we were editing, we should see something
like the following under spawns (of course, the actual item and npc are made up
here as an example-- you'll have to create your own with their own names):
  [1] Item - a treasure chest (1:foo) - spawns in room
  [2] Npc - Shiny McShinerson (5:bar) - spawns in room
\nThe first number in brackets is the spawn id. This is how we identify a
particular spawn (so we can remove it, for example).
Next we have the object type, which tells us if this spawn loads an item or an
npc.
Then we have the name of the item/npc to be loaded, with its item/npc id and
area-name in parenthesis next to it.
Finally, the last part is the spawn point for the spawn's object. We can
see here that the default is 'in room', which means both the item and the npc
will appear inside the room when the room is told to Reset. To learn how to set
a spawn point so that you can nest spawns (for example, tell a dagger to
load inside of a chest), see "help nested spawns".
"""
), ['spawn example'])

command_help.register(("<title>Nested Spawns (Room Attribute)</title>"
"""A nested spawn is when we have a spawn that tells an item to load
inside a container item, or inside an npc's inventory.
\n<b>USAGE:</b>
  add spawn [for] item <item-id> [in/inside] [spawn] <container-spawn-id>
\n<b>EXAMPLES:</b>
Let's say that when a room gets Reset, we want to load a chest with a dagger
inside. First, we need to add a spawn for the containing item (the
chest), which in this example has an id of 5:
  add spawn for item 5
\nNext we add a spawn for the dagger, telling it to load inside the object that
spawn #1 loads:
  add spawn for item 2 in spawn 1
\nIf you list the room's attributes, under spawns you should see something like
the following:
  [1] Item - a treasure chest (5:bar) - spawns in room
  [2] Item - a dagger (2:bar) - spawns into a treasure chest (S:1)
\nThe (S:1) on the end of the second spawn clarifies that the dagger is
loaded into spawn 1's item.
\nNOTE: Only items can be nested spawns (npcs can't be loaded inside other
items or npcs). Also, an item can only be loaded inside another item if the
second item is of type container ("help container").
"""
), ['nested spawn', 'nested spawns'])

command_help.register(("<title>NPC Events (NPC Attribute)</title>"
"""NPC events are what trigger an npc to perform a scripted action. 
\nUSAGE:
To add an event to an npc:
  add event <event-trigger> '<condition>' call <script_id> [<probability>]
  example: "add event hears 'I'll join your quest' call 2"
To remove an event from an npc:
  remove event <event-trigger> <event-id>
  example: "remove event hears 0"
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
when a certain event happens (see <b>"help npc event"</b>).
\nSCRIPT NOTES:
  <b>*Scripts can be created using the Create command (see "help create")*</b>
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
\nHelp pages for BuildMode Objects:
  "help area"
  "help npc"
  "help room"
  "help item"
  "help item type"
"""
), ['attributes', 'attribute'])

command_help.register(("<title>Area (BuildMode Object)</title>"
"""An area is like a package of rooms, items, npcs and scripts. You must be
editing an area before you can add new objects to it or edit its existing
objects.
\nAREA NOTES:
  <b>*Areas can be created using the Create command (see "help create")*</b>
\nAREA ATTRIBUTES:
<b>name - (not changeable)</b> The short name by which an area is referred to
during BuildMode. This name is given to the area during its creation process
and should be a short, descriptive, and unique word.
<b>title - (set title <title-text>)</b> A descriptive title for the area.
<b>level range - (set levelrange <level-range>)</b> A range of levels (such as
5-20) or a short description (e.g. Builders Only) that expresses who this level
is for.
<b>builders - (add builder <builder-name>)</b> A list of builders who have
access to edit this area (Builders that create an area are automatically
added to that area's Builder's List).
<b>description - (set description, starts TextEditMode)</b> A short description
about this area.
\nFor more help about attributes in general, see "help attribute".
"""
), ['area'])
command_help.register(("<title>Item (BuildMode Object) </title>"
"""Items make up all of the "things" in the game. From furniture to food, items
provide true interactivity to your areas.
\nITEM NOTES:
  <b>*Items can be created using the Create command (see "help create")*</b>
  <b>*For help adding items to rooms, see "help spawns"*</b>
  <b>*Gods can eat non-edible items. They can also carry non-carryble items*</b>
\nITEM ATTRIBUTES:
<b>name - (set name <name>)</b> The name of the item, seen by the player when
they interact with it (such as getting it, giving it, dropping it, etc.).
This should include any necessary articles such as 'a', 'an', or 'the' (e.g.
"a black-tinted dagger", or "an admiral's hat").
<b>title - (set title <title-text>)</b> A short (sentence-long) description
that a player sees when this item is in a room. If a title is not provided in
sentence format (capital at the beginning, period at the end), then the title
is automatically converted unless the builder prepends an @ to the title.
<b>item types - (add type <item-type>, remove type <item-type)</b> Any special
types this item has. See "help item types" for a list.
<b>description - (set description, starts TextEditMode)</b> A long description
that the player sees if they use the Look command on the item.
<b>equip location - (set equip <equip-location>)</b> The location this item can
be equipped to (see "help equip" for a list).
<b>keywords - (set keywords <kw1>,<kw2>,<kw...>)</b> Keywords that a player
can use to refer to this item when Getting it, Giving it, etc. Keywords should
contain words that are used in the item's title and name so as not to confuse
the player.
<b>weight - (set weight <weight>)</b> The weight of the object, without units.
<b>carryable - (set carryable <true/false>)</b> If carryable is true, this item
can be picked up and taken by a player. NOTE: Gods can still pick up
non-carryable items; they're just cool like that.
<b>base value - (set basevalue <base-value>)</b> The base currency value for
this item, without units.
"""
), ['item'])

command_help.register(("<title>Item Types (BuildMode Object) </title>"
"""There are currently 5 different item types:
  Equippable
  Food
  Furniture
  Container
  Portal
See their help pages for more information about the attributes and features
they add to a regular item object.
"""
), ['item types', 'item type'])

command_help.register(("<title>Portal (ItemType)</title>"
"""Portals are objects that manipulate the space-time continuum to allow players
to quickly travel from one place to another.
\nPORTAL NOTES:
  *Players (and npcs) can go through a portal using the Enter command*
\nPORTAL ATTRIBUTES:
<b>port location - (set portal to room <room-id> in area <area-name>)</b> This
is the location the user will be transported to when they enter the portal.
<b>entrance message - (set entrance <entrance-message>)</b> The message that the
user will see upon entering the portal.
<b>leave message - (set leave <leave-message>)</b> The message that will be
broadcast to the room that the player is leaving.
<b>emerge message - (set emerge <emerge-message>)</b> The message that will be
broadcast to the room that the player is emerging in.
\nNOTE: In the case of the attributes <b>emerge message</b> and <b>leave
message</b>, #actor can be used as a stand-in for the name of the player
entering the portal. See "help personalize" for details.
"""
), ['portal'])

command_help.register(("<title>Equippable (ItemType)</title>"
"""Equippable items can be worn on the character's body, or held in their hands.
\n<b>EQUIPPABLE ATTRIBUTES:</b> 
<b>damage (set damage <damage_type> <min>-<max> <percent>%)</b> Sets the amount
of damage this item can do if its wielder successfully hits an opponent. "set
damage" will always set the primary damage for an item. If you want to add
additional types of damage, use <b>add damage</b>. See also <b>help damage</b>.
<b>hit (set hit (+ or -) <amount>)</b> Sets the bonus or penalty to a
character's chance of hitting their target in battle. To cancel the
bonus/penalty, you can reset it to none using "set hit 0".
<b>evade (set evade (+ or -) <amount>)</b> Sets the bonus or penalty to a
character's evade ability. A high evade will make a character much harder to
hit. To undo, try "set evade 0".
<b>absorb (set absorb <damage_type> <amount>)</b> Sets the amount of damage that
this item can absorb, and of which types. Damage absorbed by items does not hurt
the chararter wearing them. A single item may absorb multiple types of damage,
by specifying a different damage_type each time you set it. Setting a negative
amount of damage means that the character will take extra damage of that type,
if they are hit. Some cursed items may make characters very vulnerable to
certain types of damage. see <b>help damage</b> for more info on damage types.
<b>equip (set equip <equip-slot>)</b> Set the location this item is worn/held.
The equip-slot may be one of the following:
  """ + ",\n  ".join([key for key in SLOT_TYPES.keys()]) + '.'
), ['weapon', 'equippable', 'armor', ])

command_help.register(("<title>Damage (Equippable Attribute)</title>"
"""Damage specifies how effective your attack is when you hit an opponent.
Damage is always shown and specified in the following format:
    <b><type> <min>-<max> <percent>%</b>
examples:
    slashing 3-7
    piercing 1-5 50%

<b>percent</b> The percentage of the time that this damage is applied, after the
hit is successful. This allows you to specify extra damage that only happens
some of the time. This is optional, and if not specified the damage will be
applied 100% of the time.
<b>type</b> The type of damage. Different enemies may be stronger or weaker
against different types of damage. The different types of damage are:
  """ +",\n  ".join([_ for _ in DAMAGE_TYPES]) + '.'
), ['damage', 'damage-type', 'damage-types'])

command_help.register(("<title>Food (ItemType)</title>"
"""Food items can be consumed using the Eat and Drink commands.
\nFOOD ATTRIBUTES:
<b>food type - (set food_type <food/drink>)</b> Sets whether this item is a food
or a drink (this really only changes what message is given when a player
consumes it).
<b>replace - (set replace [item] <item-id> [from area] <area-name>)</b> Set this
to have the food item be replaced by another item upon upon consumption. To
clear this attribute, try "set replace none".
<b>use message (actor) - (set actor_message <message>)</b> The message that will
be given to the character when they consume this item.
<b>use message (room) - (set room_message <message>)</b> The message that will
be broadcast to the surrounding room when a character eats this item. The
personalizer #actor can be used here.
<b>on-eat effects - (see "help effects")</b> The special effects that will be
transferred to a character when they consume this food.
"""
), ['food'])

command_help.register(("<title>Container (ItemType)</title>"
"""Containers are items that can hold other items. Characters can manage the
items inside containers by using the Put and Get commands.
\nCONTAINER ATTRIBUTES:
<b>weight capacity - (set weight_cap <capacity>)</b> The total weight capacity
that this container can hold. None means that container's weight capacity is
infinite.
<b>item capacity - (set item_cap <capacity>)</b> The total number of items that
this container can hold. None means that the container's item capacity is
infinite.
<b>weight reduction - (set reduction <percentage>)</b> The percentage of an
item's weight that is reduced when it is placed in this container.
<b>openable - (set openable <true/false>)</b> If true, then this container can
be opened and closed by the character (using the Open and Close commands).
<b>closed - (set closed <true/false>)</b> If closed is set to false, then this
container is set to closed by default; if false, this container is set to be
open by default.
<b>locked - (set locked <true/false>)</b> If locked is set to true, then this
container is locked by default and cannot be opened without first being
unlocked.
<b>key - (set key <key-item-id> [from area <area-name>])</b> The item that acts
as this container's key and can unlock it. NOTE: items can be locked and yet not
have an assigned key.
"""
), ['container'])

command_help.register(("<title>Furniture (ItemType)</title>"
"""Furniture items are items that can be slept and sat on. They can also confer
character effects upon their occupant.
\nFURNITURE ATTRIBUTES:
<b>sit effects - (not yet available)</b> The effects conferred to a sitting
character during their occupancy.
<b>sleep effects - (not yet available)</b> The effects conferred to a sleeping
character during their occupancy.
<b>capacity - (set capacity <capacity>)</b> The number of characters that this
furniture item can accommodate at one time. None means this furniture can hold
an infinite number of people.
"""
), ['furniture'])

command_help.register(("<title>Npc (BuildMode object)</title>"
"""Npcs (Non-player-characters) make up the virtual citizenry of the world. They
can hand out quests, fight against players, or dozens of other things to make
your area come to life.
\nNPC NOTES:
  <b>*Npcs can be created using the Create command (see "help create")*</b>
  <b>*For help adding npcs to rooms, see "help spawns"*</b>
  <b>*For help making your npcs come to life, see "help npc events"*</b>
\nNPC ATTRIBUTES:
<b>name - (set name <npc-name>)</b> The name of the npc.
<b>title - (set title <npc-title>)</b> A short (sentence-long) description that
a player sees when this item is in a room.
<b>gender - (set gender <gender-type>)</b> The gender of the npc. Can be male,
female, or neutral. This really only affects the pronoun that will be used in
describing the npc.
<b>keywords - (set keywords <kw1>,<kw2>,<kw...>)</b> Keywords that a player can
use to refer to this npc when interacting with it. Keywords should contain words
that are used in the npc's title and name so as not to confuse the player. A
neat trick: if you want a list of keywords to be made for you based on the npc's
name, try just "set keywords".
<b>description - (set description, starts TextEditMode)</b> A long description
that the player sees if they use the Look command on the npc.
<b>Npc events</b> - See "help npc events" for adding npc events.
"""
), ['npc', 'npcs'])

command_help.register(("<title>Room (BuildMode object)</title>"
"""Rooms are what make up the "physical" area of the world. Players, npcs, and
items all exist inside rooms.
\nROOM NOTES:
  <b>*Rooms can be created using the Create command (see "help create")*</b>
  <b>*For help adding npcs or items to rooms, see "help room spawns"*</b>
\nROOM ATTRIBUTES:
<b>name - (set name <room-name>)</b> The name of the room.
<b>description - (set description, starts TextEditMode)</b> A description of the
room. This should be anywhere from two to five sentences and should give the
player a good idea of the place they're in.
<b>exits -</b> For help editing exits, see "help exits" or "help link".
<b>spawns -</b> Spawns are the items and npcs that get loaded into this room when
the room is told to reset itself. Areas reset their rooms automatically when
they sense player activity. See "help spawns" for help adding spawn points
to your rooms, or "help reset" for help on manually resetting your room.
"""
), ['room', 'rooms'])

command_help.register(("<title>Exits (Room Attribute)</title>"
"""Exits are "doorways" from this room to another that allow players
to move from room to room.
\n<b>EXIT NOTES:</b>
  *To quickly add doorways between rooms, see "help link"*
  * An exit "direction" can be one of north, east, south, west, up, down*
\nEXIT ATTRIBUTES:
<b>to - (see "help link")</b> The area and id of the room that this exit leads
to.
<b>linked - (see "help link")</b> If true, then the room this exit goes to has
an exit linked back to this one.
<b>openable - (set exit <direction> openable <true/false>)</b> If openable is
set to true, that means this door can be opened and closed by a character.
<b>closed - (set exit <direction> closed <true/false>)</b> If closed is true,
this door will be closed by default. If closed is false, this door will be open
by default. Be careful about setting closed = true without having openable =
true -- you don't want a door closed by default that your players can't open!
<b>hidden - (set exit <direction> hidden <true/false>)</b> If hidden is set to
true, this exit won't be visible to the naked eye (a player will need "detect
hidden" to see it).
<b>locked - (set exit <direction> locked <true/false)</b> If locked is set to
true, then this door cannot be opened without first being unlocked.
<b>key - (set key <key-item-id> [from area <area-name>])</b> The item that acts
as this container's key and can unlock it. NOTE: items can be locked and yet not
have an assigned key.
"""
), ['exits', 'exit'])

command_help.register(("<title>Character Effects</title>"
"""Coming Soon! Sorry for the delay.
"""
), ['effects', 'character effects'])