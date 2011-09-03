from shinymud.models.room_exit import RoomExit
from shinymud.models.spawn import Spawn
from shinymud.modes.text_edit_mode import TextEditMode
from shinymud.models import Model, Column, model_list
from shinymud.models.shiny_types import *
import re

dir_opposites = {'north': 'south', 'south': 'north',
                 'east': 'west', 'west': 'east',
                 'up': 'down', 'down': 'up'}

class Room(Model):
    db_table_name = 'room'
    db_columns = Model.db_columns + [
        Column('area', read=read_area, write=write_area,
               foreign_key=('area', 'name'), null=False, type='INTEGER'),
        Column('id', null=False),
        Column('name', default='New Room'),
        Column('description', default='This is a shiny new room!')
    ]
    db_extras = Model.db_extras + ['UNIQUE (area, id)']
    def __init__(self, args={}):
        self.items = []
        self.exits = {'north': None,
                      'south': None,
                      'east': None,
                      'west': None,
                      'up': None,
                      'down': None}
        self.npcs = []
        self.spawns = {}
        self.players = {}
        Model.__init__(self, args)
    
    def load_extras(self):
        self.load_exits()
        self.load_spawns()
    
    @classmethod
    def create(cls, area, room_id):
        """Create a new room."""
        new_room = cls({'area':area, 'id':room_id})
        return new_room
    
    def __str__(self):
        nice_exits = ''
        for direction, value in self.exits.items():
            if value:
                nice_exits += '    ' + direction + ': ' + str(value) + '\n'
            else:
                nice_exits += '    ' + direction + ': None\n'
        spawns = ''
        for spawn in self.spawns.values():
            spawns += '\n    [%s] %s' % (spawn.id, str(spawn))
        if not spawns:
            spawns = 'None.'
        room_list = (' Room %s in Area %s ' % (self.id, self.area.name)
                     ).center(50, '-') + '\n'
        room_list += """name: %s
description: 
    %s
exits: 
%s
spawns: %s""" % (self.name, self.description, nice_exits, spawns)
        room_list += '\n' + ('-' * 50)
        return room_list
    
