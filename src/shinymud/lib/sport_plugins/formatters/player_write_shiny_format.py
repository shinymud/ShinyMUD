"""write formatter: player_write_shiny_format.py

Resulting serialized output will look like the following string (but obviously
with actual data in the place of <data>):

[ShinyMUD Version "X.X"]

[Player]
<data>
[End Player]

[Inv Items]
(item_data, {item_type_name: item_type_data, ...})
[End Inv Items]

"""
from shinymud.lib.sport_plugins import SportError
from shinymud.data.config import VERSION

import json

def format(pc):
    """Serialize a player character (and their inventory) into ShinyFormat.
    
    pc -- the player object to be serialized.
    """
    player_txt = ('[ShinyMUD Version "%s"]\n' % VERSION +
                  _pack_player(pc) +
                  '\n[Inv Items]\n' + json.dumps(_pack_items(pc.inventory)) +
                  '\n[End Inv Items]\n'
                 )
                 
    return player_txt

def _pack_player(pc):
    d = pc.create_save_dict()
    del d['dbid']
    
    return '\n[Player]\n' + json.dumps(d) + '\n[End Player]\n'

def _pack_items(item_list):
    i_list = []
    for item in item_list:
        typed = {}
        for key,value in item.item_types.items(): # hehe
            typed[key] = value.create_save_dict()
            del typed[key]['dbid']
            if key == 'container':
                i_list.extend(_pack_items(value.inventory))
        itemd = item.create_save_dict()
        i_list.append((itemd, typed))
    
    return i_list
