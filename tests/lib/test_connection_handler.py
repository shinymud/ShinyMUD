from shinymud.lib.world import *
from shinymud.lib.connection_handler import *
from unittest import TestCase

class TestDB(TestCase):
    def setUp(self):
        self.world = World()
    
    def tearDown(self):
        World._instance = None
    
    def test_something(self):
        pass

