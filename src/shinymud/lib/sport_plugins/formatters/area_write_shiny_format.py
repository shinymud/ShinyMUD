from shinymud.lib.sport_plugins import SportError
from shinymud.data.config import VERSION

import json

def format(area):
    """Serialize an area into ShinyAreaFormat.
    
    area -- the area object to be serialized.
    """
    area_txt = ('[ShinyMUD Version "%s"]\n' % VERSION +
                  _pack_area(area) +
                  _pack_scripts(area) +
                  _pack_items(area) +
                  _pack_npcs(area) +
                  _pack_rooms(area)
                 )
    return area_txt

def _pack_area(area):
    d = area.create_save_dict()
    del d['dbid']
    return '\n[Area]\n' + json.dumps(d) + '\n[End Area]\n'

def _pack_scripts(area):
    s = []
    for script in area.scripts.values():
        d = script.create_save_dict()
        del d['dbid']
        s.append(d)
    return '\n[Scripts]\n' + json.dumps(s) + '\n[End Scripts]\n'

def _pack_items(area):
    item_list = []
    itypes_list = []
    
    for item in area.items.values():
        d = item.create_save_dict()
        del d['dbid']
        item_list.append(d)
        for key,value in item.item_types.items():
            d = value.create_save_dict()
            d['item'] = item.id
            del d['dbid']
            d['item_type'] = key
            itypes_list.append(d)
    s = '\n[Items]\n' + json.dumps(item_list) + '\n[End Items]\n'
    s += '\n[Item Types]\n' + json.dumps(itypes_list) + '\n[End Item Types]\n'
    return s

def _pack_npcs(area):
    npc_list = []
    npc_elist = []
    
    for npc in area.npcs.values():
        d = npc.create_save_dict()
        del d['dbid']
        npc_list.append(d)
        event_list = []
        for elist in npc.events.values():
            event_list.extend(elist)
        for event in event_list:
            d = event.create_save_dict()
            del d['dbid']
            d['prototype'] = npc.id
            d['script'] = event.script.id
            npc_elist.append(d)
    s = '\n[Npcs]\n' + json.dumps(npc_list) + '\n[End Npcs]\n'
    s += '\n[Npc Events]\n' + json.dumps(npc_elist) + '\n[End Npc Events]\n'
    return s

def _pack_rooms(area):
    r_list = []
    r_exits = []
    r_spawns = {} # r_spawns is a dictionary of lists of dictionaries!
    for room in area.rooms.values():
        d = room.create_save_dict()
        # d['room'] = room.id
        del d['dbid']
        r_list.append(d)
        r_spawns[room.id] = []
        for exit in room.exits.values():
            if exit:
                d = exit.create_save_dict()
                d['room'] = room.id
                d['to_id'] = exit.to_room.id
                d['to_area'] = exit.to_room.area.name
                d['to_room'] = None
                del d['dbid']
                r_exits.append(d)
        for spawn in room.spawns.values():
            d = spawn.create_save_dict()
            del d['dbid']
            r_spawns[room.id].append(d)
    s = '\n[Rooms]\n' + json.dumps(r_list) + '\n[End Rooms]\n'
    s += '\n[Room Exits]\n' + json.dumps(r_exits) + '\n[End Room Exits]\n'
    s += '\n[Room Spawns]\n' + json.dumps(r_spawns) + '\n[End Room Spawns]\n'
    return s

