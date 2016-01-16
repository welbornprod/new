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

    def create(self, filename):
        """ Creates a blank text file (no content). """
        return None

exports = (TextPlugin, )
