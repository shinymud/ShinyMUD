from shinymud.lib.world import *
from shinymud.models.room import *
from shinymud.models.room_exit import *
from shinymud.commands import *
from unittest import TestCase

class TestRoomExit(TestCase):
    def setUp(self):
        self.world = World()
    
    def tearDown(self):
        World._instance = None
    
    def test_something(self):
        pass

