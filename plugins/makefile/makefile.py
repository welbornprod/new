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
VERSION = '0.5.1'


class MakefilePost(PostPlugin):
    name = 'automakefile'
    version = VERSION
    description = '\n'.join((
        'Creates a makefile for new C, CPP, NASM/YASM, or Rust files.',
        'This will not overwrite existing makefiles.'
    ))
    multifile = True

    def is_valid_plugin(self, plugin):
        return plugin.get_name() in ('asm', 'c', 'rust')

    def process(self, plugin, filepath):
        """ When a file is created, create a basic Makefile to go with it.
        """
        return self.process_multi(plugin, [filepath])

    def process_multi(self, plugin, filepaths):
        """ When a file is created, create a basic Makefile to go with it,
            with included source files.
        """
        if not self.is_valid_plugin(plugin):
            return None
        self.create_makefile(filepaths, plugin)

    def create_makefile(self, filepaths, plugin):
        """ Create a basic Makefile with the file as it's target. """
        filepath = filepaths[0]
        parentdir, filename = os.path.split(filepath)
        trynames = 'Makefile', 'makefile', 'MakeFile'
        for makefilename in trynames:
            fullpath = os.path.join(parentdir, makefilename)
            if os.path.exists(fullpath):
                self.debug('Makefile already exists: {}'.format(fullpath))
                return None
        # Pass plugin args to template_render if given.
        self.argd.update(getattr(plugin, 'argd', {}))
        # Use args forwarded from plugin.
        pluginargd = self.plugin_argd(plugin)
        self.debug_json(pluginargd, msg='Plugin-forwarded argd:')
        self.argd.update({
            k: v
            for k, v in pluginargd.items()
            if v
        })
        self.debug_json(self.argd, msg='Using argd:')
        pluginname = plugin.get_name()
        if self.argd.get('--clib', False):
            pluginname = '{}-c'.format(pluginname)
        if self.argd.get('--nasm', False):
            pluginname = 'n{}'.format(pluginname)
        elif self.argd.get('--nyasm', False):
            pluginname = 'ny{}'.format(pluginname)
        else:
            pluginname = 'y{}'.format(pluginname)
        self.debug('Creating a makefile ({} style) for: {}'.format(
            pluginname,
            filename,
        ))
        multifile = len(filepaths) > 1
        if multifile:
            self.debug('With included files: {}'.format(
                ', '.join(filepaths[1:])
            ))

        # Use default MakeFilePlugin config.
        config = MakefilePlugin().config
        # Makefile name.
        makefilename = config.get(
            'default_filename',
            templates.DEFAULT_MAKEFILE
        )
        # Render makefile templates based on file name and user args.
        if multifile:
            makefile, content = templates.template_render_multi(
                filepaths,
                makefile=makefilename,
                argd=self.argd,
                config=config,
            )
        else:
            makefile, content = templates.template_render(
                filepath,
                makefile=makefilename,
                argd=self.argd,
                config=config,
            )

        with open(makefile, 'w') as f:
            f.write(content)
        self.print_status('Created {}'.format(makefile))
        return makefile


class MakefilePlugin(Plugin):

    """ Creates a basic Makefile for a given c file name. """

    name = ('makefile', 'make')
    extensions = tuple()
    version = VERSION
    ignore_post = {'chmodx'}
    multifile = True

    description = 'Creates a makefile for a given c, cpp, nasm, or rust file.'

    docopt = True
    usage = """
    Usage:
        makefile [-c | -l] [-n | -N] [MAKEFILENAME]

    Options:
        MAKEFILENAME  : Desired file name for the makefile.
                        Can also be set in config as 'default_filename'.
        -c,--cargo    : Use Cargo style for Rust files.
        -l,--clib     : Use C library style for ASM files.
        -n,--nasm     : Use nasm instead of yasm for ASM files.
        -N,--nyasm    : Use both nasm/yasm. Send nasm preprocessor output to
                        yasm for compilation. (nasm -E file | yasm)
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

    def create_multi(self, filepaths):
        """ Creates a basic Makefile for a given c file name.
            This will include all file paths as source files.
        """
        for filepath in filepaths:
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

        makefile, content = templates.template_render_multi(
            filepaths,
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

exports = (MakefilePost, MakefilePlugin)  # noqa
