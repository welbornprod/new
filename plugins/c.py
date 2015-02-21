""" C plugin for New.
    Creates a new C file, and basic Makefile to go with it.
    -Christopher Welborn 2-20-15
"""
import os.path
from plugins import Plugin, date
DATE = date()

template = """/*  {filename}
    ...
    {author} {date}
*/

#include <stdio.h>

int main(int argc, char *argv[]) {{

    return 0;
}}
"""


class CPlugin(Plugin):

    def __init__(self):
        self.name = ('c',)
        self.extensions = ('.c',)
        self.version = '0.0.1'
        self.ignore_post = ('chmodx',)
        self.description = '\n'.join((
            'Creates a basic C file for small programs.',
            'If no Makefile exists, it will be created with basic targets.'
        ))
        self.load_config()

    def create(self, filename, args):
        """ Creates a basic C file.
        """
        parentdir, basename = os.path.split(filename)
        author = self.config.get('author', '')
        if author:
            author = '-{}'.format(author)
        return template.format(filename=basename, author=author, date=DATE)


plugins = (CPlugin(),)
