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

# I'm not very good with makefiles. The .replace() is just for my sanity.
template = """SHELL=bash
{compilervar}={compiler}
{cflagsvar}=-std={std} -Wall
binary={binary}
source={filename}

all: {objects}
    $({compilervar}) -o $(binary) $({cflagsvar}) *.o

{objects}: $(source)
    $({compilervar}) -c $(source) $({cflagsvar})

.PHONY: clean
clean:
    -@if [[ -e $(binary) ]]; then\\
        if rm -f $(binary); then\\
            echo "Binaries cleaned.";\\
        fi;\\
    else\\
        echo "Binaries already clean.";\\
    fi;

    -@if ls *.o &>/dev/null; then\\
        if rm *.o; then\\
            echo "Objects cleaned.";\\
        fi;\\
    else\\
        echo "Objects already clean.";\\
    fi;
""".replace('    ', '\t')

# Template options based on compiler name.
coptions = {
    'gcc': {
        'compilervar': 'CC',
        'cflagsvar': 'CFLAGS',
        'std': 'c11'
    },
    'g++': {
        'compilervar': 'CXX',
        'cflagsvar': 'CXXFLAGS',
        'std': 'c++11'
    }
}


def template_render(filepath, makefile=None):
    """ Render the makefile template for a given c source file name. """
    parentdir, filename = os.path.split(filepath)
    fileext = os.path.splitext(filename)[-1]
    makefile = os.path.join(
        parentdir,
        makefile if makefile else 'makefile')
    binary = os.path.splitext(filename)[0]
    objects = '{}.o'.format(binary)

    # Get compiler and make options by file extension (default to gcc).
    compiler = {'.c': 'gcc', '.cpp': 'g++'}.get(fileext, 'gcc')
    # Create template args, update with compiler-based options.
    templateargs = {
        'compiler': compiler,
        'binary': binary,
        'filename': filename,
        'objects': objects
    }
    templateargs.update(coptions[compiler])

    return makefile, template.format(**templateargs)


class MakefilePost(PostPlugin):

    def __init__(self):
        self.name = 'automakefile'
        self.version = '0.0.2'
        self.description = '\n'.join((
            'Creates a makefile for new C files.',
            'This will not overwrite existing makefiles.'
        ))

    def process(self, filename):
        """ When a C file is created, create a basic Makefile to go with it.
        """
        fileext = os.path.splitext(filename)[-1]
        if fileext not in ('.c', '.cpp'):
            return None
        self.create_makefile(filename)

    def create_makefile(self, filepath):
        """ Create a basic Makefile with the C file as it's target. """
        parentdir, filename = os.path.split(filepath)
        trynames = 'Makefile', 'makefile'
        for makefilename in trynames:
            fullpath = os.path.join(parentdir, makefilename)
            if os.path.exists(fullpath):
                debug('Makefile already exists: {}'.format(fullpath))
                return None
        debug('Creating a makefile for: {}'.format(filename))
        config = MakefilePlugin().config
        makefile, content = template_render(
            filepath,
            makefile=config.get('default_filename', 'makefile'))

        with open(makefile, 'w') as f:
            f.write(content)
        print('Makefile created: {}'.format(makefile))
        return makefile


class MakefilePlugin(Plugin):

    """ Creates a basic Makefile for a given c file name. """

    def __init__(self):
        self.name = ('makefile', 'make')
        self.extensions = tuple()
        self.version = '0.0.2'
        self.ignore_post = ('chmodx',)
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

        defaultfile = (args[0] if args else self.config.get(
            'default_filename',
            'makefile'))

        makefile, content = template_render(
            filename,
            makefile=defaultfile)

        _, basename = os.path.split(filename)
        msg = '\n'.join((
            'Creating a makefile for: {}'.format(basename),
            '              File path: {}'.format(makefile)
        ))
        raise SignalAction(
            message=msg,
            filename=makefile,
            content=content)

plugins = (MakefilePost(), MakefilePlugin())
