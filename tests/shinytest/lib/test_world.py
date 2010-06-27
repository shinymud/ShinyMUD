from shinytest import ShinyTestCase


class TestReset(ShinyTestCase):
    def test_tell_players(self):
        from shinymud.models.player import Player
        from shinymud.modes.build_mode import BuildMode
        from shinymud.modes.init_mode import InitMode
        from shinymud.data.config import wecho_color, clear_fcolor
        bob = Player(('bob', 'bar'))
        alice = Player(('alice', 'bar'))
        self.world.player_add(bob)
        self.world.player_add(alice)
        
        bob.mode = None
        bob.outq = []
        alice.mode = None
        alice.outq = []
        
        self.world.tell_players('hello world!')
        echo = wecho_color + 'hello world!' + clear_fcolor + '\r\n'
        self.assertTrue(echo in bob.outq)
        self.assertTrue(echo in alice.outq)
        
        bob.mode = InitMode(bob)
        bob.outq = []
        alice.outq = []
        
        self.world.tell_players('hello all!')
        echo = wecho_color + 'hello all!' + clear_fcolor + '\r\n'
        self.assertTrue(echo not in bob.outq)
        self.assertTrue(echo in alice.outq)
        
        bob.mode = BuildMode(bob)
        bob.outq = []
        alice.outq = []
        
        self.world.tell_players('hello!', ['alice'])
        echo = wecho_color + 'hello!' + clear_fcolor + '\r\n'
        self.assertTrue(echo in bob.outq)
        self.assertTrue(echo not in alice.outq)
    
    def test_destroy_area(self):
        from shinymud.models.area import Area
        area = Area.create({'name': 'foo'})
        room = area.new_room()
        room2 = area.new_room()
        room3 = area.new_room()
        item = area.new_item()
        npc = area.new_npc()
        self.assertTrue(npc.dbid)
        script = area.new_script()
        room.link_exits('north', room2)
        room.link_exits('south', room3)
        room.build_add_spawn('for item 1')
        room2.build_add_spawn('for npc 1')
        npc.build_add_event('pc_enter call script 1')
        item.build_add_type('portal')
        
        db_spawns = self.world.db.select('* FROM room_spawns')
        db_exits = self.world.db.select('* from room_exit')
        db_rooms = self.world.db.select('* from room')
        db_areas = self.world.db.select('* from area')
        db_scripts = self.world.db.select('* from script')
        db_npcs = self.world.db.select('* from npc')
        db_items = self.world.db.select('* from build_item')
        db_item_types = self.world.db.select('* from portal')
        
        self.assertEqual(len(db_rooms), 3)
        self.assertEqual(len(db_spawns), 2)
        self.assertEqual(len(db_exits), 4)
        self.assertEqual(len(db_rooms), 3)
        self.assertEqual(len(db_areas), 1)
        self.assertEqual(len(db_scripts), 1)
        self.assertEqual(len(db_items), 1)
        self.assertEqual(len(db_item_types), 1)
        
        echo = self.world.destroy_area('foo', 'test')
        self.assertEqual(echo, 'Area foo was successfully destroyed. I hope you meant to do that.\n')
        
        db_spawns = self.world.db.select('* FROM room_spawns')
        db_exits = self.world.db.select('* from room_exit')
        db_rooms = self.world.db.select('* from room')
        db_areas = self.world.db.select('* from area')
        db_scripts = self.world.db.select('* from script')
        db_npcs = self.world.db.select('* from npc')
        db_items = self.world.db.select('* from build_item')
        db_item_types = self.world.db.select('* from portal')
        
        self.assertFalse(self.world.area_exists('foo'))
        self.assertEqual(len(db_rooms), 0)
        self.assertEqual(len(db_spawns), 0)
        self.assertEqual(len(db_exits), 0)
        self.assertEqual(len(db_areas), 0)
        self.assertEqual(len(db_scripts), 0)
        self.assertEqual(len(db_items), 0)
        self.assertEqual(len(db_item_types), 0)
