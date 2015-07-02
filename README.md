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
    new (-c | -h | -v | -p) [-D]
    new PLUGIN (-C | -H) [-D]
    new FILENAME [-d] [-D]
    new FILENAME -- ARGS... [-d] [-D]
    new PLUGIN FILENAME [-d] [-D]
    new PLUGIN FILENAME -- ARGS... [-d] [-D]

Options:
    ARGS               : Plugin-specific args.
                         Use -H for plugin-specific help.
    PLUGIN             : Plugin name to use (like bash, python, etc.)
                         Defaults to: text (unless set in config)
    FILENAME           : File name for the new file.
    -c,--config        : Print global config and exit.
    -C,--pluginconfig  : Print plugin config and exit.
    -d,--dryrun        : Don't write anything. Print to stdout instead.
    -D,--debug         : Show more debugging info.
    -H,--pluginhelp    : Show plugin help.
    -h,--help          : Show this help message.
    -p,--plugins       : List all available plugins.
    -v,--version       : Show version.

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
new myfile.py -- t
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
`exports` which is a `tuple` or `list` of Plugin instances.

Example plugin module:
----------------------

```python
from plugins import Plugin
class HelloPlugin(Plugin):
    def __init__(self):
        self.name = ('hello',)
        self.extensions = ('.tmp',)

    def create(self, filename):
        return 'Hello World'

exports = (HelloPlugin(),)
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

Plugin Base:
------------

`Plugin` must be subclassed to create a new file type plugin.
These plugins are responsible for creating content and returning it.
All attributes and methods are documented.


Post Plugins:
-------------

PostPlugins run after the file is created. Normal errors are printed but
skipped. Normal errors will cause DeferredPlugins to be aborted.
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

Look in the `./plugins` directory for examples. Most plugins are fairly simple.

The Python and Html/JQuery plugins are a little messy because they were
basically copied and adapted from older 'newpython.py' and 'newhtml.py'
scripts. They serve as an example of plugins that do more than one thing.

The `MakefilePost` (automakefile) plugin is an example of a `PostPlugin` that
only acts on certain file types.

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
