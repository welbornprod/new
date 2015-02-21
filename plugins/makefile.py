""" Makefile plugin for New
    Creates a makefile when the C plugin is used.
    -Christopher Welborn 2-20-15
"""

import os.path
from plugins import PostPlugin, debug

template = """CC=gcc
CFLAGS=-std=c11 -Wall
binaries={binary}

{binary}: {filename}
\t$(CC) -o {binary} $(CFLAGS) {filename}

clean:
\trm -f $(binaries) *.o
"""


class MakefilePost(PostPlugin):

    def __init__(self):
        self.name = 'automakefile'
        self.version = '0.0.1'
        self.description = '\n'.join((
            'Creates a makefile for new C files.',
            'This will not overwrite existing makefiles.'
        ))

    def process(self, filename):
        """ When a C file is created, create a basic Makefile to go with it.
        """
        parentdir, basename = os.path.split(filename)
        fileext = os.path.splitext(basename)[-1]
        if fileext != '.c':
            return None
        self.create_makefile(parentdir, basename)

    def create_makefile(self, parentdir, filename):
        """ Create a basic Makefile with the C file as it's target. """
        trynames = 'Makefile', 'makefile'
        for makefilename in trynames:
            fullpath = os.path.join(parentdir, makefilename)
            if os.path.exists(fullpath):
                debug('Makefile already exists: {}'.format(fullpath))
                return None

        debug('Creating a makefile for: {}'.format(filename))
        makefile = os.path.join(parentdir, 'Makefile')
        binary = os.path.splitext(filename)[0]
        content = template.format(binary=binary, filename=filename)

        with open(makefile, 'w') as f:
            f.write(content)
        print('Makefile created: {}'.format(makefile))
        return makefile

plugins = (MakefilePost(),)
