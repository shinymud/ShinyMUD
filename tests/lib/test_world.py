from shinymud.lib.world import *
from shinymud.models.user import *
from shinymud.modes.build_mode import *
from shinymud.commands import *
from shinymud.lib.db import DB
from shinymud.models.schema import initialize_database
from unittest import TestCase

class TestReset(TestCase):
    def setUp(self):
        self.world = World()
        self.world.db = DB(':memory:')
        initialize_database(self.world.db.conn)
    
    def test_tell_users(self):
        bob = User(('bob', 'bar'))
        alice = User(('alice', 'bar'))
        bob.mode = None
        bob.outq = []
        alice.mode = None
        alice.outq = []
        self.world.user_add(bob)
        self.world.user_add(alice)
        
        self.world.tell_users('hello world!')
        
        self.assertTrue('hello world!\r\n' in bob.outq)
        self.assertTrue('hello world!\r\n' in alice.outq)
        
        bob.mode = InitMode(bob)
        bob.outq = []
        alice.outq = []
        
        self.world.tell_users('hello all!')
        
        self.assertTrue('hello all!\r\n' not in bob.outq)
        self.assertTrue('hello all!\r\n' in alice.outq)
        
        bob.mode = BuildMode(bob)
        bob.outq = []
        alice.outq = []
        
        self.world.tell_users('hello!', ['alice'])
        
        self.assertTrue('hello!\r\n' in bob.outq)
        self.assertTrue('hello!\r\n' not in alice.outq)
    
