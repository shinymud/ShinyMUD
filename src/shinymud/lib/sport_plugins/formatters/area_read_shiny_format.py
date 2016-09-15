from shinymud.lib.sport_plugins import SportError
from shinymud.models.area import Area

import traceback
import json
import re

def format(world, raw_data):
    """Deserialize an area saved in ShinyAreaFormat and adds it to the world.
    
    raw_data - the data to be deserialized into a Shiny Area object.
    world - The World instance
    """
    area = json.loads(_match_shiny_tag('Area', raw_data))
    scripts = json.loads(_match_shiny_tag('Scripts', raw_data))
    items = json.loads(_match_shiny_tag('Items', raw_data))
    itypes = json.loads(_match_shiny_tag('Item Types', raw_data))
    npcs = json.loads(_match_shiny_tag('Npcs', raw_data))
    npc_events = json.loads(_match_shiny_tag('Npc Events', raw_data))
    rooms = json.loads(_match_shiny_tag('Rooms', raw_data))
    room_exits = json.loads(_match_shiny_tag('Room Exits', raw_data))
    room_spawns = json.loads(_match_shiny_tag('Room Spawns', raw_data))
    # Build the area from the assembled dictionary data
    try:
        new_area = Area.create(area)
        for script in scripts:
            new_area.new_script(script)
        world.log.debug('Finished Scripts.')
        for item in items:
            world.log.debug('In item, %s' % item['id'])
            new_area.new_item(item)
        world.log.debug('Finished Items.')
        for itype in itypes:
            # Get this itype's item by that item's id
            my_item = new_area.get_item(itype['item'])
            my_item.load_type(itype['item_type'], itype)
        world.log.debug('Finished Item types.')
        for npc in npcs:
            new_area.new_npc(npc)
        for event in npc_events:
            my_script = new_area.get_script(str(event['script']))
            event['script'] = my_script
            my_npc = new_area.get_npc(event['prototype'])
            my_npc.new_event(event)
        for room in rooms:
            new_room = new_area.new_room(room)
            my_spawns = room_spawns.get(new_room.id)
            if my_spawns:
                new_room.load_spawns(my_spawns)
        for exit in room_exits:
            world.log.debug(exit['room'])
            my_room = new_area.get_room(str(exit['room']))
            my_room.new_exit(exit)
    except Exception as e:
        # if anything went wrong, make sure we destroy whatever parts of
        # the area that got created. This way, we won't run into problems
        # if they try to import it again, and we won't leave orphaned or
        # erroneous data in the db.
        world.log.error(traceback.format_exc())
        world.destroy_area(area.get('name'), 'SPort Error')
        raise SportError('There was a horrible error on import! '
                         'Aborting! Check logfile for details.')
    new_area.reset()
    
    return '%s has been successfully imported.' % new_area.title
    

def _match_shiny_tag(tag, text):
    """Match a ShinyTag from the ShinyAreaFormat.
    tag -- the name of the tag you wish to match
    text -- the text to be searched for the tags
    Returns the string between the tag and its matching end-tag.
    Raises an exception if the tag is not found.
    """
    exp = r'\[' + tag + r'\](\n)?(?P<tag_body>.*?)(\n)?\[End ' + tag +\
          r'\](\n)?'
    match = re.search(exp, text, re.I | re.S)
    if not match:
        raise SportError('Corrupted file: missing or malformed %s tag.' % tag)
    return match.group('tag_body')
