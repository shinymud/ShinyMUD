from unittest import TestCase
from shinymud.models import to_bool
class TestBool(TestCase):    
    def test_something(self):
        self.assertTrue(to_bool('true'))
        self.assertTrue(to_bool('True'))
        self.assertTrue(to_bool('TRUE'))
        self.assertFalse(to_bool('false'))
        self.assertFalse(to_bool('False'))
        self.assertFalse(to_bool('FALSE'))

