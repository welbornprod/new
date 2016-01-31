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

from docopt import docopt, DocoptExit, DocoptLanguageError

SCRIPTDIR = os.path.abspath(sys.path[0])
DEBUG = False
plugins = {'types': {}, 'post': {}, 'deferred': {}}
# Config is loaded in load_plugins()
config = {}

# Default version made available to all plugins when no config is set.
default_version = '0.0.1'


def config_dump():
    """ Dump config to stdout. """
    if not config:
        print('\nNo config found.\n')
        return False

    configstr = json.dumps(config, sort_keys=True, indent=4)
    print('\nConfig:\n')
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
    globalconfig = config.get('plugins', {}).get('global', {})
    default_file = globalconfig.get('default_filename', 'new_file')
    if argd['FILENAME'] in {'-', '--'}:
        # Occurs when no args are passed after the seperator: new plugin --
        raise DocoptExit()

    namedplugincls = get_plugin_byname(argd['FILENAME'], use_post=True)
    if namedplugincls:
        # Plugin name was mistaken for a file name (ambiguous docopt usage).
        # Use default file name since no file name was given.
        argd['FILENAME'] = default_file
        debug('Plugin loaded by name, using default file name.')
        return namedplugincls
    debug('get_plugin_byname({!r}) failed (FILENAME), trying PLUGIN.'.format(
        argd['FILENAME']
    ))
    if argd['PLUGIN']:
        plugincls = get_plugin_byname(argd['PLUGIN'], use_post=True)
        if plugincls:
            msg = ['Plugin loaded by given name.']
            if not argd['FILENAME']:
                argd['FILENAME'] = default_file
                msg.append('Default file name used.')
            debug(' '.join(msg))
            return plugincls
    debug('get_plugin_byname({!r}) failed (PLUGIN), trying extension.'.format(
        argd['PLUGIN']
    ))
    # No known plugin name in either FILENAME or PLUGIN,
    # Fix args to assume filename was passed.
    argd['FILENAME'] = argd['PLUGIN'] or argd['FILENAME']
    argd['PLUGIN'] = None
    extplugin = get_plugin_byext(argd['FILENAME'])
    if extplugin:
        # Determined plugin by file extension.
        debug('Plugin determined by file name/extension.')
        return extplugin
    debug('get_plugin_byext({!r}) (FILENAME) failed, trying PLUGIN.'.format(
        argd['FILENAME']
    ))

    # Fall back to default plugin, or user specified.
    # Allow loading post-plugins by name when using --pluginconfig.
    plugincls = get_plugin_byname(argd['PLUGIN'], use_post=True)
    if plugincls:
        debug('Plugin loaded by given name.')
        return plugincls
    return get_plugin_default()


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
    for postcls in plugins['post'].values():
        if plugin.ignore_post and (postcls.get_name() in plugin.ignore_post):
            skipmsg = 'Skipping post-plugin {} for {}.'
            debug(skipmsg.format(postcls.get_name(), plugin.get_name()))
            continue

        pluginret = try_post_plugin(postcls, plugin, fname)
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
    for deferredcls in plugins['deferred'].values():
        if (plugin.ignore_deferred and
                (deferredcls.get_name() in plugin.ignore_deferred)):
            skipmsg = 'Skipping deferred-plugin {} for {}.'
            debug(skipmsg.format(deferredcls.get_name(), plugin.get_name()))
            continue
        pluginret = try_post_plugin(deferredcls, plugin, fname)
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


def fix_author(s):
    """ Adds a dash before the author name if available, otherwise returns
        an empty string.
    """
    return '-{} '.format(s) if s else ''


def get_plugin_byext(name):
    """ Retrieves a plugin by file extension.
        Returns the plugin on success, or None on failure.
    """
    if not name:
        debug('No name given!')
        return None
    ext = os.path.splitext(name)[-1].lower()
    if not ext:
        return None

    for name in sorted(plugins['types']):
        plugincls = plugins['types'][name]
        if ext in plugincls.extensions:
            return plugincls
    return None


