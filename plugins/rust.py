""" Rust plugin for New
    -Christopher Welborn 1-19-15
"""

import os.path

from plugins import Plugin, date, fix_author

# Not much in this plugin at the moment.
# Cargo works really well. This is just for little "testruns" and additions.

template = """// {name}
// ...
// {author}{date}

{imports}
fn main() {{

}}
"""


class RustPlugin(Plugin):

    """ Creates a blank Rust file. """

    name = ('rust', 'rs')
    extensions = ('.rs',)
    version = '0.0.5'
    # Rust doesnt need to be made executable.
    ignore_post = {'chmodx'}
    config_opts = {'author': 'Default author name for all files.'}

    docopt = True
    usage = """
    Usage:
        rust [IMPORT...]

    Options:
        IMPORT  : One or many qualified import names. (like: std::io)
    """

    def __init__(self):
        self.load_config()

    def create(self, filename):
        """ Creates a blank Rust file. """
        return template.format(
            name=os.path.splitext(os.path.split(filename)[-1])[0],
            author=fix_author(self.config.get('author', None)),
            date=date(),
            imports=self.format_imports())

    def format_imports(self):
        """ Retrieve imports from self.argd and format them into a string. """
        # TODO: Imports still don't fully support external crates.
        # TODO: Add 'extern crate {}' lines where needed.
        if not self.argd['IMPORT']:
            return ''

        def fmtname(n):
            """ Convert a single name to a full import line. """
            # Allow ':' as a shortcut to '::'.
            n = n.replace(':', '::').replace('::::', '::')
            line = 'use {}'.format(n)
            if line.endswith(';'):
                return line
            return ''.join((line, ';'))

        lines = '\n'.join(sorted(fmtname(i) for i in self.argd['IMPORT']))
        return '{}\n'.format(lines)


exports = (RustPlugin,)
