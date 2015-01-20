""" Rust plugin for New
    -Christopher Welborn 1-19-15
"""

from plugins import Plugin

# Not much in this plugin at the moment.


class RustPlugin(Plugin):

    """ Creates a blank Rust file. """

    def __init__(self):
        self.name = ('rust', 'rs')
        self.extensions = ('.rs',)
        # Rust doesnt need to be made executable.
        self.ignore_post = ('chmodx',)
        self.version = '1.0.0'

    def create(self, fname, args):
        """ Creates a blank Rust file. """
        return """use std::io;

fn main() {

}
"""


plugins = (RustPlugin(),)
