from shinymud.lib.world import *
from shinymud.models.player import *
from shinymud.modes.build_mode import *
from shinymud.commands import *
from shinymud.lib.db import DB
from shinymud.data.config import *
from shinymud.models.schema import initialize_database
from shinytest import ShinyTestCase

class TestReset(ShinyTestCase):
    def test_tell_players(self):
        bob = Player(('bob', 'bar'))
        alice = Player(('alice', 'bar'))
        self.world.player_add(bob)
        self.world.player_add(alice)
        
        bob.mode = None
        bob.outq = []
        alice.mode = None
        alice.outq = []
        
        self.world.tell_players('hello world!')
        echo = wecho_color + 'hello world!' + clear_fcolor + '\r\n'
        self.assertTrue(echo in bob.outq)
        self.assertTrue(echo in alice.outq)
        
        bob.mode = InitMode(bob)
        bob.outq = []
        alice.outq = []
        
        self.world.tell_players('hello all!')
        echo = wecho_color + 'hello all!' + clear_fcolor + '\r\n'
        self.assertTrue(echo not in bob.outq)
        self.assertTrue(echo in alice.outq)
        
        bob.mode = BuildMode(bob)
        bob.outq = []
        alice.outq = []
        
        self.world.tell_players('hello!', ['alice'])
        echo = wecho_color + 'hello!' + clear_fcolor + '\r\n'
        self.assertTrue(echo in bob.outq)
        self.assertTrue(echo not in alice.outq)
    
