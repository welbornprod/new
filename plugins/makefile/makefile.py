""" Makefile plugin for New
    Creates a makefile when the C plugin is used.
    -Christopher Welborn 2-20-15
"""

import os.path

from .. import (
    confirm,
    Plugin,
    PostPlugin,
    SignalAction,
    SignalExit
)

from . import templates

# Version number for both plugins (if one changes, usually the other changes)
VERSION = '0.4.2'


class MakefilePost(PostPlugin):
    name = 'automakefile'
    version = VERSION
    description = '\n'.join((
        'Creates a makefile for new NASM, C, CPP, or Rust files.',
        'This will not overwrite existing makefiles.'
    ))

    def process(self, plugin, filepath):
        """ When a C file is created, create a basic Makefile to go with it.
        """
        if plugin.get_name() not in ('asm', 'c', 'rust'):
            return None
        self.create_makefile(filepath, plugin)

    def create_makefile(self, filepath, plugin):
        """ Create a basic Makefile with the C file as it's target. """
        parentdir, filename = os.path.split(filepath)
        trynames = 'Makefile', 'makefile'
        for makefilename in trynames:
            fullpath = os.path.join(parentdir, makefilename)
            if os.path.exists(fullpath):
                self.debug('Makefile already exists: {}'.format(fullpath))
                return None
        # Pass plugin args to template_render if given.
        self.argd.update(getattr(plugin, 'argd', {}))
        pluginname = plugin.get_name()
        if self.argd.get('--clib', False):
            pluginname = '{}-c'.format(pluginname)
        self.debug('Creating a makefile ({} style) for: {}'.format(
            pluginname,
            filename,
        ))
        # Use default MakeFilePlugin config.
        config = MakefilePlugin().config
        # Render makefile templates based on file name and user args.
        makefile, content = templates.template_render(
            filepath,
            makefile=config.get(
                'default_filename',
                templates.DEFAULT_MAKEFILE
            ),
            argd=self.argd,
            config=config,
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
    description = 'Creates a makefile for a given c, cpp, nasm, or rust file.'

    docopt = True
    usage = """
    Usage:
        makefile [-c | -l] [MAKEFILENAME]

    Options:
        MAKEFILENAME  : Desired file name for the makefile.
                        Can also be set in config as 'default_filename'.
        -c,--cargo    : Use Cargo style for Rust files.
        -l,--clib     : Use C library style for ASM files.
    """

    def __init__(self):
        self.load_config()

    def create(self, filepath):
        """ Creates a basic Makefile for a given c file name. """
        if not (self.dryrun or os.path.exists(filepath)):
            msg = '\n'.join((
                'The target source file doesn\'t exist: {}',
                'Continue anyway?'
            )).format(filepath)
            if not confirm(msg):
                raise SignalExit('User cancelled.')

        defaultfile = (
            self.argd['MAKEFILENAME'] or
            self.config.get(
                'default_filename',
                templates.DEFAULT_MAKEFILE
            )
        )

        makefile, content = templates.template_render(
            filepath,
            makefile=defaultfile,
            argd=self.argd,
            config=self.config,
        )

        _, basename = os.path.split(filepath)
        msg = '\n'.join((
            'Creating a makefile for: {}'.format(basename),
            'Output file path: {}'.format(makefile)
        ))
        raise SignalAction(
            message=msg,
            filename=makefile,
            content=content,
        )


exports = (MakefilePost, MakefilePlugin)
