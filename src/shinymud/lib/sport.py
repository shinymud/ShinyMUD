from shinymud.lib.world import World
from shinymud.data.config import AREAS_IMPORT_DIR, AREAS_EXPORT_DIR
from shinymud.lib.sport_plugins import SportError

import os
import re
import traceback

PATH = os.path.abspath(os.path.dirname(__file__))
NAME_REG = re.compile(r'(?P<name>[^_]+)_(?P<type>[^\.]+)\.(?P<format>\w+)')
DEFAULT_FORMAT = 'shiny_format'
DEFAULT_TRANSPORT = 'file'

def inport(obj_type, obj_name, format=None, transport=None, source_path=AREAS_IMPORT_DIR):
    """Import an object (area, player character, etc.) from an outside source
    into the MUD.
    
    obj_type - the type of the object to be imported (area, player, etc.)
    obj_name - the name of the object to be imported
    format - the format that the object data is saved in and that should be used decode it
    transport - the transport that should be used to retrieve the data
    source_path - extra information for locating an import object
    """
    format = format or DEFAULT_FORMAT
    transport = transport or DEFAULT_TRANSPORT
    world = World.get_world()
    
    if not hasattr(world, '%s_exists' % obj_type):
        return 'Invalid type "%s". See "help export".' % obj_type
    if getattr(world, '%s_exists' % obj_type)(obj_name):
        return '%s "%s" already exists in your game.' % (obj_type.capitalize(), obj_name)
    
    try:
        #Find format
        formatter = get_formatter('%s_read_%s' % (obj_type, format))
        #find source
        source = get_transport('load_%s' % transport)
        # all source-transports take world, the name of the target, and the source path
        # all read-formaters take the world and shiny_data
        fname = obj_name + '_' + obj_type + '.' + format
        message = formatter(world, source(world, fname, source_path))
    except SportError as e:
        message = str(e)
    return message

def export(obj_type, shiny_obj, format=None, transport=None, dest_path=AREAS_EXPORT_DIR):
    """Export an object from the MUD to an outside source.
    
    obj_type - the type of the object to be imported (area, player, etc.)
    shiny_obj - the shiny object being exported
    format - the format that the object data should be exported in
    transport - the transport that should be used to save the data
    dest_path - extra information for sending/saving the object
    """
    format = format or DEFAULT_FORMAT
    transport = transport or DEFAULT_TRANSPORT
    world = World.get_world()
    try:
        formatter = get_formatter('%s_write_%s' % (obj_type, format))
        #find source
        dest = get_transport('save_%s' % transport)
        # all destination transports take world, shiny_data, filename, and destination_path
        # all write-formatters take a shiny object.
        fname = shiny_obj.name + '_' + obj_type + '.' + format
        message = dest(world, formatter(shiny_obj), fname, dest_path)
    except SportError as e:
        message = str(e)
    return message

def inport_dir(obj_type, format=None, source_path=AREAS_IMPORT_DIR):
    """Import a batch of area files from a directory.
    import_list can either be a list of area-names to be imported,
    or the string 'all'. If the string 'all' is given, import_list will
    attempt to import all areas in the default import directory.
    """
    world = World.get_world()
    import_list = []
    for filename in os.listdir(source_path):
        match = NAME_REG.match(filename)
        if match:
            fname, ftype, fformat = match.group('name', 'type', 'format')
            # filter by obj_type
            if ftype == obj_type:
                # filter by format (only if format is not None)
                if format and (format == fformat):
                    import_list.append({'name': fname, 'format': fformat})
                elif not format:
                    import_list.append({'name': fname, 'format': fformat})
    if not import_list:
        return "I couldn't find any %ss in %s." % (obj_type, source_path)
    
    results = ''
    for thing in import_list:
        results += 'Importing %s %s... ' % (obj_type, thing['name'])
        try:
            status = inport(obj_type, thing['name'], thing['format'], 'file', 
                            source_path)
        except SportError as e:
            results += 'Failed: ' + str(e) + '\n'
        else:
            results += status + '\n'
    if not results:
        return 'No areas were found in %s.\n' % source_path
    return results

def list_importable(obj_type, format=None, transport=None, source_path=None):
    """ List the objects that are available for import.
     
    obj_type - the type of object to be imported
    format - (optional) filter results by this format
    transport - The transport by which the data will be obtained (if not given, 
        the DEFAULT_TRANSPORT will be used)
    source_path - any extra data needed to locate the objects to be listed
    """
    # get the transport list function
    transport = transport or DEFAULT_TRANSPORT
    obj_list = get_import_lister(transport)(source_path)
    
    cute_list = ''
    for obj in obj_list:
        oname, otype, oformat = NAME_REG.match(obj).group('name', 'type', 'format')
        # TODO: filter by format should also happen if a format is given
        if otype == obj_type:
            cute_list += '\n%s (import format: %s)' % (oname, oformat)
    
    if cute_list:
        return (' %ss Available For Import ' % obj_type.capitalize()).center(50, '-') + cute_list + '\n' + ('-' * 50)
    else:
        return 'No importable %ss were found.' % obj_type

def get_formatter(format_file):
    """ Get a formatter by its file name.
    Returns the formatter function if it can be found and raises a SportError if
    it can't.
     
    format_file - the filename of the desired formatter (without the .py extension)
    """
    # get a list of the files in the formatters folder.
    if (format_file + '.py') in os.listdir(os.path.join(PATH, 'sport_plugins/formatters')):
        # import the formatter from that file and return it
        f = __import__('shinymud.lib.sport_plugins.formatters.%s' % format_file, globals(), locals(), ['format'], -1)
    else:
        raise SportError('Cannot find formatter: %s' % format_file)
    return f.format

def get_transport(t_file):
    """ Get a transport by its file name.
    Returns the transport function if it can be found and raises a SportError if
    it can't.
     
    t_file - the filename of the desired transport (without the .py extension)
    """
    # get a list of the files in the transports folder.
    if (t_file + '.py') in os.listdir(os.path.join(PATH, 'sport_plugins/transports')):
        # import the transport from that file and return it
        t = __import__('shinymud.lib.sport_plugins.transports.%s' % t_file, globals(), locals(), ['transport'], -1)
    else:
        raise SportError('Cannot find transport: %s' % t_file)
    return t.transport

def get_import_lister(transport):
    """ Get a transport's list function.
    Return a transport's list function if it exists, or raise a SportError if it
    does not.
     
    transport - the name of the transport whose list function should be returned
    """
    if ('load_%s.py' % transport) in os.listdir(os.path.join(PATH, 'sport_plugins/transports')):
        trans = __import__('shinymud.lib.sport_plugins.transports.load_%s' % transport, globals(), locals(), ['get_list'], -1)
    else:
        raise SportError("The %s transport either doesn't exist or doesn't have the ability to list available imports. Sorry." % transport)
    return trans.get_list

