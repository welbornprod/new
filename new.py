#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" new.py
    ...Creates new files based on templates (plugin-based templates)
    -Christopher Welborn 12-25-2014

    Copyright (C) 2014-2016 Christopher Welborn

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
import os
import sys
import traceback

import docopt

import plugins
debug = plugins.debug
debug_ex = plugins.debug_ex
print_err = plugins.print_err

NAME = 'New'
VERSION = '0.6.0'
VERSIONSTR = '{} v. {}'.format(NAME, VERSION)
SCRIPT = os.path.split(os.path.abspath(sys.argv[0]))[1]
SCRIPTDIR = os.path.abspath(sys.path[0])

USAGESTR = """{versionstr}
    Usage:
        {script} --customhelp [-D]
        {script} (-c | -h | -v | -p) [-D]
        {script} FILENAME [-d | -O] [-D] [-o] [-x]
        {script} FILENAME [-d | -O] [-D] [-o] [-x] -- ARGS...
        {script} PLUGIN (-C | -H) [-D]
        {script} PLUGIN [-D] -- ARGS...
        {script} PLUGIN FILENAME [-d | -O] [-D] [-o] [-x]
        {script} PLUGIN FILENAME [-d | -O] [-D] [-o] [-x] -- ARGS...

    Options:
        ARGS               : Plugin-specific args.
                             Use -H for plugin-specific help.
                             Simply using '--' is enough to run post-plugins
                             as commands with no args.
        PLUGIN             : Plugin name to use (like bash, python, etc.)
                             Defaults to: python (unless set in config)
        FILENAME           : File name for the new file.
        --customhelp       : Show help for creating a custom plugin.
        -c,--config        : Print global config and exit.
        -C,--pluginconfig  : Print plugin config and exit.
                             If a file path is given, the default plugin for
                             that file type will be used.
        -d,--dryrun        : Don't write anything. Print to stdout instead.
        -D,--debug         : Show more debugging info.
        -H,--pluginhelp    : Show plugin help.
                             If a file path is given, the default plugin for
                             that file type will be used.
        -h,--help          : Show this help message.
        -o,--noopen        : Don't open the file after creating it.
        -O,--overwrite     : Overwrite existing files.
        -p,--plugins       : List all available plugins.
        -x,--executable    : Force the chmodx plugin to run, to make the file
                             executable. This is for plugin types that
                             normally ignore the chmodx plugin.
        -v,--version       : Show version.
""".format(script=SCRIPT, versionstr=VERSIONSTR)

# Where to locate plugins.
PLUGINDIR = os.path.join(SCRIPTDIR, 'plugins')
sys.path.insert(1, PLUGINDIR)

# Passing this as a file name will write to stdout.
STDOUT_FILENAME = '-'

# Global debug flag, set with --debug.
DEBUG = False
# Print extra info about plugins (the chosen plugin's attributes).
# This has to be set manually for now.
DEBUG_PLUGIN = False


