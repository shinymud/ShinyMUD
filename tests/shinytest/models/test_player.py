from shinytest import ShinyTestCase

class TestPlayer(ShinyTestCase):
    def setUp(self):
        ShinyTestCase.setUp(self)
        from shinymud.models.area import Area
        self.area = Area.create('boo')
    
    def test_something(self):
        pass
    
