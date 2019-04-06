New
===

**New** dynamically creates new files from templates.
It's a simple command capable of creating several types of files, mainly
focusing on source files (executable scripts and small binary projects).

There are several post-processing plugins that automatically modify the file
after it is created, such as running `chmod +x` (the `chmodx` plugin),
or opening it in your editor (the `open` plugin).
Also, information can be dynamically added to the file during creation
(like a date/time, author).

A template can be automatically chosen based on the new file's extension, or
you can explicitly use the plugin name to decide.
A default template can be set, so typing a file name without the extension
automatically uses the default template/plugin. New templates can be added
easily by dropping a `.py` file in the `./plugins` folder and subclassing
`plugins.Plugin`. They only need the `name` and `extensions` attribute, and
a method with the signature `create(self, filename)` which returns a string
ready to be written to disk. See: [plugin modules](#plugin-modules)

Usage:
------

```
    Usage:
        new --customhelp [-D]
        new (-c | -h | -v | -p) [-D] [-P]
        new FILENAME... [-d | -O] [-D] [-P] [-o] [-x]
        new PLUGIN (-C | -H) [-D] [-P]
        new PLUGIN [-D] [-P]
        new PLUGIN FILENAME... [-d | -O] [-D] [-P] [-o] [-x]

    Options:
        ARGS               : Plugin-specific args.
                             Use -H for plugin-specific help.
                             Simply using '--' is enough to run post-plugins
                             as commands with no args.
        PLUGIN             : Plugin name to use (like bash, python, etc.)
                             Defaults to: python (unless set in config)
        FILENAME           : File name for the new file.
                             Multiple files can be created.
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
        -P,--debugplugin   : Show more plugin-debugging info.
        -p,--plugins       : List all available plugins.
        -x,--executable    : Force the chmodx plugin to run, to make the file
                             executable. This is for plugin types that
                             normally ignore the chmodx plugin.
        -v,--version       : Show version.

    Plugin arguments must follow a bare -- argument.
```

Example Usage:
--------------

Creating a basic program using the python plugin:

```
new myscript.py
```

Creating the same file when the default plugin is set to `python`:

```
new myscript
```

Creating a new directory and html file using the html plugin:

```
new myproject/myfile.html
```


Passing arguments to the python plugin to list its templates:

```
new myfile.py -- -t
```

Config:
-------

Configuration is done using JSON. There is a main configuration file called
`new.json` where all config lives. Each plugin may also handle config
on it's own.

Config Options:
---------------

```javascript
{
    // Each plugin has a top-level key (it's name).
    // A plugin may also provide a `config_file` attribute to load JSON from.
    "open": {

        // The open plugin allows you to set which editor you would like to use.
        "editor": "atom"
    },

    // The "plugins" key is config for plugin loading.
    "plugins" : {

        // All plugins inherit options from global if not set already.
        "global": {
            "author": "cjwelborn",

            // Some plugins provide a default version number in their templates.
            "default_version": "0.0.1"
        },

        // Default file name to use when only a plugin name is given.
        // The proper extension is added automatically.
        "default_filename": "new_file",

        // Default plugin to use when no plugin name or extension is given.
        "default_plugin": "text",

        // Names of DeferredPost plugins that will be ignored on every run.
        "disabled_deferred": [],

        // Names of PostPlugins that will be ignored on every run.
        "disabled_post": [],

        // Names of Plugins (template types) that will be ignored on every run.
        "disabled_types": []
    },

    "python": {

        // A default python template to use when none is specified.
        "template": "docopt"
    }
}
```

Plugin Modules:
---------------

The minimum requirements for a plugin module are that it must be located in
the `./plugins` directory, and must contain a module-level attribute called
`exports` which is a `tuple` or `list` of Plugin subclasses.

Example plugin module:
----------------------

```python

from plugins import Plugin
class HelloPlugin(Plugin):
    # These are class attributes.
    # File type plugins can have several names/aliases.
    # The first one is it's "official" name, but any can be used from
    # the command line.
    name = ('hello', 'tmp')
    extensions = ('.tmp',)
    # These are not required for the plugin to work:
    version = '0.0.1'
    description = 'Creates a temporary file.'

    # Parse arguments with Docopt
    docopt = True
    usage = """
    Usage:
        hello [CONTENT]

    Options:
        CONTENT  : Content for temporary file.
    """

    def __init__(self):
        # __init__ is not required, but plugin config can be automatically
        # loaded from new.json by calling self.load_config() here.
        self.load_config()

    def create(self, filename):
        """ This will be the description if no self.description is available.
            Only the first line is used, so that actual doc strings can be
            used for development.
        """
        # self.config, self.argv, and self.argd are made available.

        # This will use the first arg if available, but fall back to config
        # (from new.json), and then finally use 'Hello World' if neither of
        # those are set.
        return self.argd['CONTENT'] or self.config.get('msg', 'Hello World')

# This is how New knows which plugins to load.
# The plugin will be initialized once, when it is needed.
exports = (HelloPlugin, )
```

This example plugin can be used in three different ways:
```bash

# Explicit, by name.
new hello myfile

# Automatic, by file extension.
new myfile.tmp

# Explicit, using default file name.
new hello
```

Passing arguments to the plugin itself:
```
# Using the argument handling.
new myfile.tmp -- "My content."

# Printing help for this plugin.
new hello -- -h
new hello -H
# Printing the version for this plugin.
new hello -- -v
```

PluginBase:
-----------

`PluginBase` holds all the common methods used by the various plugin types.
It allows all plugins to automatically handle arguments, help/version args,
and sets up attributes and helper methods so writing a new plugin doesn't
require so much boilerplate.

You shouldn't subclass `PluginBase` unless you are working on New. File type
and post-processing plugins inherit from `Plugin` or `PostPlugin`.

Plugin:
------------

`Plugin` must be subclassed to create a new file type plugin.
These plugins are responsible for creating content and returning it.
A basic plugin would return a string from it's `create` method, but they may
also raise a `plugins.SignalAction` to change the file name being created.
All attributes and methods are documented in the source.

Post Plugins:
-------------

PostPlugins run after the file is created. They receive the `Plugin` instance
that was used, and the file name, and can decide whether more processing is
needed. Normal errors are printed but skipped (they will cause DeferredPlugins
to be aborted though).
A plugin can cause the program to abort if it raises a `plugins.SignalExit`.
The load/run order of PostPlugins may vary.

Deferred Plugins:
-----------------

DeferredPlugins are the same as PostPlugins, except they will only run if
all PostPlugins succeeded (no normal errors, or SignalExit() errors). They are
meant to run last. The `open` plugin is the only DeferredPlugin right now.
The load/run order of DeferredPlugins may vary.


Notes:
------

Look in the `./plugins` directory for examples. Most plugins are fairly
simple.

The Python and Html/JQuery plugins are a little messy because they were
basically copied and adapted from older 'newpython.py' and 'newhtml.py'
scripts. They serve as an example of plugins that do more than one thing.

The `MakefilePost` (automakefile) plugin is an example of a `PostPlugin` that
only acts on certain file types (creates a working `makefile` for new C/C++
files).

Disclaimer:
-----------

This program was designed to create small templates, and is not meant to
replace tools like [cargo](https://crates.io) or
[django-admin](http://djangoproject.com).

Some of the templates are based on my coding style. I am working on a way to
make them more flexible (without enforcing my own preferences on users).
There are templates for languages that I'm not very good with,
or don't even use (php).
If you see any errors feel free to let me know.


Screenshot:
-----------

![New Screenshot](http://welbornprod.com/dl/static/media/img/new-example.png)

This is an example of New's output when using the python plugin, which is set
to use the docopt template by default.

The content was created, written to disk, made executable, and then opened with
one command.
