from shinytest import ShinyTestCase
class TestShinyTypes(ShinyTestCase):
    def test_to_bool(self):
        from shinymud.models.shiny_types import to_bool
        self.assertTrue(to_bool('true'))
        self.assertTrue(to_bool('True'))
        self.assertTrue(to_bool(1))
        self.assertTrue(to_bool('1'))
        self.assertTrue(to_bool(True))
        self.assertFalse(to_bool('false'))
        self.assertFalse(to_bool('False'))
        self.assertFalse(to_bool(0))
        self.assertFalse(to_bool('0'))
        self.assertFalse(to_bool(False))
    
    def test_read_dict(self):
        from shinymud.models.shiny_types import read_dict
        self.assertEqual(read_dict('m=n'), {'m':'n'})
        self.assertEqual(read_dict('a=b,c=d'), {'a':'b', 'c':'d'})
        self.assertEqual(read_dict(u'j=k'), {u'j':u'k'})
        self.assertEqual(read_dict(u'x=y,foo=bar'), {u'x':u'y', u'foo':u'bar'})
    
    def test_write_dict(self):
        from shinymud.models.shiny_types import write_dict
        self.assertTrue(write_dict({'a':'b', 'c':'d'}) in ('a=b,c=d', 'c=d,a=b'))
        self.assertTrue(write_dict({u'x':u'y', u'm':u'n'}) in (u'x=y,m=n', u'm=n,x=y'))
        self.assertEqual(write_dict({'a':'b'}), 'a=b')
        self.assertEqual(write_dict({u'x':u'y'}), u'x=y')

    def test_copy_dict(self):
        from shinymud.models.shiny_types import copy_dict
        d = {'a':'b', 'c':'d'}
        self.assertEqual(d, copy_dict(d))
        self.assertFalse(d is copy_dict(d))
        foo = copy_dict(d)
        foo['e'] = True
        self.assertTrue(foo.get('e', False))
        self.assertFalse(d.get('e', False))
    
    def test_read_list(self):
        from shinymud.models.shiny_types import read_list
        self.assertEqual(read_list(''), [])
        self.assertEqual(read_list('a,b,c'), ['a', 'b', 'c'])
    
    def test_write_list(self):
        from shinymud.models.shiny_types import write_list
        self.assert_(write_list([]) is None)
        self.assertEqual(write_list(['a', 'b', 'c']), 'a,b,c')
        self.assertEqual(write_list([u'a', u'b']), u'a,b')
    
    def test_copy_list(self):
        from shinymud.models.shiny_types import copy_list
        foo = ['a', 'b', 'c']
        bar = copy_list(foo)
        self.assertEqual(foo, bar)
        bar.append('d')
        self.assertNotEqual(len(bar), len(foo))
    

# 
# def read_area(val):
#     if isinstance(val, basestring):
#         return cls.world.get_area(val)
#     return val
# 
# def write_area(val):
#     if isinstance(val, basestring):
#         return val
#     return val.name
# 
# def read_json(val):
#     return json.loads(val)
# 
# def write_json(val):
#     return json.dumps(val)
# 
# def write_model(val):
#     if isinstance(val, int):
#         return val
#     return val.dbid    
# 
# def read_int_dict(val):
#     d = {}
#     if val:
#         for a in val.split(','):
#             key, val = a.split('=')
#             d[key] = int(val)
#     return d
# 
# def write_int_dict(val):
#     s = []
#     if val:
#         for key, val in val.items():
#             s.append("%s=%s" % (str(key), str(val)))
#     return ",".join(s)
# 
# def read_damage(val):
#     dmg = []
#     if val:
#         for d in val.split('|'):
#             dmg.append(Damage(d))
#     return dmg
# 
# def write_damage(val):
#     return '|'.join([str(d) for d in val])
# 
# def read_channels(val):
#     d = {}
#     for pair in val.split(','):
#         k,v = pair.split('=')
#         d[k] = to_bool(v)
#     return d    
# 
# def read_location(val):
#     #loc == 'area,id'
#     loc = val.split(',')
#     return world.get_location(loc[0], loc[1])
# 
# def write_location(val):
#     if val:
#         return '%s,%s' % (val.area.name, val.id)
#     return None
