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
    'c': os.path.join(templates_dir, 'c.makefile'),
    'cpp': os.path.join(templates_dir, 'cpp.makefile'),
    'nasm': os.path.join(templates_dir, 'nasm.makefile'),
    'nasmc': os.path.join(templates_dir, 'nasmc.makefile'),
    'nyasm': os.path.join(templates_dir, 'nyasm.makefile'),
    'nyasmc': os.path.join(templates_dir, 'nyasmc.makefile'),
    'rust': os.path.join(templates_dir, 'rust.makefile'),
    'rust-cargo': os.path.join(templates_dir, 'rust-cargo.makefile'),
    'yasm': os.path.join(templates_dir, 'yasm.makefile'),
    'yasmc': os.path.join(templates_dir, 'yasmc.makefile'),
}


def choose_template(filepath, argd):
    """ Decide which template file to use based on the filepath and argd
        options.
        Returns (lang_name, template_file)
    """
    fileext = os.path.splitext(filepath)[-1].lower()
    argd = argd or {}
    asmlang = 'yasm'
    if argd.get('--nasm', False):
        asmlang = 'nasm'
    elif argd.get('--nyasm'):
        asmlang = 'nyasm'
    asmlangc = '{}c'.format(asmlang)
    try:
        lang = {
            '.asm': asmlang,
            '.asmc': asmlangc,
            '.c': 'c',
            '.cc': 'cpp',
            '.cpp': 'cpp',
            '.rs': 'rust-cargo' if argd.get('--cargo', False) else 'rust',
            '.s': asmlang,
        }[fileext]
    except KeyError:
        raise SignalExit('Unknown makefile type: {}'.format(fileext))

    if argd.get('--clib', False):
        if lang in ('nasm', 'yasm', 'nyasm'):
            lang = '{}c'.format(lang)
        elif lang not in ('nasmc', 'yasmc', 'nyasmc'):
            raise SignalExit('--clib is for asm files (.asm, .asmc).')
    elif argd.get('--cargo', False) and (not lang.startswith('rust')):
        raise SignalExit('--cargo is for rust files (.rs).')
    return lang, template_files.get(
        lang,
        template_files['c'],
    )


def template_load(filepath, argd):
    """ Load content from one of the templates, based on the target file
        name and user args.
    """
    lang, template_file = choose_template(filepath, argd=argd)
    try:
        lines = []
        with open(template_file, 'r') as f:
            for line in f:
                if line.startswith('#!'):
                    continue
                lines.append(line)
    except FileNotFoundError as exnofile:
        raise SignalExit('Template file not found: {x.filename}'.format(
            x=exnofile,
        ))
    except EnvironmentError as ex:
        raise SignalExit('Error reading from template file: {}'.format(ex))
    debug('Using {} template for makefile: {}'.format(lang, template_file))
    return ''.join(lines)


def template_render(filepath, makefile=None, argd=None, config=None):
    """ Render the makefile template for a given c source file name. """
    parentdir, filename = os.path.split(filepath)
    makefile = os.path.abspath(
        os.path.join(parentdir, makefile or DEFAULT_MAKEFILE)
    )
    binary = os.path.splitext(filename)[0]
    author = fix_author((config or {}).get('author', ''))

    templateargs = {
        'author': author,
        'binary': binary,
        'date': ' {}'.format(date()) if author else date(),
        'source': filename,
        'source_path': os.path.relpath(filepath),
    }
    template = template_load(filepath, {} if (argd is None) else argd)

    # Format the template with compiler-specific settings.
    debug('Rendering makefile: {}'.format(makefile))
    return makefile, template.format(**templateargs)


def template_render_multi(filepaths, makefile=None, argd=None, config=None):
    """ Render the makefile template for a given c source file name. """
    if not filepaths:
        raise SignalExit('No target file specified for makefile.')

    parentdir, mainfile = os.path.split(filepaths[0])
    srcfiles = (os.path.split(s)[-1] for s in filepaths)
    makefile = os.path.abspath(
        os.path.join(parentdir, makefile or DEFAULT_MAKEFILE)
    )
    binary = os.path.splitext(mainfile)[0]
    author = fix_author((config or {}).get('author', ''))

    templateargs = {
        'author': author,
        'binary': binary,
        'date': ' {}'.format(date()) if author else date(),
        'source': ' '.join(srcfiles),
        'source_path': os.path.relpath(mainfile),
    }
    template = template_load(mainfile, {} if (argd is None) else argd)

    # Format the template with compiler-specific settings.
    debug('Rendering makefile: {}'.format(makefile))
    return makefile, template.format(**templateargs)
