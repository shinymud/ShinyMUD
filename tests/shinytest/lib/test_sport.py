from shinytest import ShinyTestCase

class TestSport(ShinyTestCase):
    def test_shinyexport_prep_rooms(self):
        from shinymud.models.area import Area
        area = Area.create({'name': 'foo'})
        rd = {'id': '1', 'name': 'Room 1', 'description': 'Cool room.'}
        room = area.new_room(rd)
        room2 = area.new_room()
        room.link_exits('north', room2)
        area.new_item()
        area.new_npc()
        room.build_add_spawn('item 1')
        room2.build_add_spawn('npc 1')
    

