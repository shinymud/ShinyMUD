from shinymud.lib.world import *
from shinymud.models.user import *
from shinymud.commands import *
from unittest import TestCase
from shinymud.lib.db import DB
from shinymud.models.schema import initialize_database

# Test all of the general commands!
# The build commands are farther down!

class TestGeneralCommands(TestCase):
    def setUp(self):
        self.world = World()
        self.db = DB(':memory:')
        initialize_database(self.db.conn)
        
    def tearDown(self):
        World._instance = None
    
    def test_command_register(self):
        cmds = CommandRegister()
        self.assertEqual(cmds['supercalifragilisticexpieladocious'], None, 
                    "Command Register is returning things it doesn't have!")
        cmds.register((lambda : 3), ['bob', 'sam'])
        self.assertEqual(cmds['bob'](), 3, 
                         "Registered command 'bob' returned wrong value.")
        self.assertEqual(cmds['sam'](), 3,
                         "Registered command 'sam' returned wrong value.")
        self.assertEqual(cmds['bob'], cmds['sam'],
                         "Registered aliases 'bob' and 'sam' did not return same function.")
        

class TestBuildCommands(TestCase):
    def setUp(self):
        self.world = World()
    
    def tearDown(self):
        World._instance = None
    
