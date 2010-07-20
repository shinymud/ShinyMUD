from shinymud.lib.sport_plugins import SportError

import os

def transport(world, filename, path):
    """Retrieve the area data from the file specified by filename.
    Raise an ShinyImportError if the file doesn't exist or opening the file
    fails.
    filename -- the name of the file the area data should be read from
    """
    filepath = os.path.join(path, filename)
    if not os.path.exists(filepath):
        raise SportError('Error: %s does not exist.' % filename)
        
    try:
        f = open(filepath, 'r')
    except IOError, e:
        world.log.debug(str(e))
        raise SportError('Error: opening the area file failed. '
                         'Check the logfile for details.')
    else:
        shinydata = f.read()
    finally: 
        f.close()
        
    return shinydata