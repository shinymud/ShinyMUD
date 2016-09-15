from shinymud.lib.sport_plugins import SportError
from shinymud.models.player import Player
from shinymud.models.item import GameItem
from shinymud.models.item_types import ITEM_TYPES

import traceback
import json
import re

def format(world, raw_data):
    """Deserialize a player character saved in ShinyFormat and adds it to 
    the world.
    
    raw_data - the data to be deserialized into a player object.
    world - The World instance
    """
    pc = json.loads(_match_shiny_tag('Player', raw_data))
    items = json.loads(_match_shiny_tag('Inv Items', raw_data))
    # Build the area from the assembled dictionary data
    try:
        new_pc = Player(('foo', 'bar'))
        new_pc.playerize(pc)
        new_pc.save()
        # Inventory time!
        containers = {} # old_container_dbid : [new_containee1, ...]
        old_new = {} # old dbid's mapped to their new ones
        
        for item in items:
            my_container = item[0].get('container')
            old_dbid = item[0]['dbid']
            del item[0]['dbid']
            if item[0].get('owner'):
                item[0]['owner'] = new_pc.dbid
            else:
                del item[0]['container']
            i = GameItem(item[0])
            i.save()
            load_item_types(i, item[1])
            old_new[old_dbid] = i.dbid
            if my_container:
                if containers.get(my_container):
                    containers[my_container].append(i)
                else:
                    containers[my_container] = [i]
        
        for old_container_dbid, containees_list in containers.items():
            for containee in containees_list:
                containee.container = old_new.get(old_container_dbid)
                containee.save()
            
    except Exception as e:
        # if anything went wrong, make sure we destroy any leftover character
        # data. This way, we won't run into problems if they try to import it
        # again, and we won't leave orphaned or erroneous data in the db.
        world.log.error(traceback.format_exc())
        try:
            new_pc.destruct()
        except:
            # if something goes wrong destroying the pc, it probably means we
            # didn't get far enough to have anything to destroy. Just ignore any
            # errors.
            pass
        
        raise SportError('There was a horrible error on import! '
                         'Aborting! Check logfile for details.')
    
    return 'Character "%s" has been successfully imported.' % new_pc.fancy_name()

def load_item_types(item, item_types):
    for name,data in item_types.items():
        if name in ITEM_TYPES:
            data['game_item'] = item.dbid
            new_itype = ITEM_TYPES[name](data)
            new_itype.save()

def _match_shiny_tag(tag, text):
    """Match a ShinyTag from ShinyFormat.
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
