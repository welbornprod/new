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

import plugins
from plugins import docopt
from plugins import C
debug = plugins.debug
debug_ex = plugins.debug_ex
print_err = plugins.print_err

NAME = 'New'
# Base version. Actual version is computed.
BASEVERSION = '0.6.1'
SCRIPT = os.path.split(os.path.abspath(sys.argv[0]))[1]
SCRIPTDIR = os.path.abspath(sys.path[0])

# Where to locate plugins.
PLUGINDIR = os.path.join(SCRIPTDIR, 'plugins')
sys.path.insert(1, PLUGINDIR)

plugins.set_debug_mode(
    (
        ('-d' in sys.argv) or ('--debug' in sys.argv) or
        ('-P' in sys.argv) or ('--debugplugin' in sys.argv)
    ),
    debugplugin=('-P' in sys.argv) or ('--debugplugin' in sys.argv),
)

try:
    # Load all available plugins.
    plugins.load_plugins(PLUGINDIR)
except plugins.InvalidConfig as ex:
    print_err(ex)
    sys.exit(1)

VERSION = plugins.append_plugin_versions(BASEVERSION)
VERSIONSTR = f'{NAME} v. {VERSION} (base: {BASEVERSION})'

# Passing this as a file name will write to stdout.
STDOUT_FILENAME = '-'

USAGESTR = """{versionstr}
    Usage:
        {script} --customhelp [-D]
        {script} (-c | -h | -v | -V | -p) [-D] [-P]
        {script} FILENAME... [-d | -O] [-D] [-P] [-o] [-x]
        {script} PLUGIN (-C | -H) [-D] [-P]
        {script} PLUGIN [-D] [-P]
        {script} PLUGIN FILENAME... [-d | -O] [-D] [-P] [-o] [-x]

    Options:
        ARGS                 : Plugin-specific args.
                               Use -H for plugin-specific help.
                               Simply using '--' is enough to run post-plugins
                               as commands with no args.
        PLUGIN               : Plugin name to use (like bash, python, etc.)
                               Defaults to: python (unless set in config)
        FILENAME             : File name for the new file.
                               Multiple files can be created.
        --customhelp         : Show help for creating a custom plugin.
        -c,--config          : Print global config and exit.
        -C,--pluginconfig    : Print plugin config and exit.
                               If a file path is given, the default plugin for
                               that file type will be used.
        -d,--dryrun          : Don't write anything. Print to stdout instead.
        -D,--debug           : Show more debugging info.
        -H,--pluginhelp      : Show plugin help.
                               If a file path is given, the default plugin for
                               that file type will be used.
        -h,--help            : Show this help message.
        -o,--noopen          : Don't open the file after creating it.
        -O,--overwrite       : Overwrite existing files.
        -P,--debugplugin     : Show more plugin-debugging info.
        -p,--plugins         : List all available plugins.
        -x,--executable      : Force the chmodx plugin to run, to make the file
                               executable. This is for plugin types that
                               normally ignore the chmodx plugin.
        -V,--pluginversions  : Show all plugin versions.
        -v,--version         : Show version.

    Plugin arguments must follow a bare -- argument.
""".format(script=SCRIPT, versionstr=VERSIONSTR)


def main(argd):
    """ Main entry point, expects doctopt arg dict as argd """
    # Do any procedures that don't require a file name/type.
    if argd['--customhelp']:
        return 0 if plugins.custom_plugin_help() else 1
    elif argd['--pluginversions']:
        return 0 if plugins.list_plugin_versions() else 1
    elif argd['--plugins']:
        plugins.list_plugins()
        return 0
    elif argd['--config']:
        return 0 if plugins.config_dump() else 1

    # Determine plugin based on file name/file type/explicit name.
    use_default_plugin = not (argd['--pluginhelp'] or argd['--pluginconfig'])
    debug('Use default plugin?: {}'.format(use_default_plugin))
    pluginclses = get_plugins(
        argd['PLUGIN'],
        argd['FILENAME'],
        use_default=use_default_plugin,
    )
    if not pluginclses:
        # No a valid plugin names, user cancelled text plugin use.
        return 1

    createdfiles = {}
    for plugin, filepaths in pluginclses.items():
        try:
            pluginfiles = handle_plugin(plugin, filepaths, argd)
        except plugins.SignalExit as ex:
            return ex.code
        if not pluginfiles:
            break
        createdfiles.setdefault(plugin, [])
        createdfiles[plugin].extend(pluginfiles)

    return handle_post_plugins(createdfiles)


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


def expand_path(fname):
    """ Expand a file path, if it's not the marker for stdout output. """
    if fname == STDOUT_FILENAME:
        return fname
    return os.path.abspath(fname)


