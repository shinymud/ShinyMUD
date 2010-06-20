from shinymud.lib.db import *
from shinymud.data.config import ROOT_DIR
from shinytest import ShinyTestCase

class TestDB(ShinyTestCase):
    def setUp(self):
        ShinyTestCase.setUp(self)
        table = "CREATE TABLE foo (id INTEGER PRIMARY KEY,val1 TEXT,val2 INTEGER)"
        self.world.db.conn.execute(table)
    
    def test_insert(self):
        id_num = self.world.db.insert("into foo (val1, val2) values (?,?)", ['bar', 55])
        rows = self.world.db.select("* from foo")
        self.assertEqual(len(rows), 1, "Select returned %s rows instead of 1" % str(len(rows)))
        row = rows[0]
        self.assertEqual(row.get('id'), id_num, 'INSERT returned id %s, but SELECT returned id %s' % (str(id_num), str(row.get('id'))))
        self.assertEqual(row.get('val1'), 'bar', 'Bad value: "%s" should be "%s"' % (row.get('val1'), 'bar'))
        self.assertEqual(row.get('val2'), 55, 'Bad value: "%s" should be "%s"' % (row.get('val2'), str(55)))
        

