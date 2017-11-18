""" Makefile plugin for New
    Creates a makefile when the C plugin is used.
    -Christopher Welborn 2-20-15
"""

import os.path

from .. import (
    confirm,
    debug,
    Plugin,
    PostPlugin,
    SignalAction,
    SignalExit
)

from . import templates

# Version number for both plugins (if one changes, usually the other changes)
VERSION = '0.4.0'

# Default filename for the resulting makefile.
DEFAULT_MAKEFILE = 'makefile'


def template_render(filepath, makefile=None, argd=None):
    """ Render the makefile template for a given c source file name. """
    argd = {} if (argd is None) else argd
    parentdir, filename = os.path.split(filepath)
    fileext = os.path.splitext(filename)[-1]
    makefile = os.path.join(parentdir, makefile or DEFAULT_MAKEFILE)
    binary = os.path.splitext(filename)[0]
    objects = '{}.o'.format(binary)

    # Get compiler and make options by file extension (default to gcc).
    compiler = {
        '.asm': 'nasm',
        '.asmc': 'nasm-c',
        '.c': 'gcc',
        '.cpp': 'g++',
        '.rs': 'rustc',
        '.s': 'nasm',
    }.get('.asmc' if argd['--clib'] else fileext, 'gcc')

    # Create the base template, retrieve compiler-specific settings.
    debug('Rendering makefile template for {}.'.format(compiler))
    compileropts = templates.coptions[compiler]
    template = templates.pre_template.format(
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
    templateargs.update(templates.coptions[compiler])

    # Format the template with compiler-specific settings.
    return makefile, template.format(**templateargs)


class MakefilePost(PostPlugin):
    name = 'automakefile'
    version = VERSION
    description = '\n'.join((
        'Creates a makefile for new NASM, C, CPP, or Rust files.',
        'This will not overwrite existing makefiles.'
    ))

    def process(self, plugin, filename):
        """ When a C file is created, create a basic Makefile to go with it.
        """
        if plugin.get_name() not in ('asm', 'c', 'rust'):
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
            makefile=config.get('default_filename', DEFAULT_MAKEFILE),
            argd=self.argd,
        )

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
    description = 'Creates a makefile for a given c, cpp, or rust file.'

    docopt = True
    usage = """
    Usage:
        makefile [MAKEFILENAME] [-l]

    Options:
        MAKEFILENAME  : Desired file name for the makefile.
                        Can also be set in config as 'default_filename'.
        -l,--clib     : Use C library style for ASM files.
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
            makefile=defaultfile,
            argd=self.argd,
        )

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
