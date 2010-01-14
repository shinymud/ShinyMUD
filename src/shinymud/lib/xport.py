from shinymud.models.area import Area
from shinymud.models.room import Room
from shinymud.models.item import Item
from shinymud.models.npc import Npc
from shinymud.lib.world import World
from shinymud.config import AREAS_IMPORT_DIR, AREAS_EXPORT_DIR

import os
import logging
from xml.dom.minidom import parse

class XPort(object):
    """Export and import areas (and their objects) to/from an XML file."""
    def __init__(self):
        self.log = logging.getLogger('XPort')
        self.world = World.get_world()
    
    def export_to_xml(self, area):
        area_xml = '<area '
        if not os.path.exists(AREAS_EXPORT_DIR):
            try:
                os.mkdir(AREAS_EXPORT_DIR)
            except Exception, e:
                self.log.error('EXPORT FAILED: ' + str(e))
                return 'Export failed; something went wrong accessing the export directory for areas.\n'
        #************* Build the area attributes *************
        area_dict = area.to_dict()
        if area_dict['dbid']:
            del area_dict['dbid']
        for key,value in area_dict.items():
            area_xml += '%s="%s" ' % (key, value)
        area_xml += '><items>'
        #************* Build the items *************
        for item in area.items.values():
            area_xml += '<item '
            item_dict = item.to_dict()
            del item_dict['dbid']
            del item_dict['area']
            for key,value in item_dict.items():
                area_xml += '%s="%s" ' % (key, value)
            area_xml += '><item_types>'
            for name,value in item.item_types.items():
                area_xml += '<item_type name="%s">' % name
                type_dict = value.to_dict()
                del type_dict['dbid']
                del type_dict['item']
                for key,value in type_dict.items():
                    area_xml += '<%s>%s</%s>' % (key, value, key)
                area_xml += '</item_type>'
            area_xml += '</item_types></item>'
        area_xml += '</items><npcs>'
        #************* Build the npcs *************
        for npc in area.npcs.values():
            area_xml += '<npc '
            npc_dict = npc.to_dict()
            del npc_dict['dbid']
            del npc_dict['area']
            for key,value in npc_dict.items():
                area_xml += '%s="%s" ' % (key, value)
            area_xml += '></npc>'
        area_xml += '</npcs><rooms>'
        #************* Build the rooms *************
        for room in area.rooms.values():
            area_xml += '<room '
            room_dict = room.to_dict()
            del room_dict['dbid']
            del room_dict['area']
            for key,value in room_dict.items():
                area_xml += '%s="%s" ' % (key, value)
            area_xml += '><item_resets>'
            for reset in room.item_resets:
                area_xml += '<id>%s</id>' % reset.id
            area_xml += '</item_resets><npc_resets>'
            for reset in room.npc_resets:
                area_xml += '<id>%s</id>' % reset.id
            area_xml += '</npc_resets><exits>'
            for exit in room.exits.values():
                if exit and (exit.to_area == area.name):
                    area_xml += '<exit '
                    exit_dict = exit.to_dict()
                    del exit_dict['dbid']
                    del exit_dict['room']
                    exit_dict['to_room'] = exit.to_id
                    if 'key' in exit_dict:
                        if exit.key_area == area.name:
                            exit_dict['key'] = exit.key_id
                        else:
                            del exit_dict['key']
                    for key,value in exit_dict.items():
                        area_xml += '%s="%s" ' % (key, value)
                    area_xml += '></exit>'
            area_xml += '</exits></room>'
        area_xml += '</rooms></area>'
        
        filename = area.name + '.xml'
        filepath = os.path.join(AREAS_EXPORT_DIR, filename)
        
        with open(filepath, 'w') as f:
            f.write(area_xml)
        return 'Export complete! Your area can be found at:\n%s\n' % filepath
    
    def import_from_xml(self, areaname):
        filepath = os.path.join(AREAS_IMPORT_DIR, areaname + '.xml')
        if not os.path.exists(filepath):
            return 'That area is not in your import directory.\n'
        area_dom  = parse(filepath)
        area_dom = area_dom.getElementsByTagName('area')[0]
        area_dict = dict([(str(key),str(value)) for key,value in area_dom.attributes.items()])
        
        item_dom = area_dom.getElementsByTagName('items')[0]
        items = []
        for item in item_dom.childNodes:
            item_dict = dict([(str(key),str(value)) for key,value in item.attributes.items()])
            item_types_dom = item_dom.getElementsByTagName('item_type')
            item_dict['item_types'] = {}
            for itype in item_types_dom:
                key = str(itype.attributes['name'].value)
                item_dict['item_types'][key] = {}
                for child in itype.childNodes:
                    item_dict['item_types'][key][str(child.tagName)] = str(child.firstChild.data)
            items.append(item_dict)
        
        npc_dom = area_dom.getElementsByTagName('npcs')[0]
        npcs = []
        for npc in npc_dom.childNodes:
            npc_dict = dict([(str(key),str(value)) for key,value in npc.attributes.items()])
            npcs.append(npc_dict)
        
        room_dom = area_dom.getElementsByTagName('rooms')[0]
        rooms = []
        for room in room_dom.childNodes:
            room_dict = dict([(str(key),str(value)) for key,value in room.attributes.items()])
            room_dict['item_resets'] = []
            room_dict['npc_resets'] = []
            room_dict['exits'] = []
            ireset_dom = room.getElementsByTagName('item_resets')[0]
            resets = ireset_dom.getElementsByTagName('id')
            for reset in resets:
                room_dict['item_resets'].append(str(reset.firstChild.data))
            nreset_dom = room.getElementsByTagName('npc_resets')[0]
            resets = nreset_dom.getElementsByTagName('id')
            for reset in resets:
                room_dict['npc_resets'].append(str(reset.firstChild.data))
            exit_dom = room.getElementsByTagName('exit')
            for exit in exit_dom:
                exit_dict = dict([(str(key),str(value)) for key,value in exit.attributes.items()])
                room_dict['exits'].append(exit_dict)
            rooms.append(room_dict)
        
        # Building the area
        try:
            new_area = Area.create(**area_dict)
            for item_dict in items:
                item_dict['area'] = new_area
                new_item = new_area.new_item(item_dict)
                for key, value in item_dict['item_types'].items():
                    self.log.info(new_item.add_type(key, value))
            
            for npc_dict in npcs:
                npc_dict['area'] = new_area
                new_npc = new_area.new_npc(npc_dict)
        
            # rooms is a list of room dictionaries
            for room_dict in rooms:
                room_dict['area'] = new_area
                new_room = new_area.new_room(room_dict)
                for reset in room_dict['item_resets']:
                    item_reset = new_area.get_item(reset)
                    if item_reset:
                        new_room.item_resets.append(item_reset)
                for reset in room_dict['npc_resets']:
                    npc_reset = new_area.get_npc(reset)
                    if npc_reset:
                        new_room.npc_resets.append(npc_reset)
                    
            for room_dict in rooms:
                room = new_area.get_room(room_dict.get('id'))
                for exit in room_dict['exits']:
                    exit['to_id'] = exit['to_room']
                    exit['to_area'] = new_area.name
                    exit['to_room'] = None
                    room.new_exit(**exit)
        except Exception, e:
            # If we fail in the above code for ANY reason, make sure we delete
            # any bits of the area we have imported thus far, then log it.
            
            self.world.destroy_area(areaname, 'XPort: corrupt area file.')
            self.log.error(str(e))
            return 'Error importing area: %s.\n' % str(e)
        
        area_dom.unlink()
        return 'Area %s has been successfully imported!\n' % new_area.name
    
    @classmethod
    def list_importable_areas(cls):
        if not os.path.exists(AREAS_IMPORT_DIR):
            return 'There are no area files in your import directory.\n'
        # Give the user a list of names of all the area files in their import directory
        # and trim off the .xml extension for readibility. Ignore all files that aren't xml
        # files
        alist = [area.replace('.xml', '') for area in os.listdir(AREAS_IMPORT_DIR) if area.endswith('.xml')]
        if alist:
            return 'The following areas are available for import:\n' + '\n'.join(alist) + '\n'
        else:
            return 'There are no area files in your import directory.\n'
