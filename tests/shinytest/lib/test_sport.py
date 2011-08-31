from shinytest import ShinyTestCase

import os
import shutil

class TestSport(ShinyTestCase):
    def test_shiny_area_format(self):
        """Make sure the read/write formatters for ShinyAreaFormat work correctly.
        """
        from shinymud.lib.sport_plugins.formatters.area_write_shiny_format import format as writeshiny
        from shinymud.lib.sport_plugins.formatters.area_read_shiny_format import format as readshiny
        area = self._create_area()
        area_txt = writeshiny(area)
        self.world.log.debug(area_txt)
        self.world.destroy_area(area.name, 'test')
        self.assertFalse(self.world.area_exists('foo'))
        readshiny(self.world, area_txt)
        
        self.assertTrue(self.world.area_exists('foo'))
        nufoo = self.world.get_area('foo')
        
        # Test to make sure all scripts are good
        self.assertEqual(len(nufoo.scripts.keys()), 1)
        s1 = nufoo.get_script('1')
        self.assertEqual('say ...', s1.body)
        self.assertEqual('bar', s1.name)
        
        # Test to make sure all items are good
        i1 = nufoo.get_item('1')
        self.assertEqual('chair', i1.name)
        self.assertTrue(i1.has_type('furniture'))
        self.assertEqual(i1.item_types['furniture'].capacity, 1)
        
        # Make sure the npcs come back good
        n1 = nufoo.get_npc('1')
        self.assertEqual('Link', n1.name)
        self.assertEqual('This little elf-man has some hearts tattooed on his arm.', n1.description)
        nevent = n1.events['hears'][0]
        self.assertEqual(nevent.event_trigger, 'hears')
        self.assertTrue(nevent.script is s1)
        self.assertEqual(nevent.condition, 'Gannon')
        
        # Go through the rooms...
        r1 = nufoo.get_room('1')
        r2 = nufoo.get_room('2')
        self.assertEqual('Room 1', r1.name)
        self.assertEqual('Cool room.', r1.description)
        self.assertTrue(r1.exits['north'].to_room is r2)
        self.assertTrue(r2.exits['south'].to_room is r1)
        self.assertTrue(r1.spawns['1'].spawn_object is i1)
        self.assertTrue(r2.spawns['1'].spawn_object is n1)
        
        # Make sure the spawns were reset properly
        self.assertEqual(len(r1.items), 1)
        self.assertEqual(len(r2.npcs), 1)
    
    def _create_area(self):
        from shinymud.models.area import Area
        
        area = Area.create({'name': 'foo'})
        # setup scripts
        script = area.new_script()
        script.name = 'bar'
        script.body = 'say ...'
        script.save()
        # setup items
        item = area.new_item()
        item.build_set_name('chair')
        item.build_add_type('furniture')
        item.item_types['furniture'].capacity = 5
        item.save()
        # setup npcs
        npc = area.new_npc()
        npc.name = 'Link'
        npc.description = 'This little elf-man has some hearts tattooed on his arm.'
        npc.save()
        npc.build_add_event("hears 'Gannon' call script 1")
        
        # setup rooms
        rd = {'id': '1', 'name': 'Room 1', 'description': 'Cool room.'}
        room = area.new_room(rd)
        room2 = area.new_room()
        room.link_exits('north', room2)
        room.build_add_spawn('item 1')
        room2.build_add_spawn('npc 1')
        
        return area
    
    def _clean_test_file(self, path):
        try:
            os.remove(path)
        except Exception, e:
            self.world.log.debug('Error removing test file:' + str(e))
    
    def test_list_areas(self):
        from shinymud.models.area import Area
        from shinymud.lib.sport import export, list_importable
        from shinymud.data.config import AREAS_EXPORT_DIR, AREAS_IMPORT_DIR
        a = Area.create({'name': 'supertestred'})
        b = Area.create({'name': 'supertestblue'})
        export('area', a)
        export('area', b)
        self.world.destroy_area('supertestred', 'test')
        self.world.destroy_area('supertestblue', 'test')
        txt = list_importable('area')
        self.assertNotEqual(txt.find('supertestred'), -1)
        self.assertNotEqual(txt.find('supertestblue'), -1)
        self.world.log.debug(txt)
        
        self._clean_test_file(AREAS_EXPORT_DIR + '/supertestblue_area.shiny_format')
        self._clean_test_file(AREAS_EXPORT_DIR + '/supertestred_area.shiny_format')
    
    def test_inport_dir(self):
        from shinymud.models.area import Area
        from shinymud.lib.sport import export, inport_dir
        from shinymud.data.config import AREAS_EXPORT_DIR
        epath = AREAS_EXPORT_DIR + '/test'
        
        a = Area.create({'name': 'supertestfooarea'})
        b = Area.create({'name': 'supertestbararea'})
        c = Area.create({'name': 'supertestbazarea'})
        export('area', a, dest_path=epath)
        export('area', b, dest_path=epath)
        export('area', c, dest_path=epath)
        self.world.destroy_area('supertestfooarea', 'test')
        self.world.destroy_area('supertestbararea', 'test')
        self.world.destroy_area('supertestbazarea', 'test')
        
        txt = inport_dir('area', source_path=epath)
        self.world.log.debug(txt)
        self.assertTrue(self.world.area_exists('supertestfooarea'))
        self.assertTrue(self.world.area_exists('supertestbararea'))
        self.assertTrue(self.world.area_exists('supertestbazarea'))
        
        shutil.rmtree(epath, True)
    
    def test_shiny_player_format(self):
        from shinymud.lib.sport_plugins.formatters.player_write_shiny_format import format as writeshiny
        from shinymud.lib.sport_plugins.formatters.player_read_shiny_format import format as readshiny
        from shinymud.models.player import Player
        #create a playa
        sven = Player(('foo', 'bar'))
        sven.playerize({'name': 'sven', 'password': 'foo'})
        sven.permissions = 17
        sven.description = "I'm pretty adorable."
        sven.title = 'Super Sven'
        sven.save()
        area = self._create_area()
        sven.item_add(area.get_item('1').load())
        
        txt = writeshiny(sven)
        self.world.log.debug(txt)
        
        sven.destruct()
        # Sven should have been taken out of the database...
        row = self.world.db.select('* from player where name=?', ['sven'])
        self.assertFalse(row)
        row = self.world.db.select('* from game_item where owner=?', [sven.dbid])
        self.assertFalse(row)
        
        result = readshiny(self.world, txt)
        self.world.log.debug(result)
        self.assertEqual(result, 'Character "Sven" has been successfully imported.')
        
        # Sven should now be in the database, but not online
        row = self.world.db.select('* from player where name=?', ['sven'])[0]
        self.assertTrue(row)
        self.assertFalse(self.world.get_player('sven'))
        
        isven = Player(('foo', 'bar'))
        isven.playerize(row)
        
        row = self.world.db.select('* from game_item where owner=?', [isven.dbid])
        self.assertTrue(row)
        
        # Make sure that all attributes we set got imported correctly
        self.assertEqual(sven.password, isven.password)
        self.assertEqual(sven.description, isven.description)
        self.assertEqual(sven.name, isven.name)
        self.assertEqual(sven.title, isven.title)
        self.assertEqual(sven.permissions, isven.permissions)
        
        # Make sure that the inventory was correctly loaded
        self.assertEqual(len(sven.inventory), len(isven.inventory))
        item = isven.inventory[0]
        self.world.log.debug(item.create_save_dict())
        self.world.log.debug(item.item_types)
        self.assertFalse(sven.inventory[0] is isven.inventory[0])
        self.assertEqual(item.name, 'chair')
        self.assertTrue(item.has_type('furniture'))
        self.assertEqual(item.item_types['furniture'].capacity, 5)
    
    def test_shiny_player_format_containers(self):
        """Make sure shiny player format still works when player has containers
        in their inventory.
        """
        from shinymud.lib.sport_plugins.formatters.player_write_shiny_format import format as writeshiny
        from shinymud.lib.sport_plugins.formatters.player_read_shiny_format import format as readshiny
        from shinymud.lib.connection_handlers.shiny_connections import ShinyConnection
        from shinymud.models.player import Player
        sven = Player(('foo', 'bar'))
        sven.playerize({'name': 'sven', 'password': 'foo'})
        sven.save()
        area = self._create_area()
        item1 = area.new_item()
        item1.build_set_keywords('item1')
        item1.build_add_type('container')
        game1 = item1.load()
        
        item2 = area.new_item()
        item2.build_set_keywords('item2')
        item2.build_add_type('container')
        game2 = item2.load()
        self.assertTrue(game1.item_types['container'].item_add(game2))
        
        item3 = area.new_item()
        item3.build_set_keywords('item3')
        game3 = item3.load()
        self.assertTrue(game2.item_types['container'].item_add(game3))
        
        sven.item_add(game1)
        
        txt = writeshiny(sven)
        self.world.log.debug(txt)
        
        sven.destruct()
        
        row = self.world.db.select('* from player where name=?', ['sven'])
        self.assertFalse(row)
        row = self.world.db.select('* from game_item where owner=?', [sven.dbid])
        self.assertFalse(row)
        
        result = readshiny(self.world, txt)
        self.world.log.debug(result)
        self.assertEqual(result, 'Character "Sven" has been successfully imported.')
        row = self.world.db.select('* from player where name=?', ['sven'])[0]
        isven = Player(('foo', 'bar'))
        isven.playerize(row)
        
        self.assertEqual(len(isven.inventory), 1)
        s1 = isven.inventory[0]
        self.assertEqual(s1.keywords, ['item1'])
        s2 = s1.item_types['container'].get_item_by_kw('item2')
        self.assertEqual(s2.keywords, ['item2'])
        s3 = s2.item_types['container'].get_item_by_kw('item3')
        self.assertEqual(s3.keywords, ['item3'])
    
