""" Text plugin for New.
    -Christopher Welborn 1-31-15
"""

from plugins import Plugin

__version__ = '0.0.2'


class TextPlugin(Plugin):

    """ Creates a blank text file (no content). """

    def __init__(self):
        self.name = ('text', 'txt', 'blank')
        self.extensions = ('.txt', '.md', '.markdown', '.rst')
        self.version = __version__
        self.allow_blank = True
        # Allow a custom extension (still .txt if no extension is provided)
        self.any_extension = True
        # Text files are not executable.
        self.ignore_post = {'chmodx'}

    def create(self, filename):
        """ Creates a blank text file (no content). """
        return None

exports = (TextPlugin(), )
