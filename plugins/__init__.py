""" Plugins package for New
    Includes the base plugin types (to be subclassed and overridden)
    and general plugin helper/loading functions.
    The raw plugins can be accessed with plugins.plugins.
"""

import inspect
import json
import os
import re
import shutil
import sys
from datetime import datetime
from enum import Enum
from importlib import import_module


SCRIPTDIR = os.path.abspath(sys.path[0])
DEBUG = False
config = {}
plugins = {'types': {}, 'post': {}, 'deferred': {}}


def config_dump():
    """ Dump config to stdout. """
    if not config:
        print('\nNo config found for plugins.\n')
        return False

    configstr = json.dumps(config, sort_keys=True, indent=4)
    print('\nConfig for plugins:\n')
    print(configstr)
    return True


def confirm(question):
    """ Confirm a question. Returns True for yes, False for no. """
    if not question:
        raise ValueError('No question provided to confirm()!')

    if not question.endswith('?'):
        question = '{}?'.format(question)

    answer = input('\n{} (y/N): '.format(question)).lower().strip()
    return answer.startswith('y')


def confirm_overwrite(filename):
    """ Use confirm() to confirm overwriting a file. """
    msg = 'File exists!: {}\n\nOverwrite the file?'.format(filename)
    if not confirm(msg):
        print('\nUser cancelled.\n')
        return False
    return True


def conflicting_file(plugin, filearg, filename):
    """ Make sure this file name and plugin mixture isn't going to cause a
        show-stopping conflict with New (for my own sanity).
        This only happens when creating .py files in New's directory, and only
        if they happen to have the same name as a plugin.

        Known mistake when testing this app:
            When in config: {plugins : { default_plugin: 'python' }}
               And running: ./new bash
            ...creates bash.py that will be found in sys.path.
    """
    # The python plugin can create conflicting files when ran in New's dir.
    # Any other plugins should be okay.
    if plugin.get_name() != 'python':
        return False

    # Check for conflicting dir.
    rootdir = filearg.partition('/')[0]

    for plugintype in plugins:
        # If the filename arg matches a plugin module name we have a conflict.
        conflict = plugins[plugintype].get(filearg, None)
        if conflict:
            break
        elif rootdir:
            conflict = plugins[plugintype].get(rootdir, None)
            if conflict:
                break
    else:
        return False

    debug('WARNING: File name conflicts with a plugin name!')
    debug('         This will create a file named: {}'.format(filename))

    if os.getcwd() == SCRIPTDIR:
        print('\n'.join((
            '\nCreating this file here ({}) will override the {} plugin:',
            '{}')).format(SCRIPTDIR, conflict.get_name(), filename))
        print('\nPlease create it in another directory.\n')
        return True

    return False


def date():
    """ Returns a string formatted date for today. """
    return datetime.strftime(datetime.today(), '%m-%d-%Y')


def debug(*args, **kwargs):
    """ Print a message only if DEBUG is truthy. """
    if not (DEBUG and args):
        return None
    parent = kwargs.get('parent', None)
    try:
        kwargs.pop('parent')
    except KeyError:
        pass
    backlevel = kwargs.get('back', 1)
    try:
        kwargs.pop('back')
    except KeyError:
        pass

    # Get filename, line number, and function name.
    frame = inspect.currentframe()
    # Go back a number of frames (usually 1).
    while backlevel > 0:
        frame = frame.f_back
        backlevel -= 1

    fname = os.path.split(frame.f_code.co_filename)[-1]
    lineno = frame.f_lineno
    if parent:
        func = '{}.{}'.format(parent.__class__.__name__, frame.f_code.co_name)
    else:
        func = frame.f_code.co_name

    # Patch args to stay compatible with print().
    pargs = list(args)
    lineinfo = '{}:{} {}(): '.format(fname, lineno, func).ljust(40)
    pargs[0] = ''.join((lineinfo, pargs[0]))
    print(*pargs, **kwargs)


