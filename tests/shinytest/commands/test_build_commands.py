from shinytest import ShinyTestCase

import os

class TestBuildCommands(ShinyTestCase):
    def setUp(self):
        ShinyTestCase.setUp(self)
        # add a builder
        from shinymud.data import config
        from shinymud.models.player import Player
        from shinymud.models.area import Area
        from shinymud.commands.build_commands import build_list
        from shinymud.modes.build_mode import BuildMode
        self.bob = Player(('bob', 'bar'))
        self.bob.mode = None
        self.bob.playerize({'name':'bob'})
        self.world.player_add(self.bob)
        self.bob.mode = BuildMode(self.bob)
        self.bob.permissions = self.bob.permissions | config.BUILDER
    
    def _clean_test_file(self, path):
        try:
            os.remove(path)
        except Exception, e:
            self.world.log.debug('Error removing test file:' + str(e))
    
    def test_edit_command(self):
        from shinymud.data import config
        from shinymud.models.player import Player
        from shinymud.models.area import Area
        from shinymud.commands.build_commands import Edit
        from shinymud.modes.build_mode import BuildMode

        # create an area 
        area = Area.create({'name':'dessert'})
        
        # Make sure that we don't die with no args!
        Edit(self.bob, '', 'edit').run()
        empty = 'Type "help edit" to get help using this command.'
        self.assertTrue(empty in self.bob.outq)
        
        # Bob should fail to be able to edit the area, since he's not yet on
        # the area's builder's list
        fail = 'You aren\'t allowed to edit someone else\'s area.'
        Edit(self.bob, 'area dessert', 'edit').run()
        self.assertTrue(fail in self.bob.outq)
        
        # Bob should now succeed in editing the area
        success = 'Now editing area "dessert".'
        area.builders.append('bob')
        Edit(self.bob, 'area dessert', 'edit').run()
        self.assertEqual(self.bob.mode.edit_area, area)
        self.assertTrue(success in self.bob.outq)
    
    def test_link_command(self):
        from shinymud.data import config
        from shinymud.models.player import Player
        from shinymud.models.area import Area
        from shinymud.commands.build_commands import Edit, Link
        from shinymud.modes.build_mode import BuildMode

        area = Area.create({'name':'pie'})
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
        self.bob.world.log.debug(self.bob.outq)
        east = room1.exits.get('east')
        self.bob.world.log.debug(east)
        self.assertTrue(east)
        self.assertEqual(east.linked_exit, 'west')
        self.assertEqual(east.to_room, room2)
        
        # Now we're linking to another room in a different area as the one
        # being edited
        area2 = Area.create({'name':'cake'})
        cake_room = area2.new_room()
        Link(self.bob, 
             'west exit to room %s from area %s' % (cake_room.id, 
                                                    cake_room.area.name),
             'link').run()
        self.bob.world.log.debug(self.bob.outq)
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
        self.bob.world.log.debug(self.bob.outq)
        fail = ("This room's (id: 1) west exit is already linked to room 1, "
                "area cake.\nYou must unlink it before linking it to a new room.")
        self.assertTrue(fail in self.bob.outq)
    
    def test_unlink_command(self):
        from shinymud.data import config
        from shinymud.models.player import Player
        from shinymud.models.area import Area
        from shinymud.commands.build_commands import Edit, Link, Unlink
        from shinymud.modes.build_mode import BuildMode
        area = Area.create({'name':'pie'})
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
    
    def test_export_command(self):
        from shinymud.models.area import Area
        from shinymud.commands.build_commands import Export
        from shinymud.data.config import AREAS_EXPORT_DIR
        a = Area.create({'name': 'superlongtestfoo'})
        
        # Make sure we fail if the area doesn't actually exist
        Export(self.bob, 'area bar', 'export').run()
        self.world.log.debug(self.bob.outq)
        self.assertTrue('Area "bar" doesn\'t exist.' in self.bob.outq)
        
        # We should fail if the player gives us incorrect syntax
        error = 'Try: "export <area/player> <name>", or see "help export".'
        Export(self.bob, 'lol', 'export').run()
        self.assertTrue(error in self.bob.outq)
        
        # Character exporting doesn't exist yet, but make sure the player gets
        # the correct logic branch if they try it
        error = 'Invalid type "char". See "help export".'
        Export(self.bob, 'char bob', 'export').run()
        self.assertTrue(error in self.bob.outq)
        
        # Make sure exporting actually works
        self.assertTrue(self.world.area_exists('superlongtestfoo'))
        Export(self.bob, 'area superlongtestfoo', 'export').run()
        self.world.log.debug(self.bob.outq)
        self.assertTrue(self.bob.outq[-1].startswith('Export complete!'))
        # make sure the file got created
        self.assertTrue(os.path.exists(AREAS_EXPORT_DIR + '/superlongtestfoo_area.shiny_format'))
        self._clean_test_file(AREAS_EXPORT_DIR + '/superlongtestfoo_area.shiny_format')
    
    def test_import_command(self):
        from shinymud.models.area import Area
        from shinymud.commands.build_commands import Import, Export
        from shinymud.data.config import AREAS_EXPORT_DIR, AREAS_IMPORT_DIR
        
        Area.create({'name': 'superlongtestbar', 'description': 'superlongtestbar is cool.'})
        Area.create({'name': 'superlongtestexistenz'})
        Export(self.bob, 'area superlongtestbar', 'import').run()
        self.assertTrue(os.path.exists(AREAS_EXPORT_DIR + '/superlongtestbar_area.shiny_format'))
        self.world.destroy_area('superlongtestbar', 'test')
        self.assertFalse(self.world.area_exists('superlongtestbar'))
        
        # Make sure we fail if the area file doesn't actually exist
        Import(self.bob, 'area superlongtestfoo', 'import').run()
        self.world.log.debug(self.bob.outq)
        self.assertTrue('Error: file superlongtestfoo_area.shiny_format does not exist.' in self.bob.outq)
        
        # Make sure we fail if the player gives incorrect syntax
        Import(self.bob, 'superlongtestbar', 'import').run()
        error = 'Invalid type "superlongtestbar". See "help export".'
        self.assertTrue(error in self.bob.outq)
        
        # Make sure we fail if the area already exists in the MUD
        Import(self.bob, 'area superlongtestexistenz', 'import').run()
        error = 'Area "superlongtestexistenz" already exists in your game.'
        self.assertTrue(error in self.bob.outq)
        
        # Make sure the import command actually works
        Import(self.bob, 'area superlongtestbar', 'import').run()
        b = self.world.get_area('superlongtestbar')
        self.world.log.debug(self.bob.outq)
        self.assertTrue(b)
        self.assertEqual(b.description, 'superlongtestbar is cool.')
        
        
        self.world.destroy_area('superlongtestbar', 'test')
        Import(self.bob, 'area superlongtestbar from email', 'import').run()
        error = 'Cannot find transport: load_email'
        self.world.log.debug(self.bob.outq)
        self.assertTrue(error in self.bob.outq)
        
        self._clean_test_file(AREAS_EXPORT_DIR + '/superlongtestbar_area.shiny_format')
    

