from shinymud.lib.world import *
from shinymud.models.user import *
from shinymud.models.room import *
from shinymud.commands import *
from unittest import TestCase

class TestRoom(TestCase):
    def setUp(self):
        self.world = World()
    
    def tearDown(self):
        World._instance = None
    
    def test_something(self):
        pass

