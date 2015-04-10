""" ChmodX plugin for New.
    Makes new files executable.
    Any plugin can block this from happening by adding:
        def __init__(self):
            self.ignore_post('chmodx',)

    -Christopher Welborn 01-01-2015
"""
import os
import stat

from plugins import PostPlugin, SignalExit


class ChmodxPlugin(PostPlugin):

    def __init__(self):
        self.name = 'chmodx'
        self.version = '0.0.1-1'

    def process(self, plugin, fname):
        """ Makes the newly created file executable. """
        chmod774 = stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH
        try:
            os.chmod(fname, chmod774)
        except FileNotFoundError:
            # The file was never created, all other plugins will fail.
            raise SignalExit('No file was created: {}'.format(fname))
        except EnvironmentError as ex:
            self.debug('Error during chmod: {}\n{}'.format(fname, ex))
        else:
            self.print_status('Made executable (chmod 774)')

exports = (ChmodxPlugin(),)
