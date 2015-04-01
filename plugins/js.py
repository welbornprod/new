""" Node/JS plugin for New
    -Christopher Welborn
"""

import os.path
from plugins import Plugin, date
DATE = date()

TEMPLATE = """#!/usr/bin/env node

/* {name}
   ...
   {author}{date}
*/

'use strict';
var docopt = require('docopt');
var sys = require('sys');

var name = '{name}';
var version = '0.0.1';
var version_str = [name, version].join(' v. ');

var usage_str = [
    version_str,
    '',
    'Usage:',
    '    {scriptname} [-h | -v]',
    '',
    'Options:',
    '    -h,--help     : Show this message.',
    '    -v,--version  : Print version and exit.'
].join('\\n');

var args = docopt.docopt(usage_str, {{'version': version_str}});

sys.puts('Hello.');
"""


class JSPlugin(Plugin):

    """ Creates a blank node/js file. """

    def __init__(self):
        self.name = ('js', 'node', 'nodejs')
        self.extensions = ('.js',)
        self.version = '0.0.3'
        self.load_config()

    def create(self, fname):
        """ Creates a blank js/node file. """
        # Using the node shebang, even though this may not be for node.
        author = self.config.get('author', '')
        if author:
            author = '- {}'.format(author)
        datestr = ' {}'.format(DATE) if author else DATE
        scriptname = os.path.split(fname)[-1]
        name = os.path.splitext(scriptname)[0]

        self.debug('Retrieved config..')
        return TEMPLATE.format(
            name=name,
            author=author,
            date=datestr,
            scriptname=scriptname)

exports = (JSPlugin(),)