def debug_load_error(plugintype, modname, plugin, exmsg):
    """ Print a debug message about plugin load errors. """
    errmsg = 'Error loading {ptype} plugin {mod}.{plugin}: {ex}'
    debug(errmsg.format(
        ptype=plugintype,
        mod=modname,
        plugin=plugin,
        ex=exmsg))


def debug_missing(attr, plugintype, modname, plugin):
    """ Print a debug message about a plugin's missing attribute. """
    msg = 'Missing attribute \'{}\'!'.format(attr)
    debug_load_error(plugintype, modname, plugin, msg)


def determine_plugin(argd):
    """ Determine which plugin to use based on user's filename, or filetype.
        Arguments:
            argd  : Docopt arg dict from user.
        Returns Plugin() on success, or None on failure.
        This may modify argd['FILENAME'] if needed.
    """
    default_file = config.get('global', {}).get('default_filename', 'new_file')
    use_post = argd['--pluginconfig']
    namedplugin = get_plugin_byname(argd['FILENAME'])
    if namedplugin:
        if argd['ARGS']:
            # Hack to allow plugin args with plugin name or file name missing.
            tryfilename = argd['ARGS'][0]
            tryext = os.path.splitext(tryfilename)[-1]
            if tryext in namedplugin.extensions:
                # Explicit file name given by extension, remove from ARGS.
                argd['FILENAME'] = tryfilename
                argd['ARGS'] = argd['ARGS'][1:]
                debug('Plugin loaded by name with args, file name given.')
                return namedplugin
            else:
                # Not a recognized file name, use it as an argument.
                debug('Plugin loaded by name with args, no known filename.')

        # Use default file name since no file name was given.
        argd['FILENAME'] = default_file
        debug('Plugin loaded by name, using default file name.')
        return namedplugin

    if argd['FILETYPE']:
        plugin = get_plugin_byname(argd['FILETYPE'], use_post=use_post)
        if not argd['FILENAME']:
            argd['FILENAME'] = default_file
        if plugin:
            msg = ['Plugin loaded by given name.']
            if argd['FILENAME'] == default_file:
                msg.append('Default file name used.')
            debug(' '.join(msg))
            return plugin

    extplugin = get_plugin_byext(argd['FILENAME'])
    if extplugin:
        # Determined plugin by file extension.
        debug('Plugin determined by file name/extension.')
        return extplugin

    # Fall back to default plugin, or user specified.
    plugin = None
    ftype = argd['FILETYPE'] or config.get('default_plugin', 'python')
    # Allow loading post-plugins by name when using --pluginconfig.
    plugin = get_plugin_byname(ftype, use_post=use_post)
    if plugin:
        debug('Plugin loaded {}.'.format(
            'by given name.' if argd['FILETYPE'] else 'by default'))
    return plugin


def do_post_plugins(fname, plugin):
    """ Handle all post-processing plugins.
        These plugins will be given the file name to work with.
        The plugin return values are not used.
        If the plugin raises pluginbase.SignalExit all processing will stop.
        Any other Exceptions are debug-printed, but processing continues.
        Returns: Number of errors encountered (can be used as an exit code)
        Arguments:
            fname   : The created file name.
            plugin  : The Plugin that was used to create the file.
    """
    errors = 0
    for post in plugins['post'].values():
        if plugin.ignore_post and (post.get_name() in plugin.ignore_post):
            skipmsg = 'Skipping post-plugin {} for {}.'
            debug(skipmsg.format(post.get_name(), plugin.get_name()))
            continue

        pluginret = try_post_plugin(post, plugin, fname)
        if pluginret == PluginReturn.fatal:
            return errors + 1
        errors += pluginret.value

    # Cancel deferred plugins if there were errors.
    if errors:
        if errors == 1:
            pluralerrs = 'was 1 error'
        else:
            pluralerrs = 'were {} errors'.format(errors)
        debug('There {}.'.format(pluralerrs))
        if plugins['deferred']:
            deflen = len(plugins['deferred'])
            plural = 'plugin' if deflen == 1 else 'plugins'
            debug('Cancelling {} deferred post-{}.'.format(deflen, plural))
        return errors

    # Defferred plugins.
    for deferred in plugins['deferred'].values():
        if (plugin.ignore_deferred and
                (deferred.get_name() in plugin.ignore_deferred)):
            skipmsg = 'Skipping deferred-plugin {} for {}.'
            debug(skipmsg.format(deferred.get_name(), plugin.get_name()))
            continue
        pluginret = try_post_plugin(deferred, plugin, fname)
        if pluginret == PluginReturn.fatal:
            return errors + 1
        errors += pluginret.value

    return errors


