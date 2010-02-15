from shinymud.models.area import Area
from shinymud.models.room import Room
from shinymud.models.item import Item
from shinymud.models.npc import Npc
from shinymud.lib.world import World
from shinymud.data.config import AREAS_IMPORT_DIR, AREAS_EXPORT_DIR, VERSION

import os
import re
import logging
import simplejson as json

class SPort(object):
    """Export and import areas (and their objects) to a file."""
    def __init__(self):
        self.log = logging.getLogger('XPort')
        self.world = World.get_world()
        error = self.check_export_path()
        if error:
            return error
    
    def export_to_shiny(self, area):
        """Export an area to a text file in ShinyAreaFormat.
        area -- the area object to be exported
        """
        shiny_area = '[ShinyMUD Version "%s"]\n' % VERSION
        d = area.to_dict()
        del d['dbid']
        shiny_area += '\n[Area]\n' + json.dumps(d) + '\n[End Area]\n'
        
        s_list = []
        for script in area.scripts.values():
            d = script.to_dict()
            del d['dbid']
            s_list.append(d)
        shiny_area += '\n[Scripts]\n' + json.dumps(s_list) + '\n[End Scripts]\n'
        
        item_list = []
        itypes_list = []
        
        for item in area.items.values():
            d = item.to_dict()
            del d['dbid']
            item_list.append(d)
            for key,value in item.item_types.items():
                d = value.to_dict()
                d['item'] = item.id
                del d['dbid']
                d['item_type'] = key
                itypes_list.append(d)
        shiny_area += '\n[Items]\n' + json.dumps(item_list) + '\n[End Items]\n'
        shiny_area += '\n[Item Types]\n' + json.dumps(itypes_list) + '\n[End Item Types]\n'
        
        npc_list = []
        npc_elist = []
        
        for npc in area.npcs.values():
            d = npc.to_dict()
            del d['dbid']
            npc_list.append(d)
            for event in npc.events.values():
                d = event.to_dict()
                del d['dbid']
                d['prototype'] = npc.id
                d['script'] = event.script.id
                npc_elist.append(d)
        shiny_area += '\n[Npcs]\n' + json.dumps(npc_list) + '\n[End Npcs]\n'
        shiny_area += '\n[Npc Events]\n' + json.dumps(npc_elist) + '\n[End Npc Events]\n'
        
        r_list = []
        r_exits = []
        r_resets = {} # r_resets is a dictionary of lists of dictionaries!
        for room in area.rooms.values():
            d = room.to_dict()
            # d['room'] = room.id
            del d['dbid']
            r_list.append(d)
            r_resets[room.id] = []
            for exit in room.exits.values():
                if exit:
                    d = exit.to_dict()
                    d['room'] = room.id
                    d['to_id'] = exit.to_room.id
                    d['to_area'] = exit.to_room.area.name
                    d['to_room'] = None
                    del d['dbid']
                    r_exits.append(d)
            for reset in room.resets.values():
                d = reset.to_dict()
                r_resets[room.id].append(d)
        shiny_area += '\n[Rooms]\n' + json.dumps(r_list) + '\n[End Rooms]\n'
        shiny_area += '\n[Room Exits]\n' + json.dumps(r_exits) + '\n[End Room Exits]\n'
        shiny_area += '\n[Room Resets]\n' + json.dumps(r_resets) + '\n[End Room Resets]\n'
        
        return self.save_to_file(shiny_area, area.name + '.txt')
    
    def import_from_shiny(self, areaname):
        """Import an area from a text file in ShinyAreaFormat."""
        txt = self.get_import_data(areaname + '.txt')
        # Assemble the data structures from the file text
        area = json.loads(self.match_shiny_tag('Area', txt))
        scripts = json.loads(self.match_shiny_tag('Scripts', txt))
        items = json.loads(self.match_shiny_tag('Items', txt))
        itypes = json.loads(self.match_shiny_tag('Item Types', txt))
        npcs = json.loads(self.match_shiny_tag('Npcs', txt))
        npc_events = json.loads(self.match_shiny_tag('Npc Events', txt))
        rooms = json.loads(self.match_shiny_tag('Rooms', txt))
        room_exits = json.loads(self.match_shiny_tag('Room Exits', txt))
        room_resets = json.loads(self.match_shiny_tag('Room Resets', txt))
        # Build the area from the assembled dictionary data
        # try:
        new_area = Area.create(**area)
        for script in scripts:
            new_area.new_script(script)
        for item in items:
            new_area.new_item(item)
        for itype in itypes:
            # Get this itype's item by that item's id
            my_item = new_area.get_item(itype['item'])
            my_item.add_type(itype['item_type'], itype)
        for npc in npcs:
            new_area.new_npc(npc)
        for event in npc_events:
            my_script = new_area.get_script(str(event['script']))
            event['script'] = my_script
            my_npc = new_area.get_npc(event['prototype'])
            my_npc.new_event(event)
        for room in rooms:
            new_room = new_area.new_room(room)
            my_resets = room_resets.get(new_room.id)
            if my_resets:
                new_room.load_resets(my_resets)
        for exit in room_exits:
            self.log.debug(exit['room'])
            my_room = new_area.get_room(str(exit['room']))
            my_room.new_exit(**exit)
        # except Exception, e:
        #     # if anything went wrong, make sure we destroy whatever parts of
        #     # the area that got created.  This way, we won't run into problems
        #     # if they try to import it again, and we won't leave orphaned or
        #     # erroneous data in the db.
        #     self.log.error(str(e))
        #     self.world.destroy_area(areaname, 'SPort Error')
        #     raise SPortImportError('There was a horrible error on import! '
        #                            'Aborting! Check logfile for details.')
        
        return 'Area %s has been successfully imported.' % new_area.name
    
    def match_shiny_tag(self, tag, text):
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
            raise SPortImportError('Corrupted file: missing or malformed %s tag.' % tag)
        return match.group('tag_body')
    
    def export_to_xml(self, area):
        """Export an area to an xml file."""
        #************* Build the area attributes *************
        area_xml = '<area '
        area_dict = area.to_dict()
        if area_dict['dbid']:
            del area_dict['dbid']
        for key,value in area_dict.items():
            area_xml += '%s="%s" ' % (key, value)
        area_xml += '>'
        #************* Build the items *************
        area_xml += '<items>'
        for item in area.items.values():
            area_xml += '<item '
            item_dict = item.to_dict()
            del item_dict['dbid']
            del item_dict['area']
            for key,value in item_dict.items():
                area_xml += '%s="%s" ' % (key, value)
            # Save this item's item types
            area_xml += '><item_types>'
            for name,value in item.item_types.items():
                td = value.to_dict()
                td['name'] = name
                del td['dbid']
                itype = ' '.join(['%s="%s" ' % (key, value) for key,value in td.items()])
                area_xml += '<item_type ' + itype + '></item_type>'
            area_xml += '</item_types></item>'
        area_xml += '</items>'
        #************* Build the scripts *************
        area_xml += '<scripts>'
        for script in area.scripts.values():
            area_xml += '<script'
            s_dict = script.to_dict()
            del s_dict['dbid']
            del s_dict['area']
            for key,value in s_dict.items():
                area_xml += '%s="%s" ' % (key, value)
            area_xml += '></script>'
        area_xml += '</scripts>'
        #************* Build the npcs *************
        area_xml += '<npcs>'
        for npc in area.npcs.values():
            area_xml += '<npc '
            npc_dict = npc.to_dict()
            del npc_dict['dbid']
            del npc_dict['area']
            for key,value in npc_dict.items():
                area_xml += '%s="%s" ' % (key, value)
            area_xml += '></npc>'
        area_xml += '</npcs>'
        #************* Build the rooms *************
        area_xml += '<rooms>'
        for room in area.rooms.values():
            area_xml += '<room '
            room_dict = room.to_dict()
            del room_dict['dbid']
            del room_dict['area']
            for key,value in room_dict.items():
                area_xml += '%s="%s" ' % (key, value)
            area_xml += '><resets>'
            for reset in room.resets.values():
                area_xml += '<reset '
                reset_dict = reset.to_dict()
                for key,value in reset_dict.items():
                    area_xml += '%s="%s" ' % (key, value)
                area_xml += '></reset>'
            area_xml += '</resets><exits>'
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
        
        return self.save_to_file(area_xml, area.name + '.xml')
    
    def import_from_xml(self, areaname):
        """Import an area from an xml file."""
        filepath = os.path.join(AREAS_IMPORT_DIR, areaname + '.xml')
        if not os.path.exists(filepath):
            return 'That area is not in your import directory.'
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
                idict = dict([(str(key),str(value)) for key,value in itype.attributes.items()])
                item_dict[idict['name']] = idict
                # key = str(itype.attributes['name'].value)
                # item_dict['item_types'][key] = {}
                # for child in itype.childNodes:
                #     if child.firstChild:
                #         item_dict['item_types'][key][str(child.tagName)] = str(child.firstChild.data)
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
            room_dict['resets'] = []
            room_dict['exits'] = []
            reset_dom = room.getElementsByTagName('reset')
            for reset in reset_dom:
                room_dict['resets'].append(dict([(str(key),str(value)) for key,value in reset.attributes.items()]))
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
                new_room.load_resets(room_dict['resets'])
                # for reset in room_dict['item_resets']:
                #     item_reset = new_area.get_item(reset)
                #     if item_reset:
                #         new_room.item_resets.append(item_reset)
                # for reset in room_dict['npc_resets']:
                #     npc_reset = new_area.get_npc(reset)
                #     if npc_reset:
                #         new_room.npc_resets.append(npc_reset)
                
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
        finally:
            area_dom.unlink()
        return 'Area %s has been successfully imported!\n' % new_area.name
    
    @classmethod
    def list_importable_areas(cls):
        if not os.path.exists(AREAS_IMPORT_DIR):
            return 'There are no area files in your import directory.'
        # Give the user a list of names of all the area files in their import directory
        # and trim off the .xml extension for readibility. Ignore all files that aren't xml
        # files
        alist = [area.replace('.xml', '') for area in os.listdir(AREAS_IMPORT_DIR) if area.endswith('.xml')]
        if alist:
            return 'The following areas are available for import:\n' + '\n'.join(alist) + '\n'
        else:
            return 'There are no area files in your import directory.'
    
    def check_export_path(self):
        """Make sure the path to the export directory exists. If it doesn't,
        create it and return an empty string. If there's an error, log it and
        return an error message."""
        if not os.path.exists(AREAS_EXPORT_DIR):
            try:
                os.mkdir(AREAS_EXPORT_DIR)
            except Exception, e:
                self.log.error('EXPORT FAILED: ' + str(e))
                # TODO: reraise an SPortExportError here...
                return 'Export failed; something went wrong accessing the export directory for areas.'
        return ''
    
    def get_import_data(self, filename):
        filepath = os.path.join(AREAS_IMPORT_DIR, filename)
        if not os.path.exists(filepath):
            raise SPortImportError('Error: %s does not exist.' % filename)
            
        try:
            f = open(filepath, 'r')
        except IOError, e:
            self.log.debug(str(e))
            raise SPortImportError('Error: opening the area file failed. '
                                   'Check the logfile for details.')
        else:
            area_txt = f.read()
        finally: 
            f.close()
            
        return area_txt
    
    def save_to_file(self, file_content, file_name):
        """Write out the file contents under the given file_name."""
        filepath = os.path.join(AREAS_EXPORT_DIR, file_name)
        try:
            f = open(filepath, 'w')
        except IOError, e:
            self.log.debug(str(e))
            raise SPExportError('Error writing your area to file. '
                                'Check the logfile for details')
        else:
            f.write(file_content)
        finally:
            f.close()
        return 'Export complete! Your area can be found at:\n%s' % filepath
    

class SPortImportError(Exception):
    """The umbrella exception for errors that occur during area import.
    """
    pass
    

class SPortExportError(Exception):
    """The umbrella exception for errors that occur during area export.
    """
    pass
        