#************** BuildMode Accessors **************
    def build_set_name(self, name, player=None):
        """Set the name of a room."""
        if not name:
            return 'Set the name to what?'
        name = ' '.join([name.strip().capitalize() for name in name.split()])
        self.name = name
        self.save()
        return 'Room %s name set.' % self.id
    
    def build_set_description(self, args, player=None):
        """Set the description of a room."""
        player.last_mode = player.mode
        player.mode = TextEditMode(player, self, 'description', self.description)
        return 'ENTERING TextEditMode: type "@help" for help.'
    
    def build_set_exit(self, args, player=None):
        args = args.split()
        if len(args) < 3:
            return 'Usage: set exit <direction> <attribute> <value(s)>. Type "help exits" for more detail.\n'
        my_exit = self.exits.get(args[0])
        if my_exit:
            if hasattr(my_exit, 'build_set_' + args[1]):
                return getattr(my_exit, 'build_set_' + args[1])(args[2:])
            else:
                return 'You can\'t set that.'
        else:
            return 'That exit doesn\'t exist.'
    
    def build_add_exit(self, args, player=None):
        exp = r'(?P<direction>(north)|(south)|(east)|(west)|(up)|(down))([ ]+to)?([ ]+(?P<room_id>\d+))([ ]+(?P<area_name>\w+))?'
        match = re.match(exp, args, re.I)
        message = 'Type "help exits" to get help using this command.'
        if match:
            direction, room_id, area_name = match.group('direction', 'room_id', 'area_name')
            area = World.get_world().get_area(area_name) or self.area
            if area:
                room = area.get_room(room_id)
                if room:
                    self.new_exit({'direction': direction, 'to_room': room})
                    message = 'Exit %s created.' % direction
                else:
                    message = 'That room doesn\'t exist.'
            else:
                message = 'That area doesn\'t exist.'
        return message
    
    def build_remove_exit(self, args, player=None):
        if not args:
            return 'Which exit do you want to remove?\n'
        if not (args in self.exits and self.exits[args]):
            return '%s is not a valid exit.\n' % args
        exit = self.exits[args]
        link = ''
        if exit.linked_exit:
            # Clear any exit that is associated with this exit
            if exit.to_room and exit.to_room.exits[exit.linked_exit]:
                exit.to_room.exits[exit.linked_exit].destruct()
                exit.to_room.exits[exit.linked_exit] = None
            link = '\nThe linked exit in room %s, area %s, has also been removed.' % (exit.to_room.id,
                                                                                     exit.to_room.area.name)
        self.exits[args].destruct()
        self.exits[args] = None
        return args + ' exit has been removed.' + link
    
    def build_add_spawn(self, args, player=None):
        if not args:
            return 'Type "help room spawns" to get help using this command.'
        exp = r'((for[ ]+)?(?P<obj_type>(item)|(npc))([ ]+(?P<obj_id>\d+))' +\
              r'(([ ]+from)?([ ]+area)([ ]+(?P<area_name>\w+)))?' +\
              r'(([ ]+((in)|(into)|(inside)))?([ ]+spawn)?([ ]+(?P<container>\d+)))?)'
        match = re.match(exp, args, re.I)
        if match:
            obj_type, obj_id, area_name, container = match.group('obj_type', 
                                                                 'obj_id', 
                                                                 'area_name',
                                                                 'container')
            area = World.get_world().get_area(area_name) or self.area
            if not area:
                return 'That area doesn\'t exist.'
            obj = getattr(area, obj_type + "s").get(obj_id)
            if not obj:
                return '%s number %s does not exist.' % (obj_type, obj_id)
            if container:
                if container not in self.spawns:
                    return 'Spawn %s doesn\'t exist.' % container
                container_spawn = self.spawns.get(container)
                c_obj = container_spawn.spawn_object
                if container_spawn.spawn_object.has_type('container'):
                    spawn = self.new_spawn({'id': self.get_spawn_id(),
                                            'room':self,
                                            'obj':obj,
                                            'spawn_type':obj_type,
                                            'container': container_spawn})
                    container_spawn.add_nested_spawn(spawn)
                    return 'A room spawn has been added for %s number %s.' % (obj_type, obj_id)
                else:
                    return 'Room spawn %s is not a container.' % container
            self.new_spawn({'id': self.get_spawn_id(), 'room':self, 'obj':obj, 'spawn_type':obj_type})
            return 'A room spawn has been added for %s number %s.' % (obj_type, obj_id)
        return 'Type "help room spawns" to get help using this command.'
    
    def build_remove_spawn(self, args, player=None):
        exp = r'(?P<spawn_num>\d+)'
        match = re.match(exp, args, re.I)
        if not match:
            return 'Type "help spawns" to get help using this command.\n'
        spawn_id = match.group('spawn_num')
        if spawn_id in self.spawns:
            spawn = self.spawns[spawn_id]
            del self.spawns[spawn_id]
            # If this spawn has a container, we need to destroy
            # that container's link to it
            if spawn.container and spawn.container.id in self.spawns:
                self.spawns[spawn.container.id].remove_nested_spawn(spawn)
            # Delete all spawns that were supposed to be
            # spawn into this container -- their spawn point is being deleted,
            # so they should no longer be on the spawn list.
            message = 'Room spawn %s has been removed.\n' % spawn_id
            dependents = ', '.join([sub_spawn.id for sub_spawn in spawn.nested_spawns])
            for sub_spawn in spawn.nested_spawns:
                sub_spawn.destruct()
                del self.spawns[sub_spawn.id]
            spawn.destruct()
            if dependents:
                message += ('The following nested spawns were also removed: ' + 
                            dependents + '.\n')
            return message
        return 'Room spawn #%s doesn\'t exist.\n' % spawn_id
    
