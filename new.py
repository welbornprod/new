#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" new.py
    ...Creates new files based on templates (plugin-based templates)
    -Christopher Welborn 12-25-2014
"""

# TODO: Make loadable classes for plugins (so that 2 plugins can be in the
#       same file) ..python needs a unittest plugin.
# TODO: Implement the basic plugins (python, bash, html)
import os
import sys
from docopt import docopt

import plugins

NAME = 'New'
VERSION = '0.0.1'
VERSIONSTR = '{} v. {}'.format(NAME, VERSION)
SCRIPT = os.path.split(os.path.abspath(sys.argv[0]))[1]
SCRIPTDIR = os.path.abspath(sys.path[0])

USAGESTR = """{versionstr}
    Usage:
        {script} -h | -v | -p [-D]
        {script} [FILETYPE] FILENAME [-D]

    Options:
        FILETYPE      : Type of file to create (bash, python, html)
                        Defaults to: python
        FILENAME      : File name for the new file.
        -D,--debug    : Show more debugging info.
        -h,--help     : Show this help message.
        -p,--plugins  : List all available plugins.
        -v,--version  : Show version.
""".format(script=SCRIPT, versionstr=VERSIONSTR)
# Where to locate plugins.
PLUGINDIR = os.path.join(SCRIPTDIR, 'plugins')
sys.path.insert(1, PLUGINDIR)

# Global debug flag.
DEBUG = False


def main(argd):
    """ Main entry point, expects doctopt arg dict as argd """
    global plugins, DEBUG
    plugins.DEBUG = DEBUG = argd['--debug']

    # Load all available plugins.
    pluginset = plugins.load_plugins(PLUGINDIR)

    if argd['--plugins']:
        plugins.list_plugins(pluginset)
        return 1

    ftype = argd['FILETYPE'] or 'python'
    plugin = plugins.get_plugin_byname(pluginset, ftype)
    if not plugin:
        print('\nNot a valid file type (not supported): {}'.format(ftype))
        print('\nUse --plugins to list available plugins.\n')
        return 1

    fname = ensure_file_ext(argd['FILENAME'], plugin)
    if not valid_filename(fname):
        return 1

    content = plugin.create()
    if not content:
        print('\nFailed to create file: {}'.format(fname))
        return 1

    # Do post-processing plugins.
    do_post_plugins(pluginset, fname)
    return 0


def confirm(question):
    """ Confirm a question. Returns True for yes, False for no. """
    if not question:
        raise ValueError('No question provided to confirm()!')

    if not question.endswith('?'):
        question = '{}?'.format(question)

    answer = input('\n{} (y/N): '.format(question)).lower().strip()
    return answer.startswith('y')


def debug(*args, **kwargs):
    """ Debug print (only if DEBUG == Truthy). """
    if DEBUG:
        print(*args, **kwargs)


def do_post_plugins(plugins, fname):
    """ Handle all post-processing plugins.
        These plugins will be given the file name to do what they wish with it.
    """
    for plugin in (p for p in plugins['post'].values()):
        plugin.process(fname)


def ensure_file_ext(fname, plugin):
    """ Ensure the file name has a valid extension for it's plugin.
        Returns a str containing a valid file name (fixed or original)
    """

    for plugin_ext in plugin.extensions:
        if fname.endswith(plugin_ext):
            # The file name was okay.
            return fname

    # Add the extension (first extension in the list wins.)
    return '{}{}'.format(fname, plugin.extensions[0])


def valid_filename(fname):
    """ Make sure a file doesn't exist already.
        If it does exist, confirm that the user wants to overwrite it.
        Returns True if it is safe to write the file, otherwise False.
    """
    if not os.path.exists(fname):
        return True

    if not confirm('File exists!: {}\nOverwrite the file?'.format(fname)):
        print('\nUser cancelled.\n')
        return False

    return True

if __name__ == '__main__':
    mainret = main(docopt(USAGESTR, version=VERSIONSTR))
    sys.exit(mainret)
