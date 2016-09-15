from shinymud.lib.sport_plugins import SportError
from shinymud.data.config import AREAS_IMPORT_DIR

import os
import re

def get_list(source_path):
    """Get a list of objects that are available for import via the file
    transport.
    
    source_path - the directory this transport should look to find importable
        files
    """
    # Match the form of name_type.format
    source_path = AREAS_IMPORT_DIR
    exp = re.compile(r"[^_]+_[^\.]+\.\w+")
    
    return [x for x in os.listdir(source_path) if exp.match(x)]

def transport(world, filename, path):
    """Retrieve the area data from the file specified by filename.
    Raise an ShinyImportError if the file doesn't exist or opening the file
    fails.
    filename - the name of the file the area data should be read from
    path - the directory in which this transport should look for filename
    world - The world instance this transport can use for logging
    """
    filepath = os.path.join(path, filename)
    if not os.path.exists(filepath):
        world.log.debug('Error: could not find ' + filepath)
        raise SportError('Error: file %s does not exist.' % filename)
    try:
        f = open(filepath, 'r')
    except IOError as e:
        world.log.debug(str(e))
        raise SportError('Error: opening the area file failed. '
                         'Check the logfile for details.')
    else:
        shinydata = f.read()
    finally: 
        f.close()
        
    return shinydata