#************** Exits Management **************
    def new_exit(self, exit_dict={}):
        exit_dict['room'] = self
        new_exit = RoomExit(exit_dict)
        new_exit.save()
        self.exits[exit_dict['direction']] = new_exit
    
    def load_exits(self):
        rows = self.world.db.select("* from room_exit where room=?", [self.dbid])
        for row in rows:
            row['room'] = self
            self.exits[row['direction']] = RoomExit(row)
    
    def link_exits(self, direction, link_room):
        """Link exits between this room (self), and the room passed."""
        this_exit = self.exits.get(direction)
        that_dir = dir_opposites.get(direction)
        that_exit = link_room.exits.get(that_dir)
        if this_exit and this_exit.linked_exit:
            return ("This room's (id: " + this_exit.room.id + ") " +
                    this_exit.direction + " exit is already linked to " +
                    "room " + this_exit.to_room.id + ", area " + 
                    this_exit.to_room.area.name + ".\nYou must " +
                    "unlink it before linking it to a new room.")
        if that_exit and that_exit.linked_exit:
            return ("Room " + that_exit.room.id + "'s " +
                    that_exit.direction + " exit is already linked to " +
                    "room " + that_exit.to_room.id + ", area " + 
                    that_exit.to_room.area.name + ".\nYou must " +
                    "unlink it before linking it to a new room.")
        if this_exit:
            this_exit.to_room = link_room
        else:
            self.new_exit({'direction': direction, 'to_room':link_room})
            this_exit = self.exits[direction]
        if that_exit:
                that_exit.to_room = self
        else:
            link_room.new_exit({'direction': that_dir, 'to_room': self})
            that_exit = link_room.exits[that_dir]
        # Now that the exits have been properly created/set, set the exits to point to each other
        this_exit.linked_exit = that_exit.direction
        that_exit.linked_exit = this_exit.direction
        this_exit.save()
        that_exit.save()
        return 'Linked room %s\'s %s exit to room %s\'s %s exit.\n' % (this_exit.room.id, this_exit.direction,
                                                                      that_exit.room.id, that_exit.direction)
    
    def unlink_exits(self, direction):
        exit = self.exits.get(direction)
        if not exit:
            return 'The %s exit doesn\'t exist.' % direction
        if not exit.linked_exit:
            return 'The %s exit is not linked to anything.' % direction
        # Just in case our linked exit got deleted and this room didn't 
        # know about it:
        if exit.to_room and exit.to_room.exits[exit.linked_exit]:
            exit.to_room.exits[exit.linked_exit].destruct()
            exit.to_room.exits[exit.linked_exit] = None
        exit.destruct()
        self.exits[direction] = None
        return 'The %s exit has been unlinked.' % direction
    
#************** Spawn Management **************
    def new_spawn(self, spawn_dict):
        """Create a new spawn object from the spawn_dict and return it."""
        spawn = Spawn(spawn_dict)
        if not spawn.dbid:
            spawn.save()
        self.spawns[spawn.id] = spawn
        return spawn
    
    def get_spawn_id(self):
        rows = self.world.db.select("max(id) as id from room_spawns where room=?", [self.dbid])
        max_id = rows[0]['id']
        if max_id:
            your_id = int(max_id) + 1
        else:
            your_id = 1
        return str(your_id)
    
    def load_spawns(self, spawn_list=None):
        """
        Loads all of the spawns into this room, from either the given spawn_list
        or the database.
        """
        if not spawn_list:
            spawn_list = self.world.db.select('* FROM room_spawns WHERE room=?', [self.dbid])
        self.world.log.debug(spawn_list) 
        #Build a dictionary of what spawns where (room, another item, an npc) which we will
        #call the dependencies. We need to build this list since self.new_spawn() needs 
        #objects for 'containers' instead of the string representations. Our 'containers'
        #don't exist yet. We will need to build spawns first, then use 'dependencies' to
        # add them later.
        dependencies = {}
        for each in spawn_list:
            dependencies[each['id']] = each['container']
            del each['container']
        self.world.log.debug("Spawn_Dependencies {Spawn_id:container} ---: " + str(dependencies))  
        #Build spawns and save them.
        for row in spawn_list:
            row['room'] = self
            area = self.world.get_area(row['spawn_object_area'])
            if area:
                obj = getattr(area, row['spawn_type'] + "s").get(row['spawn_object_id'])
                if obj:
                    row['obj'] = obj
                    self.world.log.debug(row)
                    self.new_spawn(row)
        #Add spawns to their containers and save them.               
        for spawn_id, cont in dependencies.items():
            if cont:
                spawn = self.spawns.get(spawn_id)
                spawn.container = self.spawns.get(cont)
                spawn.container.add_nested_spawn(self.spawns.get(spawn_id))
                spawn.save()
    
    
    def clean_spawns(self):
        """Make sure that all of the spawns for this room are valid, and
        remove the ones that aren't.
        """
        room_spawns = self.spawns.values()
        for spawn in room_spawns:
            # Make sure any spawns that have nested spawns still have their
            # container item_type -- if they don't, we need to remove them
            # and their nested spawns, because otherwise things will break
            # when they try to add other items to a container object that
            # doesn't exist.
            if spawn.nested_spawns:
                if not spawn.spawn_object.has_type('container'):
                    # Somehow the container item type was removed from this
                    # object (perhaps a builder edited it and forgot to
                    # remove this spawn). We should delete all spawns that
                    # were supposed to have objects spawned inside this one
                    for sub_spawn in spawn.nested_spawns:
                        if sub_spawn.id in self.spawns:
                            sub_spawn.destruct()
                            del self.spawns[sub_spawn.id]
                    spawn.destruct()
                    del self.spawns[spawn.id]
    
    def reset(self):
        """Reset (or respawn) all of the items and npc's that are on this 
        room's spawn lists.
        """
        # reset exits back to default state
        for exit in self.exits.values():
            if exit:
                exit.reset()
        # reset spawns
        self.clean_spawns()
        room_id = '%s,%s' % (self.id, self.area.name)
        for item in self.items:
            if item.has_type('container'):
                if item.spawn_id and (item.spawn_id.startswith(room_id)):
                    self.item_purge(item)
        present_obj = [item.spawn_id for item in self.items if item.spawn_id]
        present_obj.extend([npc.spawn_id for npc in self.npcs if npc.spawn_id])
        for spawn in self.spawns.values():
            if spawn.spawn_id not in present_obj and \
               (spawn.get_spawn_point() == 'in room'):
                if spawn.spawn_type == 'npc':
                    npc = spawn.spawn()
                    npc.location = self
                    self.npcs.append(npc)
                else:
                    self.items.append(spawn.spawn())
    
