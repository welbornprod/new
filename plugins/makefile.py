""" Makefile plugin for New
    Creates a makefile when the C plugin is used.
    -Christopher Welborn 2-20-15
"""

import os.path
from plugins import (
    confirm,
    debug,
    Plugin,
    PostPlugin,
    SignalAction,
    SignalExit
)

# I'm not very good with makefiles. I hate all the errors it spits out for
# `make clean`, hince all the conditionals.
template = """SHELL=bash
CC=gcc
CFLAGS=-std=c11 -Wall
binaries={binary}

{binary}: {filename}
\t$(CC) -o {binary} $(CFLAGS) {filename}

clean:
    -@if [[ -e $(binaries) ]]; then\\
        if rm -f $(binaries); then\\
            echo "Binaries cleaned.";\\
        fi;\\
    else\\
        echo "Binaries already clean.";\\
    fi\\

    -@if [[ -e *.o ]]; then\\
        if rm *.o; then\\
            echo "Objects cleaned.";\\
        fi;\\
    else\\
        echo "Objects already clean.";\\
    fi\\
""".replace('    ', '\t')


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


class MakefilePlugin(Plugin):

    """ Creates a basic Makefile for a given c file name. """

    def __init__(self):
        self.name = ('makefile', 'make')
        self.extensions = tuple()
        self.version = '0.0.1'
        self.description = '\n'.join((
            'Creates a basic makefile for a given c file name.'
            'The file created is always called "Makefile".'
        ))
        self.usage = """
    Usage:
        makefile [makefile_filename]

    Options:
        makefile_filename  : Desired file name for the makefile.
                             Can also be set in config as 'default_filename'.
    """
        self.load_config()

    def create(self, filename, args):
        """ Creates a basic Makefile for a given c file name. """
        if not os.path.exists(filename):
            msg = '\n'.join((
                'The target source file doesn\'t exist: {}',
                'Continue anyway?'
            )).format(filename)
            if not confirm(msg):
                raise SignalExit('User cancelled.')

        parentdir, basename = os.path.split(filename)
        binary = os.path.splitext(basename)[0]
        makefile = os.path.join(
            parentdir,
            args[0] if args else self.config.get(
                'default_filename',
                'makefile')
        )
        msg = '\n'.join((
            'Creating a makefile for: {}'.format(basename),
            '              File path: {}'.format(makefile)
        ))
        raise SignalAction(
            message=msg,
            filename=makefile,
            content=template.format(binary=binary, filename=basename))

plugins = (MakefilePost(), MakefilePlugin())
