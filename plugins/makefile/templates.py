#!/usr/bin/env python3
""" Templates for the New plugin, `makefile`.
    -Christopher Welborn 11-19-17
"""

import os

from .. import (
    date,
    debug,
    fix_author,
    SignalExit,
)

# Default file name for a makefile.
DEFAULT_MAKEFILE = 'makefile'

templates_dir = os.path.split(__file__)[0]
template_files = {
    '.asm': os.path.join(templates_dir, 'asm.makefile'),
    '.asmc': os.path.join(templates_dir, 'asmc.makefile'),
    '.c': os.path.join(templates_dir, 'c.makefile'),
    '.cpp': os.path.join(templates_dir, 'cpp.makefile'),
}


def template_load(filepath, argd=None):
    """ Load content from one of the templates, based on the target file
        name and user args.
    """
    fileext = os.path.splitext(filepath)[-1].lower()
    if argd.get('--clib', False):
        fileext = '.asmc'
    template_file = template_files.get(
        fileext,
        template_files['.c'],
    )
    try:
        with open(template_file, 'r') as f:
            content = f.read()
    except FileNotFoundError as exnofile:
        raise SignalExit('Template file not found: {x.filename}'.format(
            x=exnofile,
        ))
    except EnvironmentError as ex:
        raise SignalExit('Error reading from template file: {}'.format(ex))
    debug('Using {} template for makefile: {}'.format(fileext, template_file))
    return content


def template_render(filepath, makefile=None, argd=None, config=None):
    """ Render the makefile template for a given c source file name. """
    parentdir, filename = os.path.split(filepath)
    makefile = os.path.join(parentdir, makefile or DEFAULT_MAKEFILE)
    binary = os.path.splitext(filename)[0]
    author = fix_author((config or {}).get('author', ''))

    templateargs = {
        'author': author,
        'binary': binary,
        'date': ' {}'.format(date()) if author else date(),
        'source': filename,
    }
    template = template_load(filepath, argd={} if (argd is None) else argd)

    # Format the template with compiler-specific settings.
    debug('Rendering makefile: {}'.format(makefile))
    return makefile, template.format(**templateargs)
