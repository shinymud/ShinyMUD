from shinymud.lib.world import *
from shinymud.models.reset import *
from shinymud.models.area import *
from shinymud.models.npc import *
from shinymud.models.item import *
from shinymud.models.room import *
from shinymud.commands import *
from shinymud.lib.db import DB
from shinymud.models.schema import initialize_database
from unittest import TestCase

class TestReset(TestCase):
    def setUp(self):
        self.world = World()
        self.world.db = DB(':memory:')
        initialize_database(self.world.db.conn)
        self.area = Area.create('foo')
        self.room = self.area.new_room()
        self.item = self.area.new_item()
        self.npc = self.area.new_npc()
    
    def tearDown(self):
        World._instance = None
    
    def test_add_nested_reset(self):
        reset1 = self.room.new_reset({'id': self.room.get_reset_id(), 
                             'room':self.room, 
                             'obj': self.item, 
                             'reset_type': 'item'})
        reset2 = self.room.new_reset({'id': self.room.get_reset_id(), 
                             'room':self.room, 
                             'obj': self.item, 
                             'reset_type':'item'})
        reset1.add_nested_reset(reset2)
        
        self.assertTrue(reset2 in reset1.nested_resets)
    
    def test_add_nested_reset_with_item_container(self):
        item2 = self.area.new_item()
        item2.add_type('container')
        reset1 = self.room.new_reset({'id': self.room.get_reset_id(), 
                             'room':self.room, 
                             'obj': item2, 
                             'reset_type': 'item'})
        reset2 = self.room.new_reset({'id': self.room.get_reset_id(), 
                                      'room':self.room, 
                                      'obj': self.item, 
                                      'reset_type': 'item',
                                      'container': reset1})
        
        expected_spawn_point_reset2 = 'into %s (R:%s)' % (reset1.reset_object.name, 
                                                          reset1.id)
        expected_spawn_point_reset1 = 'in room'
        
        # Make sure that the the containee has its container
        # attribute set
        self.assertTrue(reset2.container)
        # Make sure the container attribute points back to reset 1
        self.assertEqual(reset2.container, reset1)
        # Make sure the spawn point got set correctly
        self.assertEqual(reset2.get_spawn_point(),
                         expected_spawn_point_reset2)
        self.assertEqual(reset1.get_spawn_point(),
                         expected_spawn_point_reset1)
    
    def test_add_nested_reset_with_npc_container(self):
        reset1 = self.room.new_reset({'id': self.room.get_reset_id(),
                                      'room': self.room,
                                      'obj': self.npc,
                                      'reset_type': 'npc'})
        reset2 = self.room.new_reset({'id': self.room.get_reset_id(),
                                      'room': self.room,
                                      'obj': self.item,
                                      'reset_type': 'item',
                                      'container': reset1})
        # reset1 = Reset(self.room, self.npc, 'npc')
        # reset1.save()
        # reset2 = Reset(self.room, self.item, 'item', reset1)
        # reset2.save()
        
        # Make sure that the the containee has its container
        # attribute set
        self.assertTrue(reset2.container)
        self.assertEqual(reset2.container, reset1)
        expected_spawn_point_reset2 = 'into %s\'s inventory (R:%s)' % (reset1.reset_object.name, 
                                                                       reset1.id)
        expected_spawn_point_reset1 = 'in room'
        
        self.assertEqual(reset2.get_spawn_point(),
                         expected_spawn_point_reset2)
        self.assertEqual(reset1.get_spawn_point(),
                         expected_spawn_point_reset1)
    
    def test_remove_nested_reset(self):
        reset1 = self.room.new_reset({'id': self.room.get_reset_id(), 
                             'room':self.room, 
                             'obj': self.item, 
                             'reset_type': 'item'})
        reset2 = self.room.new_reset({'id': self.room.get_reset_id(), 
                             'room':self.room, 
                             'obj': self.item, 
                             'reset_type':'item'})
        reset1.add_nested_reset(reset2)
        reset1.remove_nested_reset(reset2)
        
        self.assertEqual(reset1.nested_resets, [])
    
    def test_save(self):
        pass
    
    def test_to_dict(self):
        reset = self.room.new_reset({'id': self.room.get_reset_id(), 
                                     'room':self.room, 
                                     'obj': self.item, 
                                     'reset_type': 'item'})
        d = reset.to_dict()
    
    def test_spawn_npc(self):
        reset1 = self.room.new_reset({'id': self.room.get_reset_id(), 
                                      'room':self.room, 
                                      'obj': self.npc, 
                                      'reset_type': 'npc'})
        npc2 = reset1.spawn()
        self.assertTrue(isinstance(npc2, Npc))
    
    def test_spawn_item(self):
        reset1 = self.room.new_reset({'id': self.room.get_reset_id(), 
                             'room':self.room, 
                             'obj': self.item, 
                             'reset_type': 'item'})
        item1 = reset1.spawn()
        self.assertTrue(isinstance(item1, Item))
        
        # Next test 
