""" Open post-processing plugin for New.
    Opens files after they are created.
    -Christopher Welborn 12-25-14
"""

from plugins import PostPlugin


class OpenPlugin(PostPlugin):

    def __init__(self):
        self.name = 'open'

    def process(self, path):
        """ Opens the file after creation. """
        print('OPEN NOT IMPLEMENTED: {}'.format(path))

plugins = (OpenPlugin(),)
