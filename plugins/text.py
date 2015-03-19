""" Text plugin for New.
    -Christopher Welborn 1-31-15
"""

from plugins import Plugin


class TextPlugin(Plugin):

    """ Creates a blank text file (no content). """

    def __init__(self):
        self.name = ('text', 'txt', 'blank')
        self.extensions = ('.txt',)
        self.version = '0.0.1'
        self.allow_blank = True
        # Text files are not executable.
        self.ignore_post = {'chmodx'}

    def create(self, filename, args):
        """ Creates a blank text file (no content). """
        return None

exports = (TextPlugin(), )