def main(argd):
    """ Main entry point, expects doctopt arg dict as argd """
    global DEBUG
    DEBUG = argd['--debug']
    if not DEBUG:
        plugins.debugprinter.disable()
    if argd['--customhelp']:
        return 0 if plugins.custom_plugin_help() else 1

    try:
        # Load all available plugins.
        plugins.load_plugins(PLUGINDIR)
    except plugins.InvalidConfig as ex:
        print_err(ex)
        return 1

    # Do any procedures that don't require a file name/type.
    if argd['--plugins']:
        plugins.list_plugins()
        return 0
    elif argd['--config']:
        return 0 if plugins.config_dump() else 1

    # Determine plugin based on file name/file type/explicit name.
    use_default_plugin = not (argd['--pluginhelp'] or argd['--pluginconfig'])
    debug('Use default plugin?: {}'.format(use_default_plugin))
    plugin = get_plugin(argd, use_default=use_default_plugin)
    if not plugin:
        # Not a valid plugin name, user cancelled text plugin use.
        return 1

    if DEBUG_PLUGIN:
        plugins.print_json(plugin.attributes(), sort_keys=True)

    # Notify plugin that this might be a dry run.
    plugin.dryrun = argd['--dryrun']

    if argd['--executable'] and 'chmodx' in plugin.ignore_post:
        # Current behaviour says files are made executable unless told
        # otherwise, so to 'force chmodx' simply means to remove it from the
        # 'ignored' list.
        try:
            plugin.ignore_post.remove('chmodx')
        except (AttributeError, KeyError):
            pass
    pluginname = plugin.get_name().title()
    debug('Using plugin: {}'.format(pluginname))
    # Do plugin help.
    if argd['--pluginhelp']:
        return 0 if plugin.help() else 1
    elif argd['--pluginconfig']:
        return 0 if plugin.config_dump() else 1
    elif hasattr(plugin, 'run'):
        # This is a post plugin, it should only be used as a command.
        debug('Running post-processing plugin as command: {}'.format(
            pluginname
        ))
        try:
            exitcode = plugin._run(args=argd['ARGS'])
        except NotImplementedError as ex:
            print_err(str(ex))
            exitcode = 1
        except plugins.SignalExit as excancel:
            exitcode = handle_signalexit(excancel)
        except Exception:
            exitcode = handle_exception(
                '{} error:'.format(pluginname),
                *sys.exc_info())
        return exitcode

    # Get valid file name for this file.
    fname = ensure_file_ext(argd['FILENAME'], plugin)

    # Make sure the file name doesn't conflict with any plugins.
    # ...mainly during development and testing.
    if plugins.conflicting_file(plugin, argd['FILENAME'], fname):
        return 1

    try:
        content = plugin._create(fname, argd['ARGS'])
    except plugins.SignalAction as action:
        # See if we have content to write
        # No-content is fatal unless explicitly allowed.
        if not (action.content or plugin.allow_blank):
            errmsg = 'Plugin action with no content!\n    {}'
            print_err(errmsg.format(action.message))
            return 1

        content = action.content
        # Print plugin notification of any major changes (file name changes)
        if action.message:
            for line in action.message.split('\n'):
                plugin.print_status(line)
        # Plugin is changing the output file name.
        if action.filename:
            fname = action.filename
        # Plugin is adding ignore_post plugins.
        if action.ignore_post:
            debug('Adding ignore_post: {!r}'.format(action.ignore_post))
            plugin.ignore_post.update(action.ignore_post)
    except plugins.SignalExit as excancel:
        # Plugin wants to stop immediately.
        return handle_signalexit(excancel)
    except Exception:
        return handle_exception(
            '{} error:'.format(pluginname),
            *sys.exc_info())

    # Confirm overwriting existing files, exit on refusal.
    # Non-existant file names are considered valid, and need no confimation.
    if not valid_filename(
            fname,
            dryrun=argd['--dryrun'],
            overwrite=argd['--overwrite']):
        return 1

    if not (plugin.allow_blank or content):
        debug('{} is not allowed to create a blank file.'.format(pluginname))
        print_err('\nFailed to create file: {}'.format(fname))
        return 1

    if argd['--noopen']:
        # Don't open the file.
        debug('Cancelling open plugin for {}'.format(plugin.get_name()))
        plugin.ignore_deferred.add('open')

    return handle_content(fname, content, plugin, dryrun=argd['--dryrun'])


def confirm(msg):
    """ Return True if the user answers y[es] to a question, otherwise False.
    """
    return input('\n{} (y/N): '.format(msg)).lower().startswith('y')


def ensure_file_ext(fname, plugin):
    """ Ensure the file name has a valid extension for it's plugin.
        Returns a str containing a valid file name (fixed or original)
    """
    if fname == STDOUT_FILENAME:
        return fname

    if not plugin.extensions:
        # Some files don't have an extension (like makefiles)
        return fname

    if plugin.any_extension:
        # Some plugins allow using a custom extension.
        # Still, fallback to default if no extension is provided.
        filepath, basename = os.path.split(fname)
        _, fileext = os.path.splitext(basename)
        if fileext:
            return fname

    for plugin_ext in plugin.extensions:
        if fname.endswith(plugin_ext):
            # The file name was okay.
            return fname

    # Add the extension (first extension in the list wins.)
    return '{}{}'.format(fname, plugin.extensions[0])


def get_plugin(argd, use_default=True):
    """ Get the plugin to use based on the user's args (arg dict from docopt).
        When an invalid name is used, optionally use the text plugin.
        Print a message and return None on failure/cancellation.
        Arguments:
            argd         : Command line argument dict from docopt.
            use_default  : Whether determine_plugin() should use the default
                           plugin on bad names/types.
                           Default: True
    """
    plugincls = plugins.determine_plugin(argd, use_default=use_default)
    if plugincls:
        return plugincls()

    ftype = argd['PLUGIN'] or argd['FILENAME']
    print_err('Not a valid file type (not supported): {}'.format(ftype))
    if not use_default:
        return None
    elif not confirm('Continue with a blank file?'):
        print_err('Use --plugins to list available plugins.\n')
        return None

    argd['PLUGIN'] = 'text'
    plugincls = plugins.determine_plugin(argd)
    if plugincls:
        return plugincls()

    print_err('Unable to load the text plugin, sorry.')
    return None


