from shinytest import ShinyTestCase


class TestArea(ShinyTestCase):
    def test_create_area(self):
        from shinymud.models.area import Area
        area = Area.create({'name': 'foo'})
        #make sure that the area exists in the world
        self.assertTrue(self.world.area_exists('foo'))
        a = self.world.get_area('foo')
        #make sure that the area was saved to the database
        row = self.world.db.select("* from area where name=?", ['foo'])[0]
        self.assertTrue(row)
    
    def test_build_set_levelrange(self):
        from shinymud.models.area import Area
        area = Area.create({'name': 'foo'})
        echo = area.build_set_levelrange('Kittens')
        # Make sure we got a string response back to give to the user
        self.assertTrue(isinstance(echo, basestring))
        # Make sure it was set in memory
        self.assertEqual('Kittens', area.level_range)
        # Make sure it was saved to the db correctly
        row = self.world.db.select("level_range from area where name=?",
                                   [area.name])[0]
        self.assertEqual(row['level_range'], 'Kittens')
    
    def test_build_add_builder(self):
        from shinymud.models.area import Area
        area = Area.create({'name': 'foo'})
        echo = area.build_add_builder('bob')
        # Make sure we got a string response back to give to the user
        self.assertTrue(isinstance(echo, basestring))
        # Make sure it was set in memory
        self.assertTrue('bob' in area.builders)
        # Make sure it was saved to the db correctly
        row = self.world.db.select("builders from area where name=?",
                                   [area.name])[0]
        builders = row['builders'].split(',')
        self.assertTrue('bob' in builders)
    
    def test_build_set_title(self):
        from shinymud.models.area import Area
        area = Area.create({'name': 'foo'})
        title = "Best area ever!"
        echo = area.build_set_title(title)
        # Make sure we got a string response back to give to the user
        self.assertTrue(isinstance(echo, basestring))
        # Make sure it was set in memory
        self.assertEqual(title, area.title)
        # Make sure it was saved to the db correctly
        row = self.world.db.select("title from area where name=?", [area.name])[0]
        self.assertEqual(row['title'], title)
    
    def test_build_remove_builder(self):
        from shinymud.models.area import Area
        area = Area.create({'name': 'foo'})
        area.build_add_builder('bob')
        self.assertTrue('bob' in area.builders)
        echo = area.build_remove_builder('bob')
        # Make sure we got a string response back to give to the user
        self.assertTrue(isinstance(echo, basestring))
        # Make sure it was set in memory
        self.assertFalse('bob' in area.builders)
        # Make sure it was saved to the db correctly
        row = self.world.db.select("builders from area where name=?",
                                   [area.name])[0]
        self.assertTrue(row['builders'] is None)
    
    
#********** Test Room management functions #**********
    def test_new_room(self):
        from shinymud.models.area import Area
        from shinymud.models.room import Room
        area = Area.create({'name': 'foo'})
        # Test without room args
        room = area.new_room()
        self.assertTrue(isinstance(room, Room))
        self.assertTrue(room is area.get_room(room.id))
        row = self.world.db.select('* from room where area=?', [area.name])
        self.assertEqual(len(row), 1)
        # Test with room args
        room2 = area.new_room({'name': 'awesome room', 'description': 'food', 'id': '2'})
        self.assertTrue(room2 is area.get_room(room2.id))
        self.assertEqual(room2.name, 'awesome room')
        self.assertEqual(room2.description, 'food')
        
    def test_ten_new_rooms(self):
        from shinymud.models.area import Area
        from shinymud.models.room import Room
        area = Area.create({'name': 'foo'})
        for i in range(11):
            area.new_room()
        self.assertEqual(len(area.rooms.keys()), 11)
        
    
    def test_destroy_room(self):
        from shinymud.models.area import Area
        area = Area.create({'name': 'foo'})
        room = area.new_room()
        room2 = area.new_room()
        item = area.new_item()
        room.link_exits('north', room2)
        self.assertTrue(room.exits.get('north'))
        room.build_add_spawn('for item 1')
        self.assertTrue(room.spawns.get('1'))
        area.destroy_room(room.id)
        self.assertFalse(area.get_room(room.id))
        db_spawns = self.world.db.select('* FROM room_spawns')
        self.assertFalse(db_spawns)
        db_exits = self.world.db.select('* from room_exit')
        self.assertFalse(db_exits)
        
    