#************** Character Management **************
    def add_char(self, char, prev_room='void'):
        """Adds a character to this room.
        char -- character object to be added
        prev_room -- the room the character was in before they transitioned to
            this room; should be a string in the format '<room-id>_<area-name>'
        """
        if char.is_npc():
            self.npcs.append(char)
        else:
            self.players[char.name] = char
            self.area.times_visited_since_reset += 1
            self.fire_event('pc_enter', {'player': char, 'from': prev_room})
    
    def remove_char(self, char):
        """Removes a character from this room.
        char -- character object to be removed.
        """
        if char.is_npc():
            if char in self.npcs:
                self.npcs.remove(char)
        else:
            if self.players.get(char.name):
                del self.players[char.name]
    
    def get_player(self, keyword):
        """Get a player from this room if their name is equal to the keyword given."""
        keyword = keyword.strip().lower()
        return self.players.get(keyword)
    
    def get_npc_by_kw(self, keyword):
        """Get an NPC from this room if its name is equal to the keyword given."""
        keyword = keyword.strip().lower()
        for npc in self.npcs:
            if keyword in npc.keywords:
                return npc
        return None
    
    def fire_event(self, event_name, args):
        """Tell all of the npcs in my list that I got an event!"""
        for npc in self.npcs:
            npc.notify(event_name, args)
    
    def tell_room(self, message, exclude_list=[], teller=None):
        """Echo something to everyone in the room, except the people on the exclude list."""
        for person in self.players.values():
            if (person.name not in exclude_list) and (person.position[0] != 'sleeping'):
                person.update_output(message)
        self.fire_event('hears', {'string': message, 'teller': teller})
    
#************** Item Management **************
    def item_add(self, item):
        """Add an item to this room."""
        self.items.append(item)
    
    def item_remove(self, item):
        """Remove an item from this room."""
        if item in self.items:
            self.items.remove(item)
    
    def item_purge(self, item):
        """Delete this object from the room and the db, if it exists there."""
        if item in self.items:
            self.items.remove(item)
            if item.has_type('container'):
                container = item.item_types.get('container')
                container.destroy_inventory()
            item.destruct()
    
    def get_item_by_kw(self, keyword):
        """Get an item from this room they keyword given matches its keywords."""
        keyword = keyword.strip().lower()
        for item in self.items:
            if keyword in item.keywords:
                return item
        return None
    
#************** MISC **************
    def check_for_keyword(self, keyword):
        """Return the first instance of an item, npc, or player that matches the
        keyword. If nothing in the room matches the keyword, return None.
        """
        # check the items in the room first
        item = self.get_item_by_kw(keyword)
        if item: return item
        
        # then check the npcs in the room
        npc = self.get_npc_by_kw(keyword)
        if npc: return npc
        
        # then check the PCs in the room
        player = self.get_player(keyword)
        if player: return player
        
        # If we didn't match any of the above, return None
        return None
    
    def purge_room(self):
        """Delete all objects and npcs in this room."""
        # When npcs are loaded into the room, they're not saved to the db
        # so we can just wipe the memory instances of them
        self.npcs = []
        # The items in the room may have been dropped by a player (and would
        # therefore have been in the game_item db table). We need
        # to make sure we delete the item from the db if it has an entry.
        for i in range(len(self.items)):
            self.item_purge(self.items[0])
    

model_list.register(Room)
