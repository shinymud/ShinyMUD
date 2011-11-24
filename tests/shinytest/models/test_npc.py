from shinytest import ShinyTestCase

class TestNpc(ShinyTestCase):
    
    def setUp(self):
        ShinyTestCase.setUp(self)
        from shinymud.models.player import Player
        from shinymud.models.npc import Npc
        from shinymud.models.area import Area
        from shinymud.models.room import Room
        from shinymud.modes.build_mode import BuildMode
        from shinymud.data import config
        
        self.PERMS = config.PERMS
        
        self.bob = Player(('bob', 'bar'))
        self.bob.mode = None
        self.bob.playerize({'name':'bob'})
        self.world.player_add(self.bob)
        self.bob.mode = BuildMode(self.bob)
        self.bob.permissions = self.bob.permissions | self.PERMS['builder']
        
        self.area = Area.create({'name': 'foo'})
        self.room = self.area.new_room()
        
        self.area2 = Area.create({'name': 'SimCity'})
        self.area2_script = self.area2.new_script()
    
    def tearDown(self):
        del self.area
        del self.area2
        del self.bob
        
    
    def test_existance(self):
        """Test if an NPC can exist within an area properly (unspawned)"""
        self.npc = self.area.new_npc()
        self.npc.characterize({'name': 'bobert'})
        self.assertTrue(self.npc in self.area.npcs.values())
    
    def test_build_add_remove_events(self):
        npc = self.area.new_npc()
        fail_message = 'Type "help events" for help with this command.'
        message = npc.build_add_event('', self.bob)
        self.assertEqual(message, fail_message)
        #test for non-existant scripts
        message = npc.build_add_event('pc_enter call script 1', self.bob)
        self.assertEqual(message, "Script 1 doesn't exist.")
        message = npc.build_add_event("hears 'spam' call script 0", self.bob)
        self.assertEqual(message, "Script 0 doesn't exist.")
        message = npc.build_add_event("hears 'spam' call script 602", self.bob)
        self.assertEqual(message, "Script 602 doesn't exist.")
        
        script = self.area.new_script()
        #Test basic add
        message = npc.build_add_event('pc_enter call script 1', self.bob)
        self.assertEqual(message, 'Event added.' )
        #Test invalid areas
        message = npc.build_add_event('pc_enter call script 1 from area AreaDontExist', self.bob)
        self.assertEqual(message, 'Area "AreaDontExist" doesn\'t exist.')
        message = npc.build_add_event('pc_enter call script 1 from area AreaDontExist 100', self.bob)
        self.assertEqual(message, 'Area "AreaDontExist" doesn\'t exist.')
        #Test invalid probabilities.
        message = npc.build_add_event('pc_enter call script 1 0', self.bob)
        self.assertEqual(message, 'Probability value must be between 1 and 100.')
        message = npc.build_add_event('pc_enter call script 1 101', self.bob)
        self.assertEqual(message, 'Probability value must be between 1 and 100.')
        message = npc.build_add_event('pc_enter call script 1 9999', self.bob)
        self.assertEqual(message, 'Probability value must be between 1 and 100.')
        #Test different froms of valid adds.
        message = npc.build_add_event('pc_enter call script 1 50', self.bob)
        self.assertEqual(message, 'Event added.')
        message = npc.build_add_event('pc_enter call script 1 from area SimCity', self.bob)
        self.assertEqual(message, 'Event added.')
        message = npc.build_add_event('pc_enter call script 1 from area SimCity 75', self.bob)
        self.assertEqual(message, 'Event added.')
        message = npc.build_add_event('pc_enter call 1 from SimCity 50', self.bob)
        self.assertEqual(message, 'Event added.')
        #Test for trigger 'hears'
        message = npc.build_add_event("hears 'food' call script 1", self.bob)
        self.assertEqual(message, 'Event added.' )
        #Test for trigger 'emoted'
        message = npc.build_add_event("emoted 'slap' call script 1", self.bob)
        self.assertEqual(message, 'Event added.' )
          #Technically invalid, but will be left to user responsibility for now. 
          #(it shouldn't ever cause a crash)
        message = npc.build_add_event("emoted 'emotedontexist' call script 1", self.bob)
        self.assertEqual(message, 'Event added.' )
        #Test for new items
        self.area.new_item()
        message = npc.build_add_event("given_item 'item 1' call script 1", self.bob)
        self.assertEqual(message, 'Event added.' )
          #Technically invalid, but will be left to user responsibility for now. 
          #(it shouldn't ever cause a crash)
        message = npc.build_add_event("given_item 'item 5' call script 1", self.bob)
        self.assertEqual(message, 'Event added.' )
        
        #we should now have 5 successfully added events in pc_enter
        self.assertEqual(len(npc.events['pc_enter']), 5)
        message = npc.build_remove_event("pc_enter -1", self.bob)
        self.assertEqual(message, 'Try: "remove event <event-trigger> <event-id>" or see "help npc events".' )
        self.assertEqual(len(npc.events['pc_enter']), 5)
        message = npc.build_remove_event("pc_enter 5", self.bob)
        self.assertEqual(message, "Npc 1 doesn't have the event pc_enter #5." )
        self.assertEqual(len(npc.events['pc_enter']), 5)
        message = npc.build_remove_event("pc_enter 4", self.bob)
        self.assertEqual(message, 'Event pc_enter, number 4 has been removed.')
        self.assertEqual(len(npc.events['pc_enter']), 4)
        message = npc.build_remove_event("given_item 1", self.bob)
        self.assertEqual(message, 'Event given_item, number 1 has been removed.')
        self.assertEqual(len(npc.events['pc_enter']), 4)
        self.assertEqual(len(npc.events['given_item']), 1)
    
    def test_build_add_remove_permissions(self):
        npc = self.area.new_npc()
          #set npc permissions to nothing.
        npc.permissions = 0
        message = npc.build_add_permission("dm", self.bob)
        self.assertEqual(message, "You need to be GOD in order to edit an npc's permissions.")
        #Current permission level needed for messing with npc perms is 'god'. (for when this test was written)
        #Change as needed!
        self.bob.permissions = self.bob.permissions | self.PERMS['god']
        #Bad input tests
        message = npc.build_add_permission("", self.bob)
        self.assertEqual(message, 'Try: "add permission <permission group>". See "help permissions".')
        message = npc.build_add_permission("monkey", self.bob)
        self.assertTrue('Valid permissions are: admin, player, builder, dm, god\n' in message)
        #good input tests
        message = npc.build_add_permission("god", self.bob)
        self.assertTrue('Shiny McShinerson now has god permissions.' in message)
        self.assertTrue(npc.permissions is self.PERMS['god'])
        message = npc.build_add_permission("dm", self.bob)
        self.assertTrue('Shiny McShinerson now has dm permissions.' in message)
        self.assertTrue(npc.permissions is self.PERMS['god'] | self.PERMS['dm'])
        self.assertTrue(npc.permissions is not self.PERMS['god'] | self.PERMS['dm'] | self.PERMS['admin'])
        message = npc.build_add_permission("admin", self.bob)
        self.assertTrue('Shiny McShinerson now has admin permissions.' in message)
        self.assertTrue(npc.permissions is self.PERMS['god'] | self.PERMS['dm'] | self.PERMS['admin'])
        
        #Removing Permissions
          #reset bobs permissions for next test
        self.bob.permissions = 0
        message = npc.build_remove_permission("dm", self.bob)
        self.assertEqual(message, "You need to be GOD in order to edit an npc's permissions.")
        #Current permission level needed for messing with npc perms is 'god'. (for when this test was written)
        #Change as needed!
        self.bob.permissions = self.bob.permissions | self.PERMS['god']
        #Bad input tests
        message = npc.build_remove_permission("", self.bob)
        self.assertEqual(message, 'Try: "remove permission <permission group>", or see "help permissions".')
        message = npc.build_remove_permission("monkey", self.bob)
        self.assertEqual("Shiny McShinerson doesn't have monkey permissions.", message)
        #Good input tests
        self.assertTrue(npc.permissions is self.PERMS['god'] | self.PERMS['dm'] | self.PERMS['admin'])
        message = npc.build_remove_permission("god", self.bob)
        self.assertEqual('Shiny McShinerson no longer has god permissions.', message)
        self.assertTrue(npc.permissions is self.PERMS['dm'] | self.PERMS['admin'])
        self.assertTrue(npc.permissions < self.PERMS['god'])
        message = npc.build_remove_permission("dm", self.bob)
        self.assertEqual('Shiny McShinerson no longer has dm permissions.', message)
        self.assertTrue(npc.permissions is self.PERMS['admin'])
        self.assertTrue(npc.permissions >= self.PERMS['dm'])
        message = npc.build_remove_permission("admin", self.bob)
        self.assertEqual('Shiny McShinerson no longer has admin permissions.', message)
        self.assertTrue(npc.permissions is 0)
    
    def test_build_add_remove_ai(self):
        npc = self.area.new_npc()
        
        #Test adding ai pack
        message = npc.build_add_ai("", self.bob)
        self.assertEqual('Try: "add ai <ai-pack-name>", or type "help ai packs".', message)
        message = npc.build_add_ai("doesnotexist", self.bob)
        self.assertEqual('"doesnotexist" is not a valid ai pack. See "help ai packs".', message)
        message = npc.build_add_ai("merchant", self.bob)
        self.assertEqual("This npc (Shiny McShinerson) is now a merchant.", message)
        message = npc.build_add_ai("merchant", self.bob)
        self.assertEqual('This npc (Shiny McShinerson) already has that ai pack.', message)
    
        #Test basic add behavior for ai pack
        message = str(npc)
        self.assertTrue("MERCHANT ATTRIBUTES:" in message)
        
        #Test removing ai pack
        message = npc.build_remove_ai("", self.bob)
        self.assertEqual('Try: "remove ai <ai-pack-name>", or type "help ai packs".', message)
        message = npc.build_remove_ai("doesnotexist", self.bob)
        self.assertEqual('This npc doesn\'t have the "doesnotexist" ai type.', message)
        message = npc.build_remove_ai("merchant", self.bob)
        self.assertEqual('Npc 1 (Shiny McShinerson) no longer has merchant ai.', message)
        message = npc.build_remove_ai("merchant", self.bob)
        self.assertEqual('This npc doesn\'t have the "merchant" ai type.', message)
        

    



