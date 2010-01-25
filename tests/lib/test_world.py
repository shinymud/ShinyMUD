from shinymud.lib.world import *
from shinymud.models.user import *
from shinymud.modes.build_mode import *
from shinymud.commands import *
from shinymud.lib.db import DB
from shinymud.data.config import *
from shinymud.models.schema import initialize_database
from unittest import TestCase

import logging

class TestReset(TestCase):
    def setUp(self):
        self.world = World()
        self.world.db = DB(':memory:')
        initialize_database(self.world.db.conn)
    
    def test_tell_users(self):
        bob = User(('bob', 'bar'))
        alice = User(('alice', 'bar'))
        self.world.user_add(bob)
        self.world.user_add(alice)
        
        bob.mode = None
        bob.outq = []
        alice.mode = None
        alice.outq = []
        
        self.world.tell_users('hello world!')
        echo = wecho_color + 'hello world!' + clear_fcolor + '\r\n'
        self.assertTrue(echo in bob.outq)
        self.assertTrue(echo in alice.outq)
        
        bob.mode = InitMode(bob)
        bob.outq = []
        alice.outq = []
        
        self.world.tell_users('hello all!')
        echo = wecho_color + 'hello all!' + clear_fcolor + '\r\n'
        self.assertTrue(echo not in bob.outq)
        self.assertTrue(echo in alice.outq)
        
        bob.mode = BuildMode(bob)
        bob.outq = []
        alice.outq = []
        
        self.world.tell_users('hello!', ['alice'])
        echo = wecho_color + 'hello!' + clear_fcolor + '\r\n'
        self.assertTrue(echo in bob.outq)
        self.assertTrue(echo not in alice.outq)
    
