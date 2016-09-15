from shinymud.lib.sport_plugins import SportError

import os

def transport(world, shinydata, filename, path):
    """Write shinydata to a file under the given file_name.
    """
    if not os.path.exists(path):
        try:
            os.mkdir(path)
        except Exception as e:
            world.log.error('EXPORT FAILED: ' + str(e))
            raise SportError('Error accessing the export directory for areas.')
    filepath = os.path.join(path, filename)
    try:
        f = open(filepath, 'w')
    except IOError as e:
        world.log.debug(str(e))
        raise SportError('Error writing to file. Check the logfile for details')
    else:
        f.write(shinydata)
    finally:
        f.close()
    return 'Export complete! Your file can be found at:\n%s' % filepath
