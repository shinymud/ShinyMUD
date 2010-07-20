from shinymud.lib.world import World
from shinymud.data.config import AREAS_IMPORT_DIR, AREAS_EXPORT_DIR
from shinymud.lib.sport_plugins import SportError

import os
import traceback

PATH = os.path.abspath(os.path.dirname(__file__))

def inport(obj_type, obj_name, format='shiny_format', transport='file', source=AREAS_IMPORT_DIR):
    world = World.get_world()
    try:
        #Find format
        formatter = get_formatter('%s_read_%s' % (obj_type, format))
        #find source
        source = get_transport('read_%s' % transport)
        # all source-transports take world, the name of the target, and the source path
        # all read-formaters take the world and shiny_data
        message = formatter(world, source(world, obj_name, source))
    except SportError as e:
        message = str(e)
    return message

def export(obj_type, shiny_obj, format='shiny_format', transport='file', dest=AREAS_EXPORT_DIR):
    world = World.get_world()
    try:
        formatter = get_formatter('%s_write_%s' % (obj_type, format))
        #find source
        dest = get_transport('write_%s' % transport)
        # all destination transports take world, shiny_data, filename, and destination_path
        # all write-formatters take a shiny object.
        message = dest(world, formatter(shiny_obj), shiny_obj.name, dest)
    except SportError as e:
        message = str(e)
    return message

def inport_batch(self, import_list):
    """Import a batch of area files from import_list.
    import_list can either be a list of area-names to be imported,
    or the string 'all'. If the string 'all' is given, import_list will
    attempt to import all areas in the default import directory.
    """
    results = ''
    if import_list == 'all':
        import_list = [area.replace('.txt', '') for area in\
                     os.listdir(self.import_dir) if\
                     area.endswith('.txt')]
        if not import_list:
            return "I couldn't find any pre-packaged areas.\n"
    for area in import_list:
        results += 'Importing %s.txt... ' % area
        area_obj = self.world.get_area(area)
        if area_obj:
            results += 'Aborted: area %s already exists.\n' % area_obj.name
        else:
            try:
                status = self.import_from_shiny(area)
            except ShinyImportError as e:
                results += 'Failed: ' + str(e) + '\n'
            else:
                results += status + '\n'
    if not results:
        return 'No pre-packaged areas were found.\n'
    return results

def list_importable_areas(import_dir=AREAS_IMPORT_DIR):
    if not os.path.exists(import_dir):
        return 'There are no area files in your import directory.'
    # Give the player a list of names of all the area files in their import directory
    # and trim off the .txt extension for readibility. Ignore all files that aren't txt
    # files
    alist = [area.replace('.txt', '') for area in os.listdir(import_dir) if area.endswith('.txt')]
    if alist:
        string = ' Available For Import '.center(50, '-')
        string += '\n' + '\n'.join(alist) + '\n' + ('-' * 50)
        return string
    else:
        return 'There are no area files in your import directory.'

def get_formatter(format_file):
    # get a list of the files in the formatters folder.
    if (format_file + '.py') in os.listdir(os.path.join(path, 'sport_plugins/formatters')):
        # import the formatter from that file and return it
        format = __import__('shinymud.lib.sport_plugins.formatters.%s.format' % format_file, globals(), locals(), [], -1)
    raise SportError('Cannot find formatter: %s' % format_file)

def get_transport(t_file):
    # get a list of the files in the transports folder.
    if t_file in os.listdir(os.path.join(path, 'sport_plugins/transports')):
        # import the transport from that file and return it
        trasport = __import__('shinymud.lib.sport_plugins.formatters.%s.transport' % t_file, globals(), locals(), [], -1)
    raise SportError('Cannot find transport: %s' % t_file)

