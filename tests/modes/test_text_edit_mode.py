from shinymud.lib.world import *
from shinymud.models.user import *
from shinymud.modes.text_edit_mode import *
from shinymud.commands import *
from unittest import TestCase

class TestTextEditMode(TestCase):
    def setUp(self):
        self.world = World()
    
    def tearDown(self):
        World._instance = None
    
    def test_something(self):
        pass