def find_config_file():
    """ Loads the defult config file. If no file is present, it will look
        for the distribution (example) file, and copy it to the default name.

    """
    mainfile = os.path.join(SCRIPTDIR, 'new.json')
    if os.path.exists(mainfile):
        return mainfile

    distfile = '{}.dist'.format(mainfile)
    if not os.path.exists(distfile):
        # No main file or dist, load_config will handle this error.
        debug('No distribution config file exists!')
        return mainfile

    try:
        debug('Copying dist config file to: {}'.format(mainfile))
        shutil.copyfile(distfile, mainfile)
    except EnvironmentError as ex:
        debug('Unable to copy dist config file: {} -> {}\n {}'.format(
            distfile,
            mainfile,
            ex))
    else:
        debug('Copied dist config file.')

    # Whether the file was copied or not load_config will handle it.
    return mainfile


def get_plugin_byext(name):
    """ Retrieves a plugin by file extension.
        Returns the plugin on success, or None on failure.
    """
    if not name:
        return None
    ext = os.path.splitext(name)[-1].lower()
    if not ext:
        return None

    for name in sorted(plugins['types']):
        plugin = plugins['types'][name]
        if ext in plugin.extensions:
            return plugin
    return None


def get_plugin_byname(name, use_post=False):
    """ Retrieves a plugin module by name or alias.
        Returns the plugin on success, or None on failure.
    """
    if not name:
        return None
    name = name.lower()
    for plugin in plugins['types'].values():
        names = (pname.lower() for pname in plugin.name)
        if name in names:
            return plugin

    # Try post plugins also.
    if use_post:
        postplugins = list(plugins['post'].values())
        postplugins.extend(list(plugins['deferred'].values()))
        for plugin in postplugins:
            if name == plugin.name.lower():
                return plugin
    # The plugin wasn't found.
    return None


def get_usage(indent=0):
    """ Get a usage and options from all plugins.
        Returns (usage_str, options_str).
    """
    usage, opts = [], []
    for plugin in plugins['types'].values():
        pluginusage = getattr(plugin, 'usage', None)
        if not pluginusage:
            continue
        elif not isinstance(pluginusage, dict):
            errmsg = 'Bad type for {} plugin usage: {}'
            debug(errmsg.format(plugin.get_name(), type(pluginusage)))
            continue
        pluginstrfmt = '{{script}} {} FILENAME [-d] [-D]'
        pluginstr = pluginstrfmt.format(plugin.get_name())
        for usageline in pluginusage.get('usage', []):
            usage.append(' '.join((pluginstr, usageline)))
        opts.extend(pluginusage.get('options', []))
    indention = ' ' * indent
    joiner = '\n{}'.format(indention)
    return (
        ''.join((indention, joiner.join(sorted(usage)))),
        ''.join((indention, joiner.join(sorted(opts)))))


def is_plugins_module(module):
    """ Returns True if the module appears to be a plugins module. """
    return (
        hasattr(module, 'exports') and
        isinstance(module.exports, (list, tuple)))


def is_py_file(path):
    """ Returns True if the given path looks like a python file name.
        Dunder names will return False (__init__.py is not included)
        The plugins module itself is skipped also.
    """
    return (
        path.endswith('.py') and
        (not path.startswith('__')) and
        (not path == 'pluginbase.py'))