def get_plugin_byname(name, use_post=False):
    """ Retrieves a plugin module by name or alias.
        Returns the plugin on success, or None on failure.
    """
    if not name:
        debug('No name given!')
        return None
    name = name.lower()
    for plugincls in plugins['types'].values():
        if name in {pname.lower() for pname in plugincls.name}:
            return plugincls

    # Try post plugins also.
    if use_post:
        postplugins = list(plugins['post'].values())
        postplugins.extend(list(plugins['deferred'].values()))
        for plugincls in postplugins:
            if name == plugincls.get_name().lower():
                return plugincls
    # The plugin wasn't found.
    return None


def get_plugin_default(_name=None):
    """ Return the default plugin.
        The `_name` argument is for testing purposes only.
    """
    globalconfig = config.get('plugins', {}).get('global', {})
    name = globalconfig.get('default_plugin', _name or 'python')
    return get_plugin_byname(name)


def get_usage(indent=0):
    """ Get a usage and options from all plugins.
        Returns (usage_str, options_str).
    """
    usage, opts = [], []
    for plugincls in plugins['types'].values():
        pluginusage = getattr(plugincls, 'usage', None)
        if not pluginusage:
            continue
        elif not isinstance(pluginusage, dict):
            errmsg = 'Bad type for {} plugin usage: {}'
            debug(errmsg.format(plugincls.get_name(), type(pluginusage)))
            continue
        pluginstrfmt = '{{script}} {} FILENAME [-d] [-D]'
        pluginstr = pluginstrfmt.format(plugincls.get_name())
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


def is_invalid_plugin(plugincls):
    """ Determine whether a plugin has all the needed attributes.
        Returns a str (invalid reason) for invalid plugins.
        Returns None if it is a valid plugin.
    """
    if not hasattr(plugincls, 'name'):
        return 'missing name attribute'

    if issubclass(plugincls, Plugin):
        if not hasattr(plugincls, 'extensions'):
            return 'missing extensions attribute'
        elif not hasattr(plugincls, 'create'):
            return 'missing create function'
        return None
    elif issubclass(plugincls, PostPlugin):
        if not hasattr(plugincls, 'process'):
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
    if section:
        preloaded = config.get(section, {})
        if preloaded:
            debug('Retrieved config for {}.'.format(section))
            return preloaded

    configfile = find_config_file()
    conf = load_config_file(configfile)
    if section:
        sectionconfig = conf.get(section, {})
        if not sectionconfig:
            debug('No config for: {}'.format(section))
        else:
            conf = sectionconfig
            debug('Loaded {} config from: {}'.format(section, configfile))
    elif conf:
        # Loading gobal config.
        debug('Loaded config from: {}'.format(configfile))
    return conf


def load_config_file(filename, section=None):
    """ Load config from a JSON file. Expects a top-level dict object.
        If `section` is given, then loadedconfig.get(section, {}) is returned
    """
    conf = {}
    try:
        with open(filename, 'r') as f:
            conf = json.load(f)
    except FileNotFoundError:
        debug('No config file: {}'.format(filename))
    except EnvironmentError as exread:
        debug('Unable to read config file: {}\n{}'.format(filename, exread))
    except ValueError as exjson:
        # When loading the main config, JSON errors warrant a message.
        reporter = print if not section else debug
        reporter('Invalid JSON config: {}\n{}'.format(filename, exjson))
    except Exception as ex:
        debug('Error loading config: {}\n{}'.format(filename, ex))

    if section:
        return conf.get(section, {})
    return conf


def load_module(modulename):
    """ Load a single plugin module by name.
        Non-plugin modules raise ImportError.
        Return the module instance, or raises ImportError.
    """
    module = import_module('.{}'.format(modulename), package='plugins')
    # Ensure that the module has a list of plugins to work with.
    if not is_plugins_module(module):
        debug('{} ({}) is not a valid plugin!'.format(modulename, module))
        raise ImportError('Not a valid plugin module.')
    return module


