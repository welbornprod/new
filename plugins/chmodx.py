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

    name = 'chmodx'
    version = '0.0.2'

    docopt = True
    usage = """
    Usage:
        chmodx FILENAME

    Options:
        FILENAME  : File name to make executable.
    """

    mode = stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH
    modestr = '774'

    def chmod(self, filename, mode=None):
        try:
            os.chmod(filename, self.mode if mode is None else mode)
        except FileNotFoundError:
            # The file was never created, all other plugins will fail.
            raise SignalExit('No file was created: {}'.format(filename))
        except EnvironmentError as ex:
            self.debug('Error during chmod: {}\n{}'.format(filename, ex))

    def process(self, plugin, filename):
        """ Makes the newly created file executable. """

        self.chmod(filename)
        self.print_status('Made executable (chmod {})'.format(self.modestr))

    def run(self):
        """ Make a file executable from the command line. """

        self.chmod(self.argd['FILENAME'], mode=self.mode)
        self.print_status(
            'chmod {} {}'.format(self.modestr, self.argd['FILENAME'])
        )

exports = (ChmodxPlugin,)