def is_invalid_plugin(plugin):
    """ Determine whether a plugin has all the needed attributes.
        Returns a str (invalid reason) for invalid plugins.
        Returns None if it is a valid plugin.
    """
    if not hasattr(plugin, 'name'):
        return 'missing name attribute'

    if isinstance(plugin, Plugin):
        if not hasattr(plugin, 'extensions'):
            return 'missing extensions attribute'
        elif not hasattr(plugin, 'create'):
            return 'missing create function'
        return None
    elif isinstance(plugin, PostPlugin):
        if not hasattr(plugin, 'process'):
            return 'missing process function'
        return None

    return 'not a Plugin, PostPlugin, or DeferredPostPlugin'


def iter_py_files(path):
    """ Iterate over all python file names in the given path. """
    try:
        for path in [f for f in os.listdir(path) if is_py_file(f)]:
            yield path
    except EnvironmentError as exenv:
        debug('Error listing plugins: {}'.format(exenv))
    except Exception as ex:
        debug('Error iterating plugins: {}'.format(ex))


def list_plugins():
    """ Lists all plugins for the terminal. """
    # Normal Plugins (file-type)
    if plugins['types']:
        indent = 20
        aliaslbl = 'aliases'.rjust(indent)
        extlbl = 'extensions'.rjust(indent)
        print('\nFound {} file-type plugins:'.format(len(plugins['types'])))
        for pname in sorted(plugins['types']):
            plugin = plugins['types'][pname]
            print('    {}:'.format(pname))
            if len(plugin.name) > 1:
                print('{}: {}'.format(aliaslbl, ', '.join(plugin.name)))
            if plugin.extensions:
                extlist = ', '.join(plugin.extensions)
            else:
                extlist = 'None'
            print('{}: {}'.format(extlbl, extlist))

    # Do PostPlugin and DeferredPostPlugin
    posttypes = (
        ('post', 'post-processing'),
        ('deferred', 'deferred post-processing')
    )
    for ptype, pname in posttypes:
        if plugins[ptype]:
            postlen = len(plugins[ptype])
            plural = 'plugin' if postlen == 1 else 'plugins'
            print('\nFound {} {} {}:'.format(postlen, pname, plural))
            for pname in sorted(plugins[ptype]):
                plugin = plugins[ptype][pname]
                desc = plugin.get_desc().replace('\n', '\n        ')
                print('    {}:'.format(pname))
                print('        {}'.format(desc))


