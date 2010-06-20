from unittest import TestCase

class ShinyTestCase(TestCase):    
    def setUp(self):
        import sys
        remove = [m for m in sys.modules.keys() if 'shinymud' in m]
        for r in remove:
            del sys.modules[r]
        from shinymud.lib.world import World
        self.world = World(':memory:')
        from shinymud.lib.setup import initialize_database
        initialize_database()
    
    def tearDown(self):
        if hasattr(self, 'world'):
            self.world.db.conn.close()
        else:
            print "no world to close db connection"
        from shinymud.lib.world import World
        World._instance = None
    
