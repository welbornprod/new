""" Node/JS plugin for New
    -Christopher Welborn
"""

import os.path
from plugins import Plugin, date, default_version

TEMPLATE = """#!/usr/bin/env node

/*  {name}
    ...
    {author}{date}
*/

'use strict';
var docopt = require('docopt');

var name = '{name}';
var version = '{version}';
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

console.log('Hello.');
"""


class JSPlugin(Plugin):

    """ Creates a blank node/js file. """

    def __init__(self):
        self.name = ('js', 'node', 'nodejs')
        self.extensions = ('.js',)
        self.version = '0.0.3-1'
        self.load_config()

    def create(self, fname):
        """ Creates a blank js/node file. """
        # Using the node shebang, even though this may not be for node.
        author = self.config.get('author', '')
        basename = os.path.split(fname)[-1]
        name = os.path.splitext(basename)[0]

        self.debug('Retrieved config..')
        return TEMPLATE.format(
            name=name,
            author='-{} '.format(author) if author else author,
            date=date(),
            scriptname=basename,
            version=self.config.get('default_version', default_version))

exports = (JSPlugin(),)
