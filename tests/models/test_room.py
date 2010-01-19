from shinymud.lib.world import *
from shinymud.models.user import *
from shinymud.models.room import *
from shinymud.commands import *
from unittest import TestCase
from shinymud.lib.db import DB
from shinymud.models.schema import initialize_database

class TestRoom(TestCase):
    def setUp(self):
        self.world = World()
        self.world.db = DB(':memory:')
        initialize_database(self.world.db.conn)
        self.area = Area.create('blarg')
        self.room = self.area.new_room()
    
    def tearDown(self):
        World._instance = None
    
    def test_add_reset_item_inroom(self):
        """Test adding a reset for an item, with a spawn point 'in room'."""
        item = self.area.new_item()
        message = self.room.add_reset('for item %s' % item.id)
        exp_message = ('A room reset has been added for '
                       '%s number %s.\n' % ('item', item.id)
                      )
        # Make sure we get the expected result message
        self.assertEqual(message, exp_message)
        # We should only have one reset in room.resets
        self.assertEqual(len(self.room.resets.items()), 1)
        reset = self.room.resets.values()[0]
        # The object this reset points to should be equal to the item
        # we just created
        self.assertEqual(reset.reset_object, item)
        # its spawn point should be 'in room'
        self.assertEqual(reset.get_spawn_point(), 'in room')
    
    def test_add_reset_item_nested_in_item(self):
        item = self.area.new_item()
        container = self.area.new_item()
        container.add_type('container')
        
        message1 = self.room.add_reset('for item %s' % container.id)
        exp_message1 = ('A room reset has been added for '
                        '%s number %s.\n' % ('item', container.id)
                       )
        self.assertEqual(message1, exp_message1)
        message2 = self.room.add_reset('for item %s in reset %s' % (item.id, 
                                                                    '1'))
        exp_message2 = ('A room reset has been added for '
                        '%s number %s.\n' % ('item', item.id)
                       )
        self.assertEqual(message2, exp_message2)
        # Make sure the room has 2 resets in its list
        self.assertEqual(len(self.room.resets.items()), 2)
        reset1 = self.room.resets.get(1)
        reset2 = self.room.resets.get(2)
        self.assertTrue('container' in reset1.reset_object.item_types)
        # reset1 should have one nested reset
        self.assertEqual(len(reset1.nested_resets), 1)
        self.assertEqual(reset1.get_spawn_point(), 'in room')
        self.assertEqual(reset1, reset2.container)
        self.assertEqual(reset2.get_spawn_point(),
                         'into %s (R:%s)' % (container.name,
                                             str(reset1.dbid))
                        )
    
    def test_remove_reset(self):
        item = self.area.new_item()
        self.room.add_reset('for item %s' % item.id)
        self.assertEqual(len(self.room.resets.items()), 1)
        db_reset = self.world.db.select('* FROM room_resets WHERE dbid=?', [1])
        self.assertEqual(len(db_reset), 1)
        self.room.remove_reset('1')
        # The room should now have an empty resets list
        self.assertEqual(len(self.room.resets.items()), 0)
        # The reset should no longer be in the database
        db_reset = self.world.db.select('* FROM room_resets WHERE dbid=?', [1])
        self.assertEqual(len(db_reset), 0)
    
    def test_remove_nested_reset(self):
        item1 = self.area.new_item()
        item2 = self.area.new_item()
        container = self.area.new_item()
        container.add_type('container')
        self.room.add_reset('for item %s' % container.id)
        self.room.add_reset('for item %s inside %s' % (item1.id, '1'))
        self.room.add_reset('for item %s inside %s' % (item2.id, '1'))
        self.assertEqual(len(self.room.resets.items()), 3)
        c_reset = self.room.resets.get(1)
        reset1 = self.room.resets.get(2)
        reset2 = self.room.resets.get(3)
        self.assertEqual(c_reset, reset1.container)
        self.assertEqual(c_reset, reset2.container)
        self.assertEqual(len(c_reset.nested_resets), 2)
        
        message1 = self.room.remove_reset('2')
        message2 = self.room.remove_reset('3')
        self.assertEqual('Room reset 2 has been removed.\n', message1)
        self.assertEqual('Room reset 3 has been removed.\n', message2)
        self.assertTrue(c_reset in self.room.resets.values())
        self.assertEqual(len(self.room.resets.items()), 1)
        self.assertEqual(len(c_reset.nested_resets), 0)
    
    def test_remove_nested_reset_container(self):
        pass
    
    def test_reset(self):
        pass
    

