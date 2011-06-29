from shinytest import ShinyTestCase

class TestTextEditMode(ShinyTestCase):      
    def setUp(self):
        ShinyTestCase.setUp(self)
        from shinymud.models.player import Player
        from shinymud.models.area import Area
        from shinymud.models.room import Room
        from shinymud.modes.build_mode import BuildMode
        from shinymud.data import config
        
        self.bob = Player(('bob', 'bar'))
        self.bob.mode = None
        self.bob.playerize({'name':'bob'})
        self.world.player_add(self.bob)
        self.bob.mode = BuildMode(self.bob)
        self.bob.permissions = self.bob.permissions | config.BUILDER
        
        self.area = Area.create({'name': 'foo'})
    
    def tearDown(self):
        del self.area
    
    def test_help(self):
        from shinymud.modes.text_edit_mode import TextEditMode
        room = self.area.new_room()
        help_msg = "    @done - saves your progress and exits the editor.\n" +\
                   "    @cancel - quit the editor without saving changes.\n" +\
                   "    @show - display your progress so far, line by line.\n" +\
                   "    @preview - preview the formatted version of your text.\n" +\
                   "    @clear - clears ALL of your progress, giving you an empty slate.\n" +\
                   "    @delete line# - delete a specific line.\n" +\
                   "    @replace line# new_sentence - replace a line with a new sentence:\n" +\
                   "        e.g. \"@replace 5 My new sentence.\"\n" +\
                   "    @insert line# new_sentence - inserts a sentence at line#:\n" +\
                   "        e.g. \"@insert 1 My new sentence.\"\n"
        mode = TextEditMode(self.bob, room, 'description', room.description)
        mode.help()
        self.assertTrue(help_msg in self.bob.outq)
    
    def test_clear(self):
        from shinymud.modes.text_edit_mode import TextEditMode
        room = self.area.new_room()
        mode = TextEditMode(self.bob, room, 'description', room.description)
        
        mode.edit_lines = ['This is a shiny new room!']
        mode.clear_description()
        mode.finish_editing()
        self.assertEqual(room.description, '')
    
    def test_delete_line(self): 
        from shinymud.modes.text_edit_mode import TextEditMode
        room = self.area.new_room()
        mode = TextEditMode(self.bob, room, 'description', room.description)
        
        #Manually give the room description so we don't depend on the new_room() defaults
        mode.edit_lines = ["This be a shiny room here!", "There be goblins here!", "And a pirate!"]
        mode.delete_line(line='2')
        self.assertEqual(len(mode.edit_lines), 2)
        mode.finish_editing()
        self.assertFalse("There be goblins here!" in room.description)
        
        #stress testing
        mode = TextEditMode(self.bob, room, 'description', room.description)
        mode.delete_line(line='200')
        self.assertTrue("200 is not a valid line number." in self.bob.outq)
        
        #(regular expression parses non-digit input into args instead of line)
        mode.delete_line(args='YourMother')
        self.assertTrue("'YourMother' is not a valid line number." in self.bob.outq)
    
    def test_replace_line(self):
        from shinymud.modes.text_edit_mode import TextEditMode
        room = self.area.new_room()
        mode = TextEditMode(self.bob, room, 'description', room.description)
        
        #Manually give the room description so we don't depend on the new_room() defaults
        mode.edit_lines = ["This be a shiny room here!", "There be goblins here!", "And a pirate!"]
        mode.replace_line(line='2', args='There be spam and eggs here!')
        self.assertEqual(len(mode.edit_lines), 3)
        mode.finish_editing()
        self.assertTrue('There be spam and eggs here!' in room.description)
        
        #stress testing
        mode = TextEditMode(self.bob, room, 'description', room.description)
        mode.replace_line(line='200')
        self.assertTrue("200 is not a valid line number." in self.bob.outq)
        
        #(regular expression parses non-digit input into args instead of line)
        mode.replace_line(args='YourMother')
        self.assertTrue("'YourMother' is not a valid line number." in self.bob.outq)
    
    def test_insert_line(self):
        from shinymud.modes.text_edit_mode import TextEditMode
        room = self.area.new_room()
        mode = TextEditMode(self.bob, room, 'description', room.description)
        
        #Manually give the room description so we don't depend on the new_room() defaults
        mode.edit_lines = ["This be a shiny room here!", "There be goblins here!", "And a pirate!"]
        mode.insert_line(line='2', args='There be spam and eggs here!')
        self.assertEqual(len(mode.edit_lines), 4)
        mode.finish_editing()
        self.assertTrue('There be spam and eggs here!' in room.description)
        
        #stress testing
        mode = TextEditMode(self.bob, room, 'description', room.description)
        mode.insert_line(line='200')
        self.assertTrue("200 is not a valid line number." in self.bob.outq)
        
        mode.insert_line(args='YourMother')
        self.assertTrue("'YourMother' is not a valid line number." in self.bob.outq)    
    
    def test_cancel_edit(self):
        from shinymud.modes.text_edit_mode import TextEditMode
        room = self.area.new_room()
        mode = TextEditMode(self.bob, room, 'description', room.description)
        
        mode.edit_lines = ["This be a shiny room here!", "There be goblins here!", "And a pirate!"]
        mode.finish_editing()
        mode = TextEditMode(self.bob, room, 'description', room.description)
        mode.insert_line(line='2', args='There be spam and eggs here!')
        mode.cancel_edit()
        self.assertFalse('There be spam and eggs here!' in room.description)
        
    