def load_module_plugins(module):  # noqa
    """ Load all plugin instances from a plugin module.
        The module must have an 'exports' attribute that is a tuple of
        plugin instances.

        Returns a dict of: {
            'types': {name: instance},
            'post': {name: instance},
            'deferred': {name: instance}
        }
    """
    pluginsconfig = config.get('plugins', {})
    disabled_deferred = pluginsconfig.get('disabled_deferred', [])
    disabled_post = pluginsconfig.get('disabled_post', [])
    disabled_types = pluginsconfig.get('disabled_types', [])

    tmp_plugins = {'types': {}, 'post': {}, 'deferred': {}}
    modname = getattr(module, '__name__', 'unknown_module_name')

    for plugincls in module.exports:
        # debug('    checking {}'.format(plugin))
        invalidreason = is_invalid_plugin(plugincls)
        if invalidreason:
            errmsg = 'Not a valid plugin {}: {}'
            debug(errmsg.format(plugincls.__name__, invalidreason))
            continue
        try:
            name = plugincls.get_name()
        except (TypeError, ValueError) as exname:
            debug_load_error('a', modname, plugincls, exname)
            continue
        else:
            fullname = '{}.{}'.format(modname, name)

        if issubclass(plugincls, Plugin):
            if not name:
                debug_missing('name', 'file-type', modname, plugincls)
                continue
            # See if the plugin is disabled.
            if name in disabled_types:
                skipmsg = 'Skipping disabled type plugin: {}'
                debug(skipmsg.format(fullname))
                continue
            elif name in tmp_plugins['types']:
                debug('Conflicting Plugin: {}'.format(name))
                continue
            tmp_plugins['types'][name] = plugincls
            debug('Loaded: {} (Plugin)'.format(fullname))
        elif issubclass(plugincls, DeferredPostPlugin):
            if not name:
                debug_missing('name', 'deferred', modname, plugincls)
                continue
            if name in disabled_deferred:
                skipmsg = 'Skipping disabled deferred-post plugin: {}'
                debug(skipmsg.format(fullname))
                continue
            elif name in tmp_plugins['deferred']:
                errmsg = 'Conflicting DeferredPostPlugin: {}'
                debug(errmsg.format(name))
                continue
            tmp_plugins['deferred'][name] = plugincls
            debug('Loaded: {} (DeferredPostPlugin)'.format(fullname))
        elif issubclass(plugincls, PostPlugin):
            if not name:
                debug_missing('name', 'post', modname, plugincls)
                continue
            # See if the plugin is disabled.
            if name in disabled_post:
                skipmsg = 'Skipping disabled post plugin: {}'
                debug(skipmsg.format(fullname))
                continue
            elif name in tmp_plugins['post']:
                debug('Conflicting PostPlugin: {}'.format(name))
                continue
            tmp_plugins['post'][name] = plugincls
            debug('Loaded: {} (PostPlugin)'.format(fullname))
        else:
            debug('\nNon-plugin type!: {}'.format(plugincls.__name__))
    return tmp_plugins


def load_plugin(modulename, pluginname):
    """ Load a plugin on demand by module name and plugin name.

        Raises ValueError if the module cannot be imported, or the plugin
        does not exist, or any other error while loading plugins.

        Returns the Plugin instance on success.
    """
    try:
        module = load_module(modulename)
    except ImportError as eximp:
        debug('Failed to load module: {}\n  {}'.format(modulename, eximp))
        raise ValueError(str(eximp))

    try:
        plugins = load_module_plugins(module)
    except Exception as ex:
        debug('Failed to load module plugins: {}\n  {}'.format(
            modulename,
            ex))
        raise ValueError(str(ex))

    for ptype, pinfo in plugins.items():
        for name, plugincls in pinfo.items():
            if name == pluginname:
                return plugincls

    raise ValueError(
        'Cannot find the \'{}\' plugin in the \'{}\' module.'.format(
            pluginname,
            modulename))


