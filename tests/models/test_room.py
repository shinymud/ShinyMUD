from shinymud.lib.world import *
from shinymud.models.player import *
from shinymud.models.room import *
from shinymud.models.area import *
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
    
    def test_add_spawn_item_inroom(self):
        """Test adding a spawn for an item, with a spawn point 'in room'."""
        item = self.area.new_item()
        message = self.room.add_spawn('for item %s' % item.id)
        exp_message = ('A room spawn has been added for '
                       '%s number %s.' % ('item', item.id)
                      )
        # Make sure we get the expected result message
        self.assertEqual(message, exp_message)
        # We should only have one spawn in room.spawns
        self.assertEqual(len(self.room.spawns.items()), 1)
        spawn = self.room.spawns.values()[0]
        # The object this spawn points to should be equal to the item
        # we just created
        self.assertEqual(spawn.spawn_object, item)
        # its spawn point should be 'in room'
        self.assertEqual(spawn.get_spawn_point(), 'in room')
    
    def test_add_spawn_item_nested_in_item(self):
        item = self.area.new_item()
        container = self.area.new_item()
        container.add_type('container')
        
        message1 = self.room.add_spawn('for item %s' % container.id)
        exp_message1 = ('A room spawn has been added for '
                        '%s number %s.' % ('item', container.id)
                       )
        self.room.log.debug(self.room.spawns)
        self.assertEqual(message1, exp_message1)
        message2 = self.room.add_spawn('for item %s in spawn %s' % (item.id, 
                                                                    '1'))
        exp_message2 = ('A room spawn has been added for '
                        '%s number %s.' % ('item', item.id)
                       )
        self.assertEqual(message2, exp_message2)
        # Make sure the room has 2 spawns in its list
        self.assertEqual(len(self.room.spawns.items()), 2)
        spawn1 = self.room.spawns.get('1')
        spawn2 = self.room.spawns.get('2')
        self.assertTrue('container' in spawn1.spawn_object.item_types)
        # spawn1 should have one nested spawn
        self.assertEqual(len(spawn1.nested_spawns), 1)
        self.assertEqual(spawn1.get_spawn_point(), 'in room')
        self.assertEqual(spawn1, spawn2.container)
        self.assertEqual(spawn2.get_spawn_point(),
                         'into %s (R:%s)' % (container.name,
                                             str(spawn1.dbid))
                        )
    
    def test_remove_spawn(self):
        item = self.area.new_item()
        self.room.add_spawn('for item %s' % item.id)
        self.assertEqual(len(self.room.spawns.items()), 1)
        db_spawn = self.world.db.select('* FROM room_spawns WHERE dbid=?', [1])
        self.assertEqual(len(db_spawn), 1)
        self.room.remove_spawn('1')
        # The room should now have an empty spawns list
        self.assertEqual(len(self.room.spawns.items()), 0)
        # The spawn should no longer be in the database
        db_spawn = self.world.db.select('* FROM room_spawns WHERE dbid=?', [1])
        self.assertEqual(len(db_spawn), 0)
    
    def test_remove_nested_spawn(self):
        item1 = self.area.new_item()
        item2 = self.area.new_item()
        container = self.area.new_item()
        container.add_type('container')
        self.room.add_spawn('for item %s' % container.id)
        self.room.add_spawn('for item %s inside %s' % (item1.id, '1'))
        self.room.add_spawn('for item %s inside %s' % (item2.id, '1'))
        self.assertEqual(len(self.room.spawns.items()), 3)
        c_spawn = self.room.spawns.get('1')
        spawn1 = self.room.spawns.get('2')
        spawn2 = self.room.spawns.get('3')
        self.assertEqual(c_spawn, spawn1.container)
        self.assertEqual(c_spawn, spawn2.container)
        self.assertEqual(len(c_spawn.nested_spawns), 2)
        
        message1 = self.room.remove_spawn('2')
        message2 = self.room.remove_spawn('3')
        self.assertEqual('Room spawn 2 has been removed.\n', message1)
        self.assertEqual('Room spawn 3 has been removed.\n', message2)
        self.assertTrue(c_spawn in self.room.spawns.values())
        self.assertEqual(len(self.room.spawns.items()), 1)
        self.assertEqual(len(c_spawn.nested_spawns), 0)
    
    def test_remove_nested_spawn_container(self):
        pass
    
    def test_spawn(self):
        proto_item = self.area.new_item()
        proto_container = self.area.new_item()
        proto_container.add_type('container')
        proto_npc = self.area.new_npc()
        
        self.room.add_spawn('for item %s' % proto_container.id)
        self.room.add_spawn('for item %s in %s' % (proto_item.id, '1'))
        self.room.add_spawn('for npc %s' % proto_npc.id)
        
        self.assertEqual(len(self.room.items), 0)
        self.assertEqual(len(self.room.npcs), 0)
        self.room.reset()
        self.assertEqual(len(self.room.items), 1)
        self.assertEqual(self.room.npcs[0].id, proto_npc.id)
        self.assertEqual(self.room.npcs[0].area, proto_npc.area)
        self.assertEqual(len(self.room.npcs), 1)
        self.assertEqual(self.room.items[0].id, proto_container.id)
        self.assertEqual(self.room.items[0].area, proto_container.area)
        
        c_flag = False
        for item in self.room.items:
            if item.is_container():
                inventory = item.item_types.get('container').inventory
                c_flag = True
                # There should be 1 item inside the container item
                self.assertEqual(len(inventory), 1)
                self.assertEqual(inventory[0].id, proto_item.id)
                self.assertEqual(inventory[0].area, proto_item.area)
        # We better have found a container in the room's items
        self.assertTrue(c_flag)
        
        # Reset again, and make sure that we didn't add the objects that
        # we already had
        self.room.reset()
        self.assertEqual(len(self.room.items), 1)
        self.assertEqual(len(self.room.npcs), 1)
        c_flag = False
        for item in self.room.items:
            if item.is_container():
                c_flag = True
                inventory = item.item_types.get('container').inventory
                self.assertEqual(inventory[0].id, proto_item.id)
                self.assertEqual(inventory[0].area, proto_item.area)
                # There should be 1 item inside the container item
                self.assertEqual(len(inventory), 1)
        # We better have found a container in the room's items
        self.assertTrue(c_flag)
    

