

from shinytest import ShinyTestCase

class TestAiPacks(ShinyTestCase):
    
    def setUp(self):
        ShinyTestCase.setUp(self)
        from shinymud.models.player import Player
        from shinymud.models.npc import Npc
        from shinymud.models.area import Area
        from shinymud.models.room import Room
        from shinymud.modes.build_mode import BuildMode
        from shinymud.data import config
        
        self.PERMS = config.PERMS
        
        #"bob" is created so we can tell build mode functions which player called them.
        #We probably don't need bob since this functionality is only important when permissions
        #are concerned in build commands. We'll create and pass him in anyways for now.
        self.bob = Player(('bob', 'bar'))
        self.bob.mode = None
        self.bob.playerize({'name':'bob'})
        self.world.player_add(self.bob)
        self.bob.mode = BuildMode(self.bob)
        self.bob.permissions = self.bob.permissions | self.PERMS['builder']
        
        self.area = Area.create({'name': 'foo'})
    
    def tearDown(self):
        del self.area
        del self.bob
        
    def test_merchant_build_add_remove_item(self):
        npc = self.area.new_npc()
        npc.build_add_ai("merchant", self.bob)
        ai = npc.ai_packs['merchant']
        self.area.new_item()
        
        
        #Add items
        message = ai.build_add_item("", self.bob)
        self.assertEqual(message, 'Try "add item <item-id> from area <area-name> price <price>" or see "help merchant".')
        message = ai.build_add_item("BLARG", self.bob)
        self.assertEqual(message, 'Try "add item <item-id> from area <area-name> price <price>" or see "help merchant".')
        message = ai.build_add_item("1 from area_which_does_not_exist price 20", self.bob)
        self.assertEqual(message, 'Area "area_which_does_not_exist" doesn\'t exist.')
        message = ai.build_add_item("2 from foo price 20", self.bob)
        self.assertEqual(message, "Item 2 doesn't exist.")
        message = ai.build_add_item("1 from foo price 30", self.bob)
        self.assertEqual(message, "Merchant now sells New Item.")
        
        #remove items
        message = ai.build_remove_item("", self.bob)
        self.assertEqual(message, 'Try "remove item <item-id>", or see "help merchant".')
        message = ai.build_remove_item("BLARG", self.bob)
        self.assertEqual(message, 'Try "remove item <item-id>", or see "help merchant".')
        message = ai.build_remove_item("6203", self.bob)
        self.assertEqual(message, "That item doesn't exist.")
        message = ai.build_remove_item("0", self.bob)
        self.assertEqual(message, "That item doesn't exist.")
        message = ai.build_remove_item("-1", self.bob)
        self.assertEqual(message, 'Try "remove item <item-id>", or see "help merchant".')
        message = ai.build_remove_item("1", self.bob)
        self.assertEqual(message, 'Merchant no longer sells New Item.')
        
        #Clean up everything in the area so future tests don't have problems
        self.area.destroy_npc(1)
        self.area.destroy_item(1)
        
    def test_merchant_build_add_remove_types(self):
        #We'll need a merchant npc for this test!
        npc = self.area.new_npc()
        npc.build_add_ai("merchant", self.bob)
        ai = npc.ai_packs['merchant']
        
        #Test adding types with good and bad user input.
        tests = {
            "": 'Try "add type <item-type>", or see "help merchant".',
            "BLARG": 'blarg is not a valid item type. See "help merchant" for details.',
            'equippable': 'Merchant will now buy items of type equippable from players.',
            'plain': 'Merchant will now buy items of type plain from players.'
        }
        for (input_m, output_m) in tests.iteritems():
            self.assertEqual(ai.build_add_type(input_m, self.bob), output_m)
              
        #Test user input for removing types. Note: We test these inputs below with two
        #input types already added from the tests above. (equippable and plain)
        tests = {
            "":'Try "remove type <item-type>", or see "help merchant".',
            "BLARG":'blarg is not a valid item type. See "help merchant" for details.',
            "equippable":'Merchant no longer buys items of type equippable.',
            "plain":'Merchant no longer buys items of type plain.'
        }   
        for (input_m, output_m) in tests.iteritems():
            self.assertEqual(ai.build_remove_type(input_m, self.bob), output_m)
            
        #test trying to remove a vaild item type again, after we already did.
        message = ai.build_remove_type("equippable", self.bob)
        self.assertEqual(message, "Merchant already doesn't buy items of type equippable.")
        
        #cleanup for additional tests
        self.area.destroy_npc(1)
        self.area.destroy_item(1)
        
    def test_merchant_volatile_items(self):
        #Merchants can sell items from different areas, which can be
        #destroyed or re-imported/recreated at random. Make sure that
        #Merchants can still keep track of items amidst such chaos!
        from shinymud.models.area import Area
        #Create our merchant
        npc = self.area.new_npc()
        npc.build_add_ai("merchant", self.bob)
        ai = npc.ai_packs['merchant']
        
        #Create our area, with which we will have our missing 'dead item'
        area2 = Area.create({'name':'bar'})
        item = area2.new_item()
        item.name = 'trucknuts'
        item.save()
        
        #add item to area, make sure it added correctly
        message = ai.build_add_item('1 from area bar price 2000')
        self.assertEqual(message, 'Merchant now sells trucknuts.')
        self.assertEqual(item, ai.sale_items.verify_item(ai.sale_items.live[0]))
        self.assertEqual([], ai.sale_items.dead)
        
        #Destroy the area, with the item we're selling.
        self.world.destroy_area('bar', self.bob)
        self.assertFalse(self.world.area_exists('bar'))
        
        #ask for a copy of the merch list, make sure the item is not still
        #trying to be sold (dead)
        ai.sale_items.merch_list() # updates live,dead lists
        self.assertEqual([], ai.sale_items.live)
        self.assertTrue('trucknuts' in ai.sale_items.dead[0].values())
    
        #Recreate the same area and item
        area2 = Area.create({'name':'bar'})
        item = area2.new_item()
        item.name = 'trucknuts'
        item.save()
        
        #Update the list. Our item should be resurrected!
        ai.sale_items.merch_list()
        self.assertTrue('trucknuts' in ai.sale_items.live[0].values())
        self.assertEqual([], ai.sale_items.dead)
    
        
        