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
        self.assertEqual(i1.item_types['furniture'].capacity, 5)
        
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