def get_plugins(pluginname, filenames, use_default=True):
    """ Get the plugin to use based on the user's args (arg dict from docopt).
        When an invalid name is used, optionally use the text plugin.
        Print a message and return None on failure/cancellation.
        Arguments:
            pluginname   : Plugin name provided by the user (from docopt).
            filenames    : File names provided by the user (from docopt).
            use_default  : Whether determine_plugin() should use the default
                           plugin on bad names/types.
                           Default: True
    """
    debug('Using PLUGIN={!r}, FILENAMES={!r}'.format(pluginname, filenames))
    if filenames and (filenames[0] == '--'):
        # Occurs when no args are passed after the seperator: new plugin --
        debug('No args after --, filename is: {}'.format(filenames[0]))
        filename = None

    pluginclses = plugins.determine_plugins(
        pluginname,
        filenames,
        use_default=use_default,
    )
    if not pluginclses:
        return {}

    if all((cls is not None) for cls in pluginclses):
        # All plugins were determined.
        return {cls(): filepaths for cls, filepaths in pluginclses.items()}

    # Regular plugin-determinaing failed
    for filename in pluginclses[None]:
        ftype = pluginname or filename
        print_err('Not a valid file type (not supported): {}'.format(ftype))
        if not use_default:
            return None
        elif not confirm('Continue with a blank file?'):
            print_err('Use --plugins to list available plugins.\n')
            return None

        # Use text plugin (blank file).
        pluginname = 'text'
        plugincls = plugins.determine_plugin(pluginname, filename)
        if plugincls:
            pluginclses.setdefault(plugincls, [])
            pluginclses[plugincls].append(filename)
        else:
            # If the text plugin can't be loaded, we have bigger problems.
            print_err('Something is horribly wrong.')
            print_err('Unable to load the text plugin, sorry.')
            return None
    # All plugins were determined or set to the TextPlugin.
    return {cls(): filepaths for cls, filepaths in pluginclses.items()}


def handle_content(fname, content, plugin, dryrun=False, filepaths=None):
    """ Either write the new content to a file,
        or print it if this is a dryrun.
        Run post-processing plugins if a file was written.
        Returns the created file name.
        Arguments:
            fname     : The file name to write.
            content   : Content to write to the file.
            plugin    : The plugin that created the content.
            filepaths : Any extra file paths that were passed to the plugin,
                        for multi-file plugins.
    """
    if content and plugin.ensure_newline and (not content.endswith('\n')):
        # Ensure newline if there is any content, only if plugin allows it.
        debug(
            'Adding missing newline for {} content.'.format(plugin.get_name())
        )
        content = ''.join((content, '\n'))
    elif content and plugin.ensure_newline and content.endswith('\n\n'):
        debug('Removing multiple newlines for {} content.'.format(
            plugin.get_name()
        ))
        content = '{}\n'.format(content.rstrip('\n'))

    if dryrun and fname != STDOUT_FILENAME:
        print_term('Dry run, would\'ve written: {}\n'.format(fname))
        print(content or '<No Content>')
        # No post plugins can run.
        return None

    created = write_file(fname, content)
    if not created:
        print_err('\nUnable to create: {}'.format(fname))
        return None

    if fname != STDOUT_FILENAME:
        print_status('Created ({}) {}'.format(plugin.get_name(), created))
    return created


def handle_exception(msg, ex_type, ex_value, ex_tb):
    """ Handle a plugin run() or create() exception (not Signal* exceptions).
        If DEBUG is True, the traceback will be printed, otherwise a simple
        message is printed.
        Returns an error exit status.
    """
    if plugins.DEBUG:
        exargs = {'ex_type': ex_type, 'ex_value': ex_value, 'ex_tb': ex_tb}
    else:
        exargs = {}
    print_ex(ex_value, msg, **exargs)
    return 1


def handle_plugin(plugin, filepaths, argd):
    """ Sets up the plugin, runs command plugins, plugin help,
        plugin config dump, or multiple file writes.
        Returns a list of created files.
    """
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
        raise plugins.SignalExit('Exiting for errors.', code=exitcode)

    if plugin.multifile:
        # This plugin handles multiple file names on it's own.
        created = handle_plugin_multifile(plugin, filepaths, argd)
        return [created] if created else []

    createdfiles = []
    for filename in filepaths:
        created = handle_plugin_file(plugin, filename, argd)
        if created:
            createdfiles.append(created)
        else:
            break
    return createdfiles


