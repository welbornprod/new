""" Text plugin for New.
    -Christopher Welborn 1-31-15
"""

from plugins import Plugin

__version__ = '0.0.2'


class TextPlugin(Plugin):

    """ Creates a blank text file (no content). """

    name = ('text', 'txt', 'blank')
    extensions = ('.txt', '.md', '.markdown', '.rst')
    version = __version__
    allow_blank = True
    # Allow a custom extension (still .txt if no extension is provided)
    any_extension = True
    # Text files are not executable.
    ignore_post = {'chmodx'}

    def config_dump(self):
        """ Overloaded config_dump() for special-case text plugin. """
        print('\nConfig for: {}\n'.format(self.get_name()))
        print('{}')
        print('\n'.join((
            '\nThe text plugin has no config settings.',
            'To create a custom text template use a CustomPlugin.',
            'For more information run with --customhelp.',
        )))
        return True

    def create(self, filename):
        """ Creates a blank text file (no content). """
        return None

    def help(self):
        """ Overloaded help() for special-case text plugin. """
        print('\nHelp for New plugin, {} v. {}:\n'.format(
            self.get_name(),
            self.version
        ))
        print('\n'.join((
            'The text plugin creates a blank file, and has no settings.',
            'To create custom text templates use a CustomPlugin.',
            'For more information run with --customhelp.',
        )))
        return True


exports = (TextPlugin, )
