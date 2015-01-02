#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" new.py
    ...Creates new files based on templates (plugin-based templates)
    -Christopher Welborn 12-25-2014
"""

# TODO: Implement the basic plugins (python, bash, html)
import os
import sys
import docopt

import plugins

NAME = 'New'
VERSION = '0.0.1'
VERSIONSTR = '{} v. {}'.format(NAME, VERSION)
SCRIPT = os.path.split(os.path.abspath(sys.argv[0]))[1]
SCRIPTDIR = os.path.abspath(sys.path[0])

USAGESTR = """{versionstr}
    Usage:
        {script} -h | -v | -p [-D]
        {script} FILETYPE -H
        {script} FILENAME [-d] [-D]
        {script} FILETYPE FILENAME [-d] [-D]
        {script} FILETYPE FILENAME ARGS... [-d] [-D]

    Options:
        ARGS               : Plugin-specific args.
        FILETYPE           : Type of file to create (bash, python, html)
                             Defaults to: python
        FILENAME           : File name for the new file.
        -d,--dryrun        : Show what would be written, don't write anything.
        -D,--debug         : Show more debugging info.
        -H,--HELP          : Show plugin help.
        -h,--help          : Show this help message.
        -p,--plugins       : List all available plugins.
        -v,--version       : Show version.
""".format(script=SCRIPT, versionstr=VERSIONSTR)

# Where to locate plugins.
PLUGINDIR = os.path.join(SCRIPTDIR, 'plugins')
sys.path.insert(1, PLUGINDIR)

# Global debug flag.
DEBUG = False


def main(argd):
    """ Main entry point, expects doctopt arg dict as argd """
    global DEBUG
    plugins.DEBUG = DEBUG = argd['--debug']

    # Load all available plugins.
    plugins.load_plugins(PLUGINDIR)

    # Do any procedures that don't require a file name/type.
    if argd['--plugins']:
        plugins.list_plugins()
        return 1

    # Get plugin needed for this file type.
    ftype = argd['FILETYPE'] or 'python'
    plugin = plugins.get_plugin_byname(ftype)
    if not plugin:
        print('\nNot a valid file type (not supported): {}'.format(ftype))
        print('\nUse --plugins to list available plugins.\n')
        return 1

    # Do plugin help.
    if argd['--HELP']:
        return 0 if plugins.plugin_help(plugin) else 1

    # Get valid file name for this file.
    fname = ensure_file_ext(argd['FILENAME'], plugin)
    if not valid_filename(fname):
        return 1

    try:
        content = plugin.create(fname, argd['ARGS'])
    except plugins.SignalAction as action:
        # Plugin is changing the file name.
        if not action.content:
            print('Plugin action with no content: {}'.format(action.message))
            return 1
        else:
            content = action.content
        # Changing the output file name.
        if action.filename:
            fname = action.filename
    except Exception as ex:
        print('{} error: {}'.format(plugin.get_name().title(), ex))
        return 1

    if not content:
        print('\nFailed to create file: {}'.format(fname))
        return 1

    if argd['--dryrun']:
        print('\nWould\'ve written:')
        print(content)
    else:
        created = write_file(fname, content)
        if created:
            print('\nCreated: {}'.format(created))
        else:
            print('\nUnable to create: {}'.format(created))
            return 1

    # Do post-processing plugins on the created file.
    plugins.do_post_plugins(fname)
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


def write_file(fname, content):
    """ Write a new file given a filename and it's content.
        Returns the file name on success, or None on failure.
    """

    try:
        with open(fname, 'w') as f:
            f.write(content)
    except EnvironmentError as ex:
        print('\nFailed to write file: {}\n{}'.format(fname, ex))
        return None
    except Exception as exgen:
        print('\nError writing file: {}\n{}'.format(fname, exgen))
        return None
    return fname

if __name__ == '__main__':

    # Parse args with docopt.
    argd = docopt.docopt(USAGESTR, version=VERSIONSTR)
    # Okay, run.
    mainret = main(argd)
    sys.exit(mainret)
