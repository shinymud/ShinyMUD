from shinymud.lib.db import *
from shinymud.data.config import ROOT_DIR
from unittest import TestCase

class TestDB(TestCase):
    def setUp(self):
        self.db = DB(':memory:')
        setup_cursor = self.db.conn.cursor()
        table = "CREATE TABLE foo (id INTEGER PRIMARY KEY,val1 TEXT,val2 INTEGER)"
        setup_cursor.execute(table)
    
    def tearDown(self):
        self.db.conn.close()
        
    def test_insert(self):
        id_num = self.db.insert("into foo (val1, val2) values (?,?)", ['bar', 55])
        rows = self.db.select("* from foo")
        self.assertEqual(len(rows), 1, "Select returned %s rows instead of 1" % str(len(rows)))
        row = rows[0]
        self.assertEqual(row.get('id'), id_num, 'INSERT returned id %s, but SELECT returned id %s' % (str(id_num), str(row.get('id'))))
        self.assertEqual(row.get('val1'), 'bar', 'Bad value: "%s" should be "%s"' % (row.get('val1'), 'bar'))
        self.assertEqual(row.get('val2'), 55, 'Bad value: "%s" should be "%s"' % (row.get('val2'), str(55)))
        

