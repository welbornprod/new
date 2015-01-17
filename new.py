#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" new.py
    ...Creates new files based on templates (plugin-based templates)
    -Christopher Welborn 12-25-2014
"""
import os
import sys
import docopt

import plugins
debug = plugins.debug

NAME = 'New'
VERSION = '0.0.1-4'
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
    ftype = argd['FILETYPE'] or plugins.config.get('default_plugin', 'python')
    plugin = plugins.get_plugin_byname(ftype)
    if plugin:
        debug('Using plugin: {}'.format(plugin.get_name()))
    else:
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

    # Make sure the file name doesn't conflict with any plugins.
    if plugins.conflicting_file(plugin, argd['FILENAME'], fname):
        return 1

    try:
        content = plugin.create(fname, argd['ARGS'])
    except plugins.SignalAction as action:
        # See if we have content to write (no content is fatal).
        if not action.content:
            errmsg = 'Plugin action with no content!\n    {}'
            print(errmsg.format(action.message))
            return 1
        else:
            content = action.content
        # Print a plain message if set.
        if action.message:
            print(action.message)

        # Changing the output file name.
        if action.filename:
            fname = action.filename
    except Exception as ex:
        pluginname = plugin.get_name().title()
        print_ex(ex, '{} error:'.format(pluginname), with_class=True)
        return 1

    if not content:
        print('\nFailed to create file: {}'.format(fname))
        return 1

    if argd['--dryrun']:
        print('\nWould\'ve written: {}'.format(fname))
        print(content)
    else:
        created = write_file(fname, content)
        if created:
            print_status('Created {}'.format(created))
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


def get_ex_class(ex, default=None):
    """ Returns a string containing the __class__ for an object.
        The string repr is cleaned up a little bit. If it can't be
        determined then 'default' is returned.
    """
    errclass = str(getattr(ex, '__class__', '')).split()[-1]
    if errclass:
        return errclass[1:-2]
    return default


def make_dirs(path):
    """ Use os.mkdirs() to ensure a path exists, and create it if needed.
        Returns the existing path on success.
        Returns None on failure.
        Errors are printed, except for FileExistsError (it is ignored)
    """
    try:
        os.makedirs(path)
        debug('Directory created: {}'.format(path))
    except FileExistsError:
        debug('Directory exists: {}'.format(path))
        return path
    except EnvironmentError as ex:
        print_ex(ex, 'Failed to create directory: {}'.format(path))
        return None
    return path


def print_err(msg):
    """ Print a formatted error msg.
        (color-formatting in the future.)
    """
    print('\n{}'.format(msg))


def print_ex(msg, ex, with_class=False):
    """ Print an error msg, formatted with str(Exception).
        Arguments:
            msg         : User message to print.
            ex          : Exception to print.
            with_class  : Use the Exception.__class__ in the message.
                          Default: False
    """
    if with_class:
        kls = get_ex_class(ex, '?')
        print_err('({}) {}\n  {}'.format(kls, msg, ex))
        return None
    print_err('{}\n  {}'.format(msg, ex))


def print_status(msg):
    """ Print a status message.
        (color-formatting in the future)
    """
    print('{}: {}'.format('new'.ljust(15), msg))


def valid_filename(fname):
    """ Make sure a file doesn't exist already.
        If it does exist, confirm that the user wants to overwrite it.
        Returns True if it is safe to write the file, otherwise False.
    """
    if not os.path.exists(fname):
        return True

    if not confirm('File exists!: {}\n\nOverwrite the file?'.format(fname)):
        print('\nUser cancelled.\n')
        return False

    return True


def write_file(fname, content):
    """ Write a new file given a filename and it's content.
        Returns the file name on success, or None on failure.
    """
    # Create directories if needed.
    dirs = os.path.split(fname)[0]
    if ('/' in fname) and (not make_dirs(dirs)):
        print_err('Failed to create directory: {}'.format(dirs))
        return None

    try:
        with open(fname, 'w') as f:
            f.write(content)
    except EnvironmentError as ex:
        print_ex(ex, 'Failed to write file: {}'.format(fname))
        return None
    except Exception as exgen:
        print_ex(exgen, 'Error writing file: {}'.format(fname))
        return None
    return fname

if __name__ == '__main__':
    # Parse args with docopt.
    argd = docopt.docopt(USAGESTR, version=VERSIONSTR)
    # Okay, run.
    mainret = main(argd)
    sys.exit(mainret)
