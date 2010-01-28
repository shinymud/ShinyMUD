from shinymud.lib.world import *
from shinymud.data.config import *
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
        
        Chat(bob, 'lol, hey guys!', 'chat').run()
        chat = chat_color + 'Bob chats, "lol, hey guys!"' + clear_fcolor + '\r\n'
        self.assertTrue(chat in sam.outq)
        self.assertTrue(chat in bob.outq)
        self.assertFalse(chat in alice.outq)
        
        sam.channels['chat'] = False
        sam.outq = []
        bob.outq = []
        alice.outq = []
        
        Chat(bob, 'lol, hey guys!', 'chat').run()
        self.assertFalse(chat in sam.outq)
        self.assertTrue(chat in bob.outq)
        self.assertFalse(chat in alice.outq)
    
    def test_give_command(self):
        area = Area.create('blarg')
        room = area.new_room()
        bob = User(('bob', 'bar'))
        bob.mode = None
        bob.userize(name='bob')
        alice = User(('alice', 'bar'))
        alice.mode = None
        alice.userize(name='alice')
        self.world.user_add(bob)
        self.world.user_add(alice)
        
        room.user_add(bob)
        room.user_add(alice)
        alice.location = room
        bob.location = room
        npc = area.new_npc()
        room.npc_add(npc)
        
        item = area.new_item()
        item.set_keywords('bauble', bob)
        item.set_name('a bauble', bob)
        bob.item_add(item.load())
        
        self.assertEqual(len(bob.inventory), 1)
        Give(bob, 'bauble to alice', 'give').run()
        self.assertEqual(len(bob.inventory), 0)
        self.assertEqual(len(alice.inventory), 1)
        to_alice = 'Bob gives you a bauble.\r\n'
        self.assertTrue(to_alice in alice.outq)
        to_bob = 'You give a bauble to Alice.\r\n'
        self.assertTrue(to_bob in bob.outq)
        
        Give(alice, 'bauble to shiny', 'give').run()
        self.assertEqual(len(alice.inventory), 0)
        self.assertEqual(len(npc.inventory), 1)
        to_alice = 'You give a bauble to %s.\r\n' % npc.name
        self.assertTrue(to_alice in alice.outq)
        to_shiny = 'Alice gives you a bauble.'
        self.assertTrue(to_shiny in npc.actionq)
    
    def test_set_command(self):
        bob = User(('bob', 'bar'))
        bob.mode = None
        bob.userize(name='bob')
        
        # Test setting e-mail
        Set(bob, 'email bob@bob.com', 'set').run()
        self.assertEqual('bob@bob.com', bob.email)
        
        # Test setting title
        Set(bob, 'title is the best EVAR', 'set').run()
        self.assertEqual('is the best EVAR', bob.title)
        
        # Try to set goto_appear and goto_disappear (both should fail
        # since this user shouldn't have permissions)
        Set(bob, 'goto_appear Bob pops in from nowhere.', 'set').run()
        eresult = 'You don\'t have the permissions to set that.\r\n'
        self.assertTrue(eresult in bob.outq)
        bob.outq = []
        Set(bob, 'goto_disappear foo', 'set').run()
        self.assertTrue(eresult in bob.outq)
        
        bob.permissions = bob.permissions | BUILDER
        
        # Try to set goto_appear and goto_disappear (both should now
        # succeed now that the user has adequate permissions)
        Set(bob, 'goto_appear Bob pops in from nowhere.', 'set').run()
        self.assertEqual('Bob pops in from nowhere.', bob.goto_appear)
        bob.outq = []
        Set(bob, 'goto_disappear foo', 'set').run()
        self.assertEqual('foo', bob.goto_disappear)
    

class TestBuildCommands(TestCase):
    def setUp(self):
        self.world = World()
    
    def tearDown(self):
        World._instance = None
    
