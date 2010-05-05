from shinymud.lib.world import *
from shinymud.data.config import *
from shinymud.models.player import *
from shinymud.models.area import *
from shinymud.lib.db import DB
from shinymud.models.schema import initialize_database
from shinymud.commands.build_commands import *
from shinymud.modes.build_mode import *

from unittest import TestCase

class TestBuildCommands(TestCase):
    def setUp(self):
        self.world = World()
        self.world.db = DB(':memory:')
        initialize_database(self.world.db.conn)
        # add a builder
        self.bob = Player(('bob', 'bar'))
        self.bob.mode = None
        self.bob.playerize(name='bob')
        self.world.player_add(self.bob)
        self.bob.mode = BuildMode(self.bob)
        self.bob.permissions = self.bob.permissions | BUILDER
    
    def tearDown(self):
        World._instance = None
    
    def test_edit_command(self):
        # create an area 
        area = Area.create('dessert')
        
        # Make sure that we don't die with no args!
        Edit(self.bob, '', 'edit').run()
        empty = 'Type "help edit" to get help using this command.\r\n'
        self.assertTrue(empty in self.bob.outq)
        
        # Bob should fail to be able to edit the area, since he's not yet on
        # the area's builder's list
        fail = 'You aren\'t allowed to edit someone else\'s area.\r\n'
        Edit(self.bob, 'area dessert', 'edit').run()
        self.assertTrue(fail in self.bob.outq)
        
        # Bob should now succeed in editing the area
        success = 'Now editing area "dessert".\r\n'
        area.builders.append('bob')
        Edit(self.bob, 'area dessert', 'edit').run()
        self.assertEqual(self.bob.mode.edit_area, area)
        self.assertTrue(success in self.bob.outq)
    
    def test_link_command(self):
        area = Area.create('pie')
        room1 = area.new_room()
        area.builders.append('bob')
        
        # Make sure bob is editing a room
        Edit(self.bob, 'area pie', 'edit').run()
        Edit(self.bob, 'room %s' % room1.id, 'edit').run()
        
        # By passing only a direction, this should create a new room
        # and link its south exit to the current room's north exit
        Link(self.bob, 'north', 'link').run()
        # self.bob.log.debug(self.bob.outq)
        north = room1.exits.get('north')
        self.assertTrue(north)
        self.assertEqual(north.linked_exit, 'south')
        self.bob.outq = []
        
        # Now we're linking to another room in the same area as the one being
        # edited
        room2 = area.new_room()
        Link(self.bob, 'east exit to room %s' % room2.id, 'link').run()
        self.bob.log.debug(self.bob.outq)
        east = room1.exits.get('east')
        self.bob.log.debug(east)
        self.assertTrue(east)
        self.assertEqual(east.linked_exit, 'west')
        self.assertEqual(east.to_room, room2)
        
        # Now we're linking to another room in a different area as the one
        # being edited
        area2 = Area.create('cake')
        cake_room = area2.new_room()
        Link(self.bob, 
             'west exit to room %s from area %s' % (cake_room.id, 
                                                    cake_room.area.name),
             'link').run()
        self.bob.log.debug(self.bob.outq)
        west = room1.exits.get('west')
        self.assertTrue(west)
        self.assertEqual(west.linked_exit, 'east')
        self.assertEqual(west.to_room, cake_room)
        
        self.bob.outq = []
        
        # Linking should fail if we try to link to a pre-linked room 
        Link(self.bob, 
             'west exit to room %s from area %s' % (cake_room.id, 
                                                    cake_room.area.name),
             'link').run()
        self.bob.log.debug(self.bob.outq)
        fail = ("This room's (id: 1) west exit is already linked to room 1, "
                "area cake.\r\n"
                "You must unlink it before linking it to a new room.\r\n")
        self.assertTrue(fail in self.bob.outq)
    
    def test_unlink_command(self):
        area = Area.create('pie')
        room1 = area.new_room()
        area.builders.append('bob')
        Edit(self.bob, 'area pie', 'edit').run()
        Edit(self.bob, 'room %s' % room1.id, 'edit').run()
        
        Link(self.bob, 'north', 'link').run()
        room2 = room1.exits.get('north').to_room
        self.assertTrue(room2.exits['south'].linked_exit)
        self.assertTrue(room1.exits['north'].linked_exit)
        
        Unlink(self.bob, 'north', 'unlink').run()
        self.assertEqual(room1.exits.get('north'), None)
        self.assertEqual(room2.exits.get('south'), None)
        
    