def load_plugins(plugindir):
    """ Loads all available plugins from a path.
        Returns a dict of
            {'types': {module: Plugin}, 'post': {module: PostPlugin}}
    """
    global plugins, config
    # Load general plugin config.
    config = load_config()

    debug('Loading plugins from: {}'.format(plugindir))
    tmp_plugins = {'types': {}, 'post': {}, 'deferred': {}}

    for modname in (os.path.splitext(p)[0] for p in iter_py_files(plugindir)):
        try:
            module = load_module(modname)
        except ImportError as eximp:
            # Bad plugin, cannot be imported.
            debug('Plugin failed: {}\n{}'.format(modname, eximp))
            continue
        try:
            moduleplugins = load_module_plugins(module)
            for ptype in ('types', 'post', 'deferred'):
                tmp_plugins[ptype].update(moduleplugins[ptype])
        except Exception as ex:
            print('\nError loading plugin: {}\n{}'.format(modname, ex))

    # Set module-level copy of plugins.
    plugins = tmp_plugins


def print_err(*args, **kwargs):
    """ Wrapper for print() that uses sys.stderr by default. """
    if kwargs.get('file', None) is None:
        kwargs['file'] = sys.stderr
    print(*args, **kwargs)


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


def try_post_plugin(plugincls, typeplugin, filename):
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
        plugin = plugincls()
    except Exception as ex:
        print_err('Failed to load post plugin: {}\n{}'.format(
            plugincls.__name__,
            getattr(plugincls, 'get_name', lambda: 'unknown name')(),
            ex
        ))
        return PluginReturn.fatal

    try:
        plugin.process(typeplugin, filename)
    except SignalExit as exstop:
        if exstop.reason:
            errmsg = '\nFatal error in post-processing plugin \'{}\':\n{}'
            print_err(errmsg.format(plugin.name, exstop.reason))
        else:
            errmsg = '\nFatal error in post-processing plugin: \'{}\''
            print_err(errmsg.format(plugin.name))
        print_err('\nCancelling all post plugins.')
        return PluginReturn.fatal
    except Exception as ex:
        print_err('\nError in post-processing plugin \'{}\':\n{}'.format(
            plugin.get_name(),
            ex))
        return PluginReturn.error
    return PluginReturn.success


