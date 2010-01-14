from shinymud.lib.db import *
from shinymud.config import ROOT_DIR
from unittest import TestCase

class TestDB(TestCase):
    def setUp(self):
        self.db = DB(':memory:')
    
    def tearDown(self):
        pass
    def test_something(self):
        pass