def handle_plugin_file(plugin, filename, argd):
    """ Ensure valid file names, call plugin.create(), catch any
        SignalActions or SignalExits, and eventually write the file content
        if everything goes well.
        Returns the name of the file created.
    """
    debug('Handling file for {} plugin: {}'.format(
        plugin.get_name(),
        filename,
    ))
    # Get valid file name for this file.
    fname = expand_path(
        ensure_file_ext(filename, plugin)
    )

    # Make sure the file name doesn't conflict with any plugins.
    # ...mainly during development and testing.
    if plugins.conflicting_file(plugin, filename, fname):
        return None
    pluginname = plugin.get_name().title()
    try:
        content = plugin._create(fname, argd['ARGS'])
    except plugins.SignalAction as action:
        # See if we have content to write
        # No-content is fatal unless explicitly allowed.
        if not (action.content or plugin.allow_blank):
            errmsg = 'Plugin action with no content!\n    {}'
            print_err(errmsg.format(action.message))
            return None

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
    # Non-existant file names are considered valid, and need no confirmation.
    if not valid_filename(
            fname,
            dryrun=argd['--dryrun'],
            overwrite=argd['--overwrite']):
        return None

    if not (plugin.allow_blank or content):
        debug('{} is not allowed to create a blank file.'.format(pluginname))
        print_err('\nFailed to create file: {}'.format(fname))
        return None

    if argd['--noopen']:
        # Don't open the file.
        debug('Cancelling open plugin for {}'.format(plugin.get_name()))
        plugin.ignore_deferred.add('open')

    return handle_content(
        fname,
        content,
        plugin,
        dryrun=argd['--dryrun'],
        filepaths=None,
    )


def handle_plugin_multifile(plugin, filepaths, argd):
    """ Like handle_plugin_file, except the plugin will receive multiple
        file names and return a single file name and content to be written.
        It is the plugin's responsibility to ensure a valid file name
        and extension.
        This function will handle the setup/error-handling for that file
        to be written.
        Returns the name of the file created.
    """
    pluginname = plugin.get_name().title()
    try:
        filename, content = plugin._create_multi(filepaths, argd['ARGS'])
    except plugins.SignalAction as action:
        # See if we have content to write
        # No-content is fatal unless explicitly allowed.
        if not (action.content or plugin.allow_blank):
            errmsg = 'Plugin action with no content!\n    {}'
            print_err(errmsg.format(action.message))
            return None

        content = action.content
        # Print plugin notification of any major changes (file name changes)
        if action.message:
            for line in action.message.split('\n'):
                plugin.print_status(line)
        # Plugin is changing the output file name.
        if action.filename:
            filename = action.filename
        # Plugin is adding ignore_post plugins.
        if action.ignore_post:
            debug('Adding ignore_post: {!r}'.format(action.ignore_post))
            plugin.ignore_post.update(action.ignore_post)
    except plugins.SignalExit as excancel:
        # Plugin wants to stop immediately.
        raise plugins.SignalExit(
            'Exiting for errors.',
            code=handle_signalexit(excancel)
        )
    except Exception:
        raise plugins.SignalExit(
            'Exiting for errors.',
            code=handle_exception(
                '{} error:'.format(pluginname),
                *sys.exc_info()
            )
        )

    # Confirm overwriting existing files, exit on refusal.
    # Non-existant file names are considered valid, and need no confirmation.
    if not valid_filename(
            filename,
            dryrun=argd['--dryrun'],
            overwrite=argd['--overwrite']):
        return None

    if not (plugin.allow_blank or content):
        debug('{} is not allowed to create a blank file.'.format(pluginname))
        print_err('\nFailed to create file: {}'.format(filename))
        return None

    if argd['--noopen']:
        # Don't open the file.
        debug('Cancelling open plugin for {}'.format(plugin.get_name()))
        plugin.ignore_deferred.add('open')

    return handle_content(
        filename,
        content,
        plugin,
        dryrun=argd['--dryrun'],
        filepaths=filepaths,
    )


def handle_post_plugins(createdinfo):
    """ Runs post plugins on the created files.
        Arguments:
            createdinfo : A dict of {plugin: [created_file, ..], ..}
    """
    errs = 0
    for plugin, pluginfiles in createdinfo.items():
        errs += plugins.do_post_plugins(pluginfiles, plugin)
    return errs


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


def parse_args():
    """ Strips plugin args from sys.argv, and fixes the docopt argd.
        Returns a docopt arg dict.
    """
    sysargs = []
    pluginargs = []
    in_plugin_args = False
    for arg in sys.argv[1:]:
        if arg == '--':
            in_plugin_args = True
            continue
        if in_plugin_args:
            pluginargs.append(arg)
        else:
            sysargs.append(arg)

    plugins.debugprinter.enable(('-D' in sysargs) or ('--debug' in sysargs))
    debug('  Sys args: {}'.format(sysargs))
    debug('Plugin arg: {}'.format(pluginargs), align=True)

    argd = docopt(USAGESTR, version=VERSIONSTR, argv=sysargs, script=SCRIPT)
    argd['ARGS'] = pluginargs
    return argd


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
    print_term('{}: {}'.format(C('new'.ljust(16), 'blue'), msg))


def print_term(*args, **kwargs):
    """ Print only if stdout is a terminal. """
    kwargs['file'] = kwargs.get('file', sys.stdout)
    if kwargs['file'].isatty():
        print(*args, **kwargs)


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
        mainret = main(parse_args())
    except ValueError as ex:
        print_err('Error: {}'.format(ex))
        mainret = 1
    sys.exit(mainret)