class PluginBase(object):
    """ Base for all plugins. Used to implement common methods that don't
        depend on the plugin type.
    """
    # (str)
    # Description for this plugin.
    # When present, this overrides the default behaviour of using
    # the first line of self.create.__doc__.
    description = None

    # (tuple) - Plugin
    #     Plugin: Names/aliases for this plugin/filetype.
    #             The proper name will be self.name[0].
    # (str)   - PostPlugin
    # PostPlugin: The name for this plugin.
    name = None

    # (list/tuple)
    # Usage string for this plugin when `new plugin -H` is used.
    usage = None

    # (str)
    # Version for this plugin.
    version = '0.0.1'

    # Set by command-line args, or tests.
    dryrun = False

    # Set by self.load_config()
    config = {}

    # Set by _setup(), before create() or run() is called.
    args = tuple()
    # Docopt args if self.docopt is True, set in _setup().
    argd = {}

    docopt = False

    def _setup(self, args=None):
        """ Perform any plugin setup before using it. """

        # Handle -h and -v before docopt, for a better new-style plugin msg.
        if ('-h' in args) or ('--help' in args):
            self.help()
            raise SignalExit(code=0)
        elif ('-v' in args) or ('--version' in args):
            vers = getattr(self, 'version', None)
            verstr = 'v. {}'.format(vers) if vers else '(no version set)'
            print(' '.join(('New:', self.get_name(), verstr)))
            raise SignalExit(code=0)

        # Fill in default args from config.
        self.args = args or self.get_default_args()

        if self.usage and self.docopt:
            try:
                self.argd = docopt(
                    self.usage,
                    self.args,
                    version=getattr(self, 'version', None))
            except DocoptExit as ex:
                pname = self.get_name()
                raise SignalExit(
                    str(ex).replace(pname, 'new {} --'.format(pname)),
                    code=1)
            except DocoptLanguageError as ex:
                raise SignalExit(
                    'Plugin usage string error in {} plugin: {}'.format(
                        self.get_name(),
                        ex),
                    code=1)

        else:
            # No docopt, but flag arguments will be marked with True if given.
            self.argd = {a: True for a in self.args if a.startswith('-')}

        self.debug('args: {!r}'.format(', '.join(self.args)))
        self.debug('argd: {!r}'.format(
            ', '.join(
                '{}: {}'.format(k, v) for k, v in self.argd.items()
            )
        ))

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

    @classmethod
    def get_desc(cls):
        """ Get the description for this plugin.
            It uses the first line in create.__doc__ if self.description is
            not set. This is not the same as self.usage.
        """
        if cls.description:
            return cls.description

        mainfunc = getattr(cls, 'create', getattr(cls, 'process', None))
        if mainfunc is None:
            cls.description = ''
            return cls.description

        docs = mainfunc.__doc__
        if docs:
            cls.description = docs.split('\n')[0].strip()
        else:
            cls.description = ''
        return cls.description

    @classmethod
    def get_name(cls):
        """ Get the proper name for this plugin (no aliases). """
        if issubclass(cls, PostPlugin):
            return cls.name or ''

        # Grab single name from names/aliases in Plugins.
        if not hasattr(cls, '_name'):
            cls._name = None
        if not hasattr(cls, 'name'):
            raise ValueError('Plugin has an empty name!')

        if cls._name:
            return cls._name

        if isinstance(cls.name, str):
            cls._name = cls.name
            cls.name = (cls._name,)
        elif isinstance(cls.name, (list, tuple)):
            if not cls.name:
                # Empty name list!
                raise ValueError('Plugin has an empty name!')
            cls._name = cls.name[0]
        else:
            raise TypeError('Plugin.name is the wrong type!')

        return cls._name

    @classmethod
    def get_usage(cls):
        """ Safely retrieve a usage string for the plugin, if any exists.
            Returns self.usage on success, or None on failure.
        """
        return getattr(cls, 'usage', None)

    def config_dump(self):
        """ Dump plugin config to stdout. """
        pluginname = self.get_name().title()
        if not getattr(self, 'config', None):
            print('\nNo config for: {}\n'.format(pluginname))
            return False

        configstr = json.dumps(self.config, sort_keys=True, indent=4)
        print('\nConfig for: {}\n'.format(pluginname))
        print(configstr)
        return True

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
                try:
                    if re.search(pattern, a) is not None:
                        return True
                except re.error as ex:
                    raise ValueError('Bad argument pattern: {}\n{}'.format(
                        a,
                        ex))
            return False
        try:
            exists = re.search(pattern, args[position]) is not None
        except IndexError:
            return False
        except re.error as ex:
            raise ValueError('Bad argument pattern: {}\n{}'.format(
                a,
                ex))

        return exists

    def has_args(self, *args):
        """ Convenient function to check for short and long options.
            Example:
                if self.has_args('-s', '--short'):
                    print('s')

            Arguments:
                args  : One or more arguments to test for.
        """
        if not args:
            return False
        argpats = '|'.join('({})'.format(s) for s in args)
        return self.has_arg('^({})$'.format(argpats))

    def help(self):
        """ Show help for a plugin if available. """
        name = self.get_name()
        ver = getattr(self, 'version', '')
        if ver:
            versionstr = '{} v. {}'.format(name, ver)

        usage = getattr(self, 'usage', '')
        if usage:
            print('\nHelp for New plugin, {}:'.format(versionstr))
            nameindent = '    {}'.format(name)
            print(usage.replace(nameindent, '    new {} --'.format(name)))
            return True

        # No real usage available, try getting a description instead.
        desc = self.get_desc()
        print('\nNo help available for {}.\n'.format(versionstr))
        if desc:
            print('Description:')
            print(desc)
        else:
            print('(no description available)')
        return False

    def load_config(self):
        """ Load config file for a plugin instance.
            Sets self.config to a dict on success.
        """
        plugin_configfile = getattr(self, 'config_file', None)
        pluginconfig = {}
        # Load plugin's file if available, otherwise the global file is used.
        if plugin_configfile:
            pluginconfig = load_config_file(
                plugin_configfile,
                section=self.get_name())
        else:
            # Use global file for config.
            # Actual config is in {'<plugin_name>': {}}
            pluginconfig = config.get(self.get_name(), {})
            self.debug(
                'No config file for {n}, {globstat} global config.'.format(
                    n=self.get_name(),
                    globstat='using' if pluginconfig else 'no'
                )
            )

        if pluginconfig:
            self.debug('Loaded config from: {}'.format(
                plugin_configfile or 'global config'
            ))

        globalconfig = config.get('plugins', {}).get('global', {})
        # Merge global config with plugin config.
        for k, v in globalconfig.items():
            if v and (not pluginconfig.get(k, None)):
                pluginconfig[k] = v

        self.config = pluginconfig

    def pop_args(self, *args):
        """ Safely removes any occurrence of an argument from self.args.
            This will not error on non-existing args, use self.args.pop/remove
            for that.

            Arguments:
                args  : One or more arguments to remove.
        """
        for a in args:
            while self.args:
                try:
                    self.args.remove(a)
                except ValueError:
                    # Arg does not exist anymore (possibly never did).
                    break

    def print_err(self, msg, padlines=0, **kwargs):
        """ Print an error msg for a plugin instance.
            This function provides implementation of 'self.print_err' for
            Plugins and PostPlugins.
        """
        print(
            '{}{} Error: {}'.format(
                '\n' * padlines,
                self.get_name().ljust(15),
                msg
            ),
            **kwargs
        )

    def print_status(self, msg, end='n', padlines=0, **kwargs):
        """ Print a status msg for a plugin instance.
            This function provides implementation of 'self.print_status' for
            Plugins and PostPlugins.
        """
        print(
            '{}{}: {}'.format(
                '\n' * padlines,
                self.get_name().ljust(15),
                msg
            ),
            **kwargs
        )