def handle_content(fname, content, plugin, dryrun=False):
    """ Either write the new content to a file,
        or print it if this is a dryrun.
        Run post-processing plugins if a file was written.
        Returns exit code status.
    """
    if content and plugin.ensure_newline and (not content.endswith('\n')):
        # Ensure newline if there is any content, only if plugin allows it.
        debug(
            'Adding missing newline for {} content.'.format(plugin.get_name())
        )
        content = ''.join((content, '\n'))

    if dryrun and fname != STDOUT_FILENAME:
        print_term('Dry run, would\'ve written: {}\n'.format(fname))
        print(content or '<No Content>')
        # No post plugins can run.
        return 0 if content else 1

    created = write_file(fname, content)
    if not created:
        print_err('\nUnable to create: {}'.format(fname))
        return 1

    if fname != STDOUT_FILENAME:
        print_status('Created {}'.format(created))
        # Do post-processing plugins on the created file.
        return plugins.do_post_plugins(fname, plugin)
    return 0


def handle_exception(msg, ex_type, ex_value, ex_tb):
    """ Handle a plugin run() or create() exception (not Signal* exceptions).
        If DEBUG is True, the traceback will be printed, otherwise a simple
        message is printed.
        Returns an error exit status.
    """
    if DEBUG:
        exargs = {'ex_type': ex_type, 'ex_value': ex_value, 'ex_tb': ex_tb}
    else:
        exargs = {}
    print_ex(ex_value, msg, **exargs)
    return 1


def handle_signalexit(ex):
    """ Handle a SignalExit exception's message printing,
        return the final exit code.
    """
    if ex.code != 0:
        # This was a real error, so print a message.
        reason = ex.reason or 'No reason was given for the exit.'
        print_err('\n{}\n'.format(reason))
        debug_ex()
    return ex.code


def make_dirs(path):
    """ Use os.makedirs() to ensure a path exists, and create it if needed.
        Returns the existing path on success.
        Returns None on failure.
        Errors are printed, except for FileExistsError (it is ignored).
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


def print_ex(ex, msg, ex_type=None, ex_value=None, ex_tb=None):
    """ Print an error msg, formatted with str(Exception).
        Arguments:
            msg         : User message to print.
            ex          : Exception to print.

        Arguments for debug mode:
            ex_type     : Type of exception obtained from sys.exc_info()
            ex_value    : Value of exception obtained from sys.exc_info()
            ex_tb       : Traceback for exception obtained from sys.exc_info()
    """
    if all((ex_type, ex_value, ex_tb)):
        print_err('{} (debug mode traceback)\n{}\n'.format(
            msg,
            ''.join(traceback.format_exception(ex_type, ex_value, ex_tb))
        ))
        return 1
    # No traceback.
    print_err('({}) {}\n  {}'.format(type(ex).__name__, msg, ex))
    return 1


def print_status(msg):
    """ Print a status message.
        (color-formatting in the future)
    """
    print_term('{}: {}'.format('new'.ljust(15), msg))


def print_term(*args, **kwargs):
    """ Print only if stdout is a terminal. """
    if print_term.is_tty:
        print(*args, **kwargs)


# print_term remembers whether stdout is a tty.
print_term.is_tty = sys.stdout.isatty()


def valid_filename(fname, dryrun=False, overwrite=False):
    """ Make sure a file doesn't exist already.
        If it does exist, confirm that the user wants to overwrite it.
        If `overwrite` is True, this function always returns True.
        Returns True if it is safe to write the file, otherwise False.

        For dryruns, existing files are ignored.
    """
    if overwrite:
        return True
    if not os.path.exists(fname):
        return True

    return dryrun or plugins.confirm_overwrite(fname)


def write_file(fname, content):
    """ Write a new file given a filename and it's content.
        Returns the file name on success, or None on failure.
    """
    if content is None:
        content = ''
    if fname == STDOUT_FILENAME:
        # This is not needed, because `write_file()` is short-circuited in
        # `handle_content()` anyway.
        print(content)
        return STDOUT_FILENAME

    # Create directories if needed.
    dirs = os.path.split(fname)[0]
    if ('/' in fname) and (not make_dirs(dirs)):
        print_err('Failed to create directory: {}'.format(dirs))
        return None

    try:
        with open(fname, 'w') as f:
            f.write(content)
    except EnvironmentError as ex:
        print_ex(
            ex,
            'Failed to write file: {}'.format(fname))
        return None
    except Exception as exgen:
        print_ex(exgen, 'Error writing file: {}'.format(fname))
        return None
    return fname


if __name__ == '__main__':
    # Okay, run.
    try:
        mainret = main(docopt.docopt(USAGESTR, version=VERSIONSTR))
    except ValueError as ex:
        print_err('Error: {}'.format(ex))
        mainret = 1
    sys.exit(mainret)
