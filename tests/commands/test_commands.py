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
        self.world.db = DB(':memory:')
        initialize_database(self.world.db.conn)
        
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
    
    def test_chat_command(self):
        bob = User(('bob', 'bar'))
        alice = User(('alice', 'bar'))
        sam = User(('sam', 'bar'))
        bob.mode = None
        bob.userize(name='bob')
        bob.outq = []
        sam.mode = None
        sam.userize(name='sam')
        sam.outq = []
        self.world.user_add(bob)
        self.world.user_add(sam)
        self.world.user_add(alice)
        
        Chat(bob, 'lol, hey guys!', 'chat').execute()
        self.assertTrue('Bob chats, "lol, hey guys!"\r\n' in sam.outq)
        self.assertTrue('Bob chats, "lol, hey guys!"\r\n' in bob.outq)
        self.assertFalse('Bob chats, "lol, hey guys!"\r\n' in alice.outq)
        
        sam.channels['chat'] = False
        sam.outq = []
        bob.outq = []
        alice.outq = []
        
        Chat(bob, 'lol, hey guys!', 'chat').execute()
        self.assertFalse('Bob chats, "lol, hey guys!"\r\n' in sam.outq)
        self.assertTrue('Bob chats, "lol, hey guys!"\r\n' in bob.outq)
        self.assertFalse('Bob chats, "lol, hey guys!"\r\n' in alice.outq)
    

class TestBuildCommands(TestCase):
    def setUp(self):
        self.world = World()
    
    def tearDown(self):
        World._instance = None
    
