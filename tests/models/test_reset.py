from shinymud.lib.world import *
from shinymud.models.reset import *
from shinymud.models.area import *
from shinymud.models.npc import *
from shinymud.models.item import *
from shinymud.models.room import *
from shinymud.commands import *
from unittest import TestCase

class TestReset(TestCase):
    def setUp(self):
        self.world = World()
        self.world.db = DB(':memory:')
        area = Area()
        room = area.new_room()
        item = area.new_item()
        npc = area.new_npc()
    
    def tearDown(self):
        World._instance = None
    
    def test_add_nested_reset(self):
        reset1 = Reset(room, item, 'item')
        reset2 = Reset(room, item, 'item')
        reset1.add_nested_reset(reset2)
        
        self.AssertTrue(reset2 in reset.nested_reset)
    
    def test_add_nested_reset_with_container(self):
        pass
    
    def test_remove_nested_reset(self):
        pass
    
    def test_save(self):
        pass
    
    def test_to_dict(self):
        pass
    
    def test_spawn(self):
        pass
