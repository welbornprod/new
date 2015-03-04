""" Node/JS plugin for New
    -Christopher Welborn
"""

import os.path
from plugins import Plugin, date, debug
DATE = date()

TEMPLATE = """#!/usr/bin/env node

/* {name}
   ...
   {author}{date}
*/

var XXX = function () {{

}}
"""


class JSPlugin(Plugin):

    """ Creates a blank node/js file. """

    def __init__(self):
        self.name = ('js', 'node', 'nodejs')
        self.extensions = ('.js',)
        self.version = '0.0.2'
        self.load_config()

    def create(self, fname, args):
        """ Creates a blank js/node file. """
        # Using the node shebang, even though this may not be for node.
        author = self.config.get('author', '')
        if author:
            author = '- {}'.format(author)
        datestr = ' {}'.format(DATE) if author else DATE
        name = os.path.splitext(os.path.split(fname)[-1])[0]
        debug('Retrieved config..')
        return TEMPLATE.format(
            name=name,
            author=author,
            date=datestr)

plugins = (JSPlugin(),)