class Plugin(PluginBase):

    """ Base for file-type plugins. """
    # (tuple)
    # File extensions for this file type.
    # Default file extension is self.extensions[0].
    extensions = None

    # (bool)
    # Whether this plugin is allowed to create blank content.
    # Plugins such as the 'text' plugin might use this.
    # Otherwise, no content means an error occurred and no file is written.
    allow_blank = False

    # (bool)
    # Whether a custom extension is allowed with this plugin.
    # The default extension is used when no user extension is given,
    # but if the user provides an extension then use it.
    any_extension = False

    # (set)
    # Names of deferred plugins that will be skipped when using this plugin.
    ignore_deferred = set()

    # (set)
    # Names of post plugins that will be skipped when using this plugin.
    ignore_post = set()

    def __init__(self, name=None, extensions=None):
        self._name = None
        self.name = name
        self.extensions = extensions
        # A usage string for this plugin.
        self.usage = None

    def _create(self, filename, args=None):
        """ This method is called for content creation, and is responsible
            for calling the plugin's create() method.
            It sets self.args so they are available in create() and
            afterwards.
            If no args were given then get_default_args() is used to grab them
            from config.
        """
        self._setup(args=args)
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


class PostPlugin(PluginBase):

    """ Base for post-processing plugins. """

    def __init__(self, name=None):
        self.name = name

    def process(self, plugin, filename):
        """ (unimplemented post-plugin description)

            This should accept an existing file name and do some processing.
            It may raise an exception to signal that something went wrong.

            Arguments:
                plugin    : The original Plugin that created the content.
                filename  : The requested file name for file creation.
        """
        raise NotImplementedError('process() must be overridden!')

    def _run(self, args=None):
        """ This function performs any plugin setup, and then calls the actual
            run() method, so that New takes care of all setup, and plugins
            only need to implement run().
        """
        self._setup(args=args)
        return self.run()

    def run(self):
        """ Run this post-processing plugin as a command. """
        # Implement the run() method to use them as commands!
        raise NotImplementedError('This plugin is not runnable.')


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
