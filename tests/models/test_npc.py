from shinymud.lib.world import *
from shinymud.models.npc import *
from shinymud.commands import *
from unittest import TestCase
from shinymud.lib.db import DB
from shinymud.models.schema import initialize_database

class TestNpc(TestCase):
    def setUp(self):
        self.world = World()
        self.db = DB(':memory:')
        initialize_database(self.db.conn)
    
    def tearDown(self):
        World._instance = None
    
    def test_something(self):
        pass

