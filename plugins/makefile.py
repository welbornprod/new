""" Makefile plugin for New
    Creates a makefile when the C plugin is used.
    -Christopher Welborn 2-20-15
"""

import os.path
import re
from plugins import (
    confirm,
    debug,
    Plugin,
    PostPlugin,
    SignalAction,
    SignalExit
)

# Version number for both plugins (if one changes, usually the other changes)
VERSION = '0.1.0'

# Default filename for the resulting makefile.
DEFAULT_MAKEFILE = 'makefile'


def fix_indent(s):
    """ Replace leading spaces with tabs. """
    final = []
    for line in s.split('\n'):
        cnt = 0
        while line.startswith('    '):
            cnt += 1
            line = line[4:]
        final.append(''.join(('\t' * cnt, line)))
    return '\n'.join(final)

# I'm not very good with makefiles.
# {targets} and {cleantarget} are set by compiler type,
# and *then* the whole template is rendered.
pre_template = """SHELL=bash
{{compilervar}}={{compiler}}
{{cflagsvar}}={{cflags}}
binary={{binary}}
source={{filename}}

{targets}

.PHONY: clean, targets
clean:
{cleantarget}

targets:
    -@echo -e "Make targets available:\\n\\
    all     : Build the executable with no optimization or debug symbols.\\n\\
    clean   : Delete previous build files.\\n\\
    debug   : Build the executable with debug symbols.\\n\\
    release : Build the executable with optimizations.\\n\\
    ";
"""
# This is just for my sanity when dealing with tabs vs. spaces.
pre_template = fix_indent(pre_template)

# Make targets for c/c++.
ctargets = """
all: {objects}
    $({compilervar}) -o $(binary) $({cflagsvar}) *.o

debug: {cflagsvar}+=-g3
debug: all

release: {cflagsvar}+=-O3
release: all

{objects}: $(source)
    $({compilervar}) -c $(source) $({cflagsvar})
""".replace('    ', '\t').strip()

# Clean target for C/C++.
ccleantarget = """
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
""".replace('    ', '\t').lstrip('\n')

# Make targets for rustc (until I find a better way)
rusttargets = """
all: $(source)
    $({compilervar}) $({cflagsvar}) -o $(binary) $(source)

debug: {cflagsvar}+=-g
debug: all

release: {cflagsvar}+=-O
release: all
""".replace('    ', '\t').strip()

# Clean target for Rust/Cargo.
rustcleantarget = """
    -@if [[ -e $(binary) ]]; then\\
        if rm -f $(binary); then\\
            echo "Binaries cleaned.";\\
        fi;\\
    else\\
        echo "Binaries already clean.";\\
    fi;
""".replace('    ', '\t').lstrip('\n')

# Template options based on compiler name.
coptions = {
    'gcc': {
        'compilervar': 'CC',
        'cflagsvar': 'CFLAGS',
        'cflags': '-std=c11 -Wall -Wextra',
        'targets': ctargets,
        'cleantarget': ccleantarget,
    },
    'g++': {
        'compilervar': 'CXX',
        'cflagsvar': 'CXXFLAGS',
        'cflags': '-std=c++11 -Wall -Wextra',
        'targets': ctargets,
        'cleantarget': ccleantarget,
    },
    'rustc': {
        'compilervar': 'RUSTC',
        'cflagsvar': 'RUSTFLAGS',
        'cflags': '',
        'targets': rusttargets,
        'cleantarget': rustcleantarget,
    }
}


def template_render(filepath, makefile=None):
    """ Render the makefile template for a given c source file name. """
    parentdir, filename = os.path.split(filepath)
    fileext = os.path.splitext(filename)[-1]
    makefile = os.path.join(parentdir, makefile or DEFAULT_MAKEFILE)
    binary = os.path.splitext(filename)[0]
    objects = '{}.o'.format(binary)

    # Get compiler and make options by file extension (default to gcc).
    compiler = {
        '.c': 'gcc',
        '.cpp': 'g++',
        '.rs': 'rustc'
    }.get(fileext, 'gcc')

    # Create the base template, retrieve compiler-specific settings.
    debug('Rendering makefile template for {}.'.format(compiler))
    compileropts = coptions[compiler]
    template = pre_template.format(
        targets=compileropts.pop('targets'),
        cleantarget=compileropts.pop('cleantarget')
    )

    # Create template args, update with compiler-based options.
    templateargs = {
        'compiler': compiler,
        'binary': binary,
        'filename': filename,
        'objects': objects
    }
    templateargs.update(coptions[compiler])

    # Format the template with compiler-specific settings.
    return makefile, template.format(**templateargs)


class MakefilePost(PostPlugin):
    name = 'automakefile'
    version = VERSION
    description = '\n'.join((
        'Creates a makefile for new C files.',
        'This will not overwrite existing makefiles.'
    ))

    def process(self, plugin, filename):
        """ When a C file is created, create a basic Makefile to go with it.
        """
        if plugin.get_name() not in ('c', 'rust'):
            return None
        self.create_makefile(filename)

    def create_makefile(self, filepath):
        """ Create a basic Makefile with the C file as it's target. """
        parentdir, filename = os.path.split(filepath)
        trynames = 'Makefile', 'makefile'
        for makefilename in trynames:
            fullpath = os.path.join(parentdir, makefilename)
            if os.path.exists(fullpath):
                self.debug('Makefile already exists: {}'.format(fullpath))
                return None
        self.debug('Creating a makefile for: {}'.format(filename))
        config = MakefilePlugin().config
        makefile, content = template_render(
            filepath,
            makefile=config.get('default_filename', DEFAULT_MAKEFILE))

        with open(makefile, 'w') as f:
            f.write(content)
        print('Makefile created: {}'.format(makefile))
        return makefile


class MakefilePlugin(Plugin):

    """ Creates a basic Makefile for a given c file name. """

    name = ('makefile', 'make')
    extensions = tuple()
    version = VERSION
    ignore_post = {'chmodx'}
    description = 'Creates a basic makefile for a given c or rust file name.'

    docopt = True
    usage = """
    Usage:
        makefile [MAKEFILENAME]

    Options:
        MAKEFILENAME  : Desired file name for the makefile.
                        Can also be set in config as 'default_filename'.
    """

    def __init__(self):
        self.load_config()

    def create(self, filename):
        """ Creates a basic Makefile for a given c file name. """
        if not (self.dryrun or os.path.exists(filename)):
            msg = '\n'.join((
                'The target source file doesn\'t exist: {}',
                'Continue anyway?'
            )).format(filename)
            if not confirm(msg):
                raise SignalExit('User cancelled.')

        defaultfile = (
            self.argd['MAKEFILENAME'] or
            self.config.get('default_filename', DEFAULT_MAKEFILE)
        )

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

exports = (MakefilePost, MakefilePlugin)