def load_config(section=None):
    """ Load global config, or a specific section. """
    configfile = find_config_file()

    config = {}
    try:
        with open(configfile, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        debug('No config file: {}'.format(configfile))
    except EnvironmentError as exread:
        debug('Unable to read config file: {}\n{}'.format(configfile, exread))
    except ValueError as exjson:
        debug('Invalid JSON config: {}\n{}'.format(configfile, exjson))
    except Exception as ex:
        debug('Error loading config: {}\n{}'.format(configfile, ex))
    if section:
        sectionconfig = config.get(section, {})
        if not sectionconfig:
            debug('No config for: {}'.format(section))
        else:
            config = sectionconfig
            debug('Loaded {} config from: {}'.format(section, configfile))
    elif config:
        # Loading gobal config.
        debug('Loaded config from: {}'.format(configfile))
    return config


def load_plugin_config(plugin):
    """ Load config file for a plugin instance.
        Sets plugin.config to a dict on success.
    """
    # Load global config if available.
    globalconfig = config.get('global', {})

    if not getattr(plugin, 'config_file', None):
        configfile = 'new.json'
        plugin.config_file = os.path.join(SCRIPTDIR, configfile)

    pluginconfig = {}
    try:
        with open(plugin.config_file, 'r') as f:
            pluginconfig = json.load(f)
    except FileNotFoundError:
        msg = 'No config file for {}: {}'
        debug(msg.format(plugin.get_name(), plugin.config_file))
    except EnvironmentError as exread:
        errmsg = 'Unable to open {} config: {}\n{}'
        debug(errmsg.format(plugin.get_name(), plugin.config_file, exread))
    except ValueError as exjson:
        errmsg = 'Error loading json from: {}\n{}'
        debug(errmsg.format(plugin.config_file, exjson))
    except Exception as ex:
        errmsg = 'Error loading plugin config: {}\n{}'
        debug(errmsg.format(plugin.config_file, ex))

    # Actual config is in {'<plugin_name>': {}}
    pluginconfig = pluginconfig.get(plugin.get_name(), {})
    if pluginconfig:
        loadmsg = 'Loaded {} config from: {}'
        debug(loadmsg.format(plugin.get_name(), plugin.config_file))
    else:
        errmsg = 'No config for {}: {}'
        debug(errmsg.format(plugin.get_name(), plugin.config_file))
    # Merge global config with plugin config.
    for k, v in globalconfig.items():
        if v and (not pluginconfig.get(k, None)):
            pluginconfig[k] = v

    plugin.config = pluginconfig


def load_plugins(plugindir):
    """ Loads all available plugins from a path.
        Returns a dict of
            {'types': {module: Plugin}, 'post': {module: PostPlugin}}
    """
    global plugins, config
    # Load general plugin config.
    config = load_config('plugins')

    debug('Loading plugins from: {}'.format(plugindir))
    tmp_plugins = {'types': {}, 'post': {}, 'deferred': {}}
    disabled_deferred = config.get('disabled_deferred', [])
    disabled_post = config.get('disabled_post', [])
    disabled_types = config.get('disabled_types', [])

    for modname in (os.path.splitext(p)[0] for p in iter_py_files(plugindir)):
        # debug('Importing: {}'.format(modname))
        try:
            module = import_module(modname)
            # Ensure that the module has a list of plugins to work with.
            if not is_plugins_module(module):
                debug('{} ({}) is not a valid plugin!'.format(modname, module))
                continue
            # debug('    {} ..imported.'.format(modname))
        except ImportError as eximp:
            # Bad plugin, cannot be imported.
            debug('Plugin failed: {}\n{}'.format(modname, eximp))
            continue
        try:
            for plugin in module.exports:
                # debug('    checking {}'.format(plugin))
                invalidreason = is_invalid_plugin(plugin)
                if invalidreason:
                    errmsg = 'Not a valid plugin {}: {}'
                    debug(errmsg.format(plugin, invalidreason))
                    continue
                try:
                    name = plugin.get_name()
                except (TypeError, ValueError) as exname:
                    debug_load_error('a', modname, plugin, exname)
                    continue
                else:
                    fullname = '{}.{}'.format(modname, name)

                if isinstance(plugin, Plugin):
                    if not name:
                        debug_missing('name', 'file-type', modname, plugin)
                        continue
                    # See if the plugin is disabled.
                    if name in disabled_types:
                        skipmsg = 'Skipping disabled type plugin: {}'
                        debug(skipmsg.format(fullname))
                        continue
                    elif name in tmp_plugins['types']:
                        debug('Conflicting Plugin: {}'.format(name))
                        continue
                    tmp_plugins['types'][name] = plugin
                    debug('Loaded: {} (Plugin)'.format(fullname))
                elif isinstance(plugin, DeferredPostPlugin):
                    if not name:
                        debug_missing('name', 'deferred', modname, plugin)
                        continue
                    if name in disabled_deferred:
                        skipmsg = 'Skipping disabled deferred-post plugin: {}'
                        debug(skipmsg.format(fullname))
                        continue
                    elif name in tmp_plugins['deferred']:
                        errmsg = 'Conflicting DeferredPostPlugin: {}'
                        debug(errmsg.format(name))
                        continue
                    tmp_plugins['deferred'][name] = plugin
                    debug('Loaded: {} (DeferredPostPlugin)'.format(fullname))
                elif isinstance(plugin, PostPlugin):
                    if not name:
                        debug_missing('name', 'post', modname, plugin)
                        continue
                    # See if the plugin is disabled.
                    if name in disabled_post:
                        skipmsg = 'Skipping disabled post plugin: {}'
                        debug(skipmsg.format(fullname))
                        continue
                    elif name in tmp_plugins['post']:
                        debug('Conflicting PostPlugin: {}'.format(name))
                        continue
                    tmp_plugins['post'][name] = plugin
                    debug('Loaded: {} (PostPlugin)'.format(fullname))
                else:
                    debug('\nNon-plugin type!: {}'.format(type(plugin)))
        except Exception as ex:
            print('\nError loading plugin: {}\n{}'.format(modname, ex))
    # Set module-level copy of plugins.
    plugins = tmp_plugins


def plugin_config_dump(plugin):
    """ Dump plugin config to stdout. """
    pluginname = plugin.get_name().title()
    if not getattr(plugin, 'config', None):
        print('\nNo config for: {}\n'.format(pluginname))
        return False

    configstr = json.dumps(plugin.config, sort_keys=True, indent=4)
    print('\nConfig for: {}\n'.format(pluginname))
    print(configstr)
    return True


def plugin_help(plugin):
    """ Show help for a plugin if available. """
    name = plugin.get_name()
    ver = getattr(plugin, 'version', '')
    if ver:
        name = '{} v. {}'.format(name, ver)

    usage = getattr(plugin, 'usage', '')
    if usage:
        print('\nHelp for {}:'.format(name))
        print(usage)
        return True

    # No real usage available, try getting a description instead.
    desc = plugin.get_desc()
    print('\nNo help available for {}.\n'.format(name))
    if desc:
        print('Description:')
        print(desc)
    else:
        print('(no description available)')
    return False


def plugin_print_status(plugin, msg, padlines=0):
    """ Print a status msg for a plugin instance.
        This function provides implementation of 'self.print_status' for
        Plugins and PostPlugins.
    """
    print('{}{}: {}'.format('\n' * padlines, plugin.get_name().ljust(15), msg))


def print_inplace(s):
    """ Overwrites the last printed line. """
    print('\033[2A\033[160D')
    print(s)


def save_config(config, section=None):
    """ Save config to global config file. """
    configfile = os.path.join(SCRIPTDIR, 'new.json')
    if section:
        existing = load_config(section)
        existing[section] = config
        writeconfig = existing
    else:
        writeconfig = config

    try:
        with open(configfile, 'w') as f:
            json.dump(writeconfig, f, indent=4, sort_keys=True)
    except (TypeError, ValueError) as exjson:
        debug('Invalid JSON config error: {}'.format(exjson))
    except EnvironmentError as exwrite:
        debug('Unable to write config: {}\n{}'.format(configfile, exwrite))
    except Exception as ex:
        debug('Error writing config: {}\n{}'.format(configfile, ex))
    else:
        # Success.
        return True
    # Failure.
    return False


def try_post_plugin(plugin, typeplugin, filename):
    """ Try running plugin.process(filename).
        Arguments:
            plugin      : Post or Deferred plugin to try running.
            typeplugin  : The original Plugin that created the content.
            filename    : The requested filename for file creation.
        Returns one of:
            PluginReturn.success (0)
            PluginReturn.error (1)
            PluginReturn.fatal (2)
    """
    try:
        plugin.process(typeplugin, filename)
    except SignalExit as exstop:
        if exstop.reason:
            errmsg = '\nFatal error in post-processing plugin \'{}\':\n{}'
            print(errmsg.format(plugin.name, exstop.reason))
        else:
            errmsg = '\nFatal error in post-processing plugin: \'{}\''
            print(errmsg.format(plugin.name))
        print('\nCancelling all post plugins.')
        return PluginReturn.fatal
    except Exception as ex:
        errmsg = '\nError in post-processing plugin \'{}\':\n{}'
        print(errmsg.format(plugin.name, ex))
        return PluginReturn.error
    return PluginReturn.success


class Plugin(object):

    """ Base for file-type plugins. """
    # (tuple)
    # Names/aliases for this plugin/filetype.
    # The proper name will be self.name[0].
    name = None

    # (tuple)
    # File extensions for this file type.
    # Default file extension is self.extensions[0].
    extensions = None

    # (str)
    # Description for this plugin.
    # When present, this overrides the default behaviour of using
    # the first line of self.create.__doc__.
    description = None

    # (str)
    # Version for this plugin.
    version = '0.0.1'

    # (bool)
    # Whether this plugin is allowed to create blank content.
    # Plugins such as the 'text' plugin might use this.
    # Otherwise, no content means an error occurred and no file is written.
    allow_blank = False

    # (set)
    # Names of deferred plugins that will be skipped when using this plugin.
    ignore_deferred = set()

    # (set)
    # Names of post plugins that will be skipped when using this plugin.
    ignore_post = set()

    # (list/tuple)
    # Usage string for this plugin when `new plugin -H` is used.
    usage = None

    # (function)
    # Internal use. Function to load config data into self.config.
    # This may be overridden.
    load_config = load_plugin_config

    def __init__(self, name=None, extensions=None):
        self._name = None
        self.name = name
        self.extensions = extensions
        # A usage string for this plugin.
        self.usage = None

    def _create(self, filename, args=None):
        """ This method is called for content creation, and is responsible
            for calling the plugin's create() method.
            It sets self.args so they are available in create() and afterwards.
            If no args were given then get_default_args() is used to grab them
            from config.
        """
        self.args = args if args else self.get_default_args()
        return self.create(filename)

    def create(self, filename):
        """ (unimplemented plugin description)

            This should return a string that is ready to be written to a file.
            It may raise an exception to signal that something went wrong.

            Arguments:
                filename  : The file name that will be written.
                            Plugins do not write the file, but the file name
                            may be useful information. The python plugin
                            uses it to create the main doc str.
        """
        raise NotImplementedError('create() must be implemented!')

    def debug(self, *args, **kwargs):
        """ Uses the debug() function, but includes the class name. """
        kargs = kwargs.copy()
        kargs.update({'parent': self, 'back': 2})
        return debug(*args, **kargs)

    def get_arg(self, index, default=None):
        """ Safely retrieve an argument by index.
            On failure (index error), return 'default'.
        """
        args = getattr(self, 'args', tuple())
        try:
            val = args[index]
        except IndexError:
            return default
        return val

    def get_default_args(self):
        """ Loads default args from config, if any are set.
            Returns a list of args on success, or [] on failure.
        """
        args = getattr(self, 'config', {}).get('default_args', [])
        if args:
            self.debug('Got default args: {}'.format(args))
        return args

    def get_desc(self):
        """ Get the description for this plugin.
            It uses the first line in create.__doc__ if self.description is
            not set. This is not the same as self.usage.
        """
        if self.description:
            return self.description

        docs = self.create.__doc__
        if docs:
            self.description = self.create.__doc__.split('\n')[0].strip()
        else:
            self.description = ''
        return self.description

    def get_name(self):
        """ Get the proper name for this plugin (no aliases). """
        if not hasattr(self, '_name'):
            self._name = None
        if not hasattr(self, 'name'):
            raise ValueError('Plugin has an empty name!')

        if self._name:
            return self._name

        if isinstance(self.name, str):
            self._name = self.name
            self.name = (self._name,)
        elif isinstance(self.name, (list, tuple)):
            if not self.name:
                # Empty name list!
                raise ValueError('Plugin has an empty name!')
            self._name = self.name[0]
        else:
            raise TypeError('Plugin.name is the wrong type!')

        return self._name

    def get_usage(self):
        """ Safely retrieve a usage string for the plugin, if any exists.
            Returns self.usage on success, or None on failure.
        """
        return getattr(self, 'usage', None)

    def has_arg(self, pattern, position=None):
        """ Determine if an argument was given using a regex pattern.
            If position is given it simply returns:
                re.search(pattern, args[position]) is not None
            If position is None then all args are searched.
            Returns True if any match, otherwise False.
        """
        args = getattr(self, 'args', tuple())
        if not args:
            self.debug('No args to check.')
            return False

        self.debug(
            'Checking for arg: (pattern {}) (position: {}) in {!r}'.format(
                pattern,
                position,
                args))
        if position is None:
            for a in args:
                if re.search(pattern, a) is not None:
                    return True
            return False
        try:
            exists = re.search(pattern, args[position]) is not None
        except IndexError:
            return False
        return exists

    def print_status(self, msg, padlines=0):
        """ Print a status message including the plugin name and file name
            if available.
        """
        return plugin_print_status(self, msg, padlines=padlines)


class PostPlugin(object):

    """ Base for post-processing plugins. """
    # (str)
    # A name for this post plugin. Alises are not needed.
    name = None
    # (str)
    # A version string for this post plugin.
    version = '0.0.1'
    # (str)
    # A description for this plugin. This is optional.
    # When not given, the first line of self.process.__doc__ is used.
    description = None
    # (function)
    # Internal use. This may be overridden to load config for this plugin.
    load_config = load_plugin_config

    def __init__(self, name=None):
        self.name = name

    def debug(self, *args, **kwargs):
        """ Uses the debug() function, but includes the class name. """
        kargs = kwargs.copy()
        kargs.update({'parent': self, 'back': 2})
        return debug(*args, **kargs)

    def get_desc(self):
        """ Get the description for this plugin.
            It uses the first line in process.__doc__ if self.description is
            not set.
        """
        if self.description:
            return self.description

        docs = self.process.__doc__
        if docs:
            self.description = self.process.__doc__.split('\n')[0].strip()
        else:
            self.description = ''
        return self.description

    def get_name(self):
        """ Get the name for this plugin.
            Returns a str. (empty str on failure)
        """
        return self.name if self.name else ''

    def print_status(self, msg, padlines=0):
        """ Print a status message including the plugin name and file name
            if available.
        """
        return plugin_print_status(self, msg, padlines=padlines)

    def process(self, plugin, filename):
        """ (unimplemented post-plugin description)

            This should accept an existing file name and do some processing.
            It may raise an exception to signal that something went wrong.

            Arguments:
                plugin    : The original Plugin that created the content.
                filename  : The requested file name for file creation.
        """
        raise NotImplementedError('process() must be overridden!')


class DeferredPostPlugin(PostPlugin):

    """ A post plugin that is 'deferred', meaning that this plugin will only
        run if all the others succeeded without an exception.
    """
    pass


class PluginReturn(Enum):

    """ Return values for try_post_plugin().
        These provide readable names for the return values, but can be used
        as integers (or exit codes) with '.value'.
    """
    success = 0
    error = 1
    fatal = 2


class SignalAction(Exception):

    """ An  exception to raise when the plugin.create() function is a success,
        but changes need to be made to the filename.
        Arguments:
            message   : A message about the action. Printed with no formatting
                        when 'content' is set.
                        Defaults to: 'No message provided.' when 'content' is
                        not set.
            filename  : The new file name to use.
            content   : Content for the new file. If this is not set an error
                        message is printed along with 'message', and the
                        program exits.

        If you raise a SignalAction like a normal Exception:
            raise SignalAction(mystring)
        ...then SignalAction.message is set to mystring.

    """

    def __init__(self, *args, message=None, filename=None, content=None):
        Exception.__init__(self, *args)
        self.message = message
        self.filename = filename
        self.content = content
        arglen = len(args)
        if args:
            arglen = len(args)
            if (not self.content) and (arglen > 2):
                self.content = args[2]
            if (not self.filename) and (arglen > 1):
                self.filename = args[1]
            if not self.message:
                self.message = args[0]

        if (not self.content) and (not self.message):
            self.message = 'No message was provided.'


class SignalExit(Exception):

    """ An exception to raise when a plugin wants to stop the rest of the
        plugins from running. In other words, stop and exit completely.
        The plugin may give a reason/message by initializing with a str as the
        first argument. The programs exit code can be changed by setting the
        optional 'code' argument.

        If 'code' is 0, no extra warnings are printed.
        The default exit code is 1.

        Example:
            raise plugins.SignalExit('Program was not installed!', code=2)
    """

    def __init__(self, *args, code=None):
        self.reason = args[0] if args else None
        self.code = 1 if code is None else code
