from shinymud.lib.world import *
from shinymud.models.spawn import *
from shinymud.models.area import *
from shinymud.models.npc import *
from shinymud.models.item import *
from shinymud.models.room import *
from shinymud.commands import *
from shinymud.lib.db import DB
from shinymud.models.schema import initialize_database
from shinytest import ShinyTestCase

class TestSpawn(ShinyTestCase):
    def setUp(self):
        ShinyTestCase.setUp(self)
        self.area = Area.create('foo')
        self.room = self.area.new_room()
        self.item = self.area.new_item()
        self.npc = self.area.new_npc()
        
    def test_add_nested_spawn(self):
        spawn1 = self.room.new_spawn({'id': self.room.get_spawn_id(), 
                             'room':self.room, 
                             'obj': self.item, 
                             'spawn_type': 'item'})
        spawn2 = self.room.new_spawn({'id': self.room.get_spawn_id(), 
                             'room':self.room, 
                             'obj': self.item, 
                             'spawn_type':'item'})
        spawn1.add_nested_spawn(spawn2)
        
        self.assertTrue(spawn2 in spawn1.nested_spawns)
    
    def test_add_nested_spawn_with_item_container(self):
        item2 = self.area.new_item()
        item2.build_add_type('container')
        spawn1 = self.room.new_spawn({'id': self.room.get_spawn_id(), 
                             'room':self.room, 
                             'obj': item2, 
                             'spawn_type': 'item'})
        spawn2 = self.room.new_spawn({'id': self.room.get_spawn_id(), 
                                      'room':self.room, 
                                      'obj': self.item, 
                                      'spawn_type': 'item',
                                      'container': spawn1})
        
        expected_spawn_point_spawn2 = 'into %s (R:%s)' % (spawn1.spawn_object.name, 
                                                          spawn1.id)
        expected_spawn_point_spawn1 = 'in room'
        
        # Make sure that the the containee has its container
        # attribute set
        self.assertTrue(spawn2.container)
        # Make sure the container attribute points back to spawn 1
        self.assertEqual(spawn2.container, spawn1)
        # Make sure the spawn point got set correctly
        self.assertEqual(spawn2.get_spawn_point(),
                         expected_spawn_point_spawn2)
        self.assertEqual(spawn1.get_spawn_point(),
                         expected_spawn_point_spawn1)
    
    def test_add_nested_spawn_with_npc_container(self):
        spawn1 = self.room.new_spawn({'id': self.room.get_spawn_id(),
                                      'room': self.room,
                                      'obj': self.npc,
                                      'spawn_type': 'npc'})
        spawn2 = self.room.new_spawn({'id': self.room.get_spawn_id(),
                                      'room': self.room,
                                      'obj': self.item,
                                      'spawn_type': 'item',
                                      'container': spawn1})
        # spawn1 = Reset(self.room, self.npc, 'npc')
        # spawn1.save()
        # spawn2 = Reset(self.room, self.item, 'item', spawn1)
        # spawn2.save()
        
        # Make sure that the the containee has its container
        # attribute set
        self.assertTrue(spawn2.container)
        self.assertEqual(spawn2.container, spawn1)
        expected_spawn_point_spawn2 = 'into %s\'s inventory (R:%s)' % (spawn1.spawn_object.name, 
                                                                       spawn1.id)
        expected_spawn_point_spawn1 = 'in room'
        
        self.assertEqual(spawn2.get_spawn_point(),
                         expected_spawn_point_spawn2)
        self.assertEqual(spawn1.get_spawn_point(),
                         expected_spawn_point_spawn1)
    
    def test_remove_nested_spawn(self):
        spawn1 = self.room.new_spawn({'id': self.room.get_spawn_id(), 
                             'room':self.room, 
                             'obj': self.item, 
                             'spawn_type': 'item'})
        spawn2 = self.room.new_spawn({'id': self.room.get_spawn_id(), 
                             'room':self.room, 
                             'obj': self.item, 
                             'spawn_type':'item'})
        spawn1.add_nested_spawn(spawn2)
        spawn1.remove_nested_spawn(spawn2)
        
        self.assertEqual(spawn1.nested_spawns, [])
    
    def test_save(self):
        pass
        
    def test_spawn_npc(self):
        spawn1 = self.room.new_spawn({'id': self.room.get_spawn_id(), 
                                      'room':self.room, 
                                      'obj': self.npc, 
                                      'spawn_type': 'npc'})
        npc2 = spawn1.spawn()
        self.assertTrue(isinstance(npc2, Npc))
    
    def test_spawn_item(self):
        spawn1 = self.room.new_spawn({'id': self.room.get_spawn_id(), 
                             'room':self.room, 
                             'obj': self.item, 
                             'spawn_type': 'item'})
        item1 = spawn1.spawn()
        self.assertTrue(isinstance(item1, GameItem))
        
        # Next test 
