from shinymud.lib.world import *
from shinymud.models.user import *
from shinymud.commands import *
from unittest import TestCase
from shinymud.lib.db import DB
from shinymud.models.schema import initialize_database

class TestUser(TestCase):
    def setUp(self):
        self.world = World()
        self.world.db = DB(':memory:')
        initialize_database(self.world.db.conn)
        self.area = Area.create('boo')
    
    def tearDown(self):
        World._instance = None
    
    def test_something(self):
        pass