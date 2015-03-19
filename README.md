New
===

**New** dynamically creates new files from templates.
It's a simple command capable of creating several types of files.
I know this been done before.

Plugins can be created to modify the file after it has been created,
such as running `chmod +x` (the `chmodx` plugin), or opening it automatically
after creation (the `open` plugin). Also, information can be dynamically added
to the file during creation (like a date/time).

Templates/plugins can be invoked by name and may have their own options.
A template can be automatically chosen based on the new file's extension.
A default template can be set, so typing a file name without the extension
automatically uses the default template/plugin. New templates can be added
easily by dropping a `.py` file in the `./plugins` folder and subclassing
`plugins.Plugin`. They only need the `name` and `extensions` attribute, and
a method with the signature `create(self, filename)`.

Usage:
------

```
Usage:
    new -c | -h | -v | -p [-D]
    new FILETYPE (-C | -H) [-D]
    new FILENAME [-d] [-D]
    new FILETYPE FILENAME [-d] [-D]
    new FILETYPE FILENAME ARGS... [-d] [-D]

Options:
    ARGS               : Plugin-specific args.
    FILETYPE           : Type of file to create.
                         Defaults to: python
    FILENAME           : File name for the new file.
    -c,--config        : Dump global config.
    -C,--pluginconfig  : Dump plugin config.
    -d,--dryrun        : Show what would be written, don't write anything.
    -D,--debug         : Show more debugging info.
    -H,--HELP          : Show plugin help.
    -h,--help          : Show this help message.
    -p,--plugins       : List all available plugins.
    -v,--version       : Show version.
 ```

Example Usage:
--------------

Creating a file called `myscript.py` using the python plugin:
```
new py myscript
```

Creating the same file when the default plugin is set to `python`:
```
new myscript
```

Creating a new directory and html file:
```
new html myproject/myfile.html
```

Using the file extension is optional. When not given, the extension will
default to whatever the plugin has defined for the `extensions` attribute.

You can omit the plugin name if you do add the extension.
This would create a new file using the `bash` plugin:
```
new myscript.sh
```


Config:
-------

Configuration is done using JSON. There is a main configuration file called
`new.json` where all config lives. Each plugin may also handle loading config
on it's own.

Config Options:
---------------

```javascript
{
    // Plugin config belongs under a key with the plugin name.
    "open": {
        // The open plugin allows you to set which editor you would like to use.
        "editor": "subl"
    },

    "plugins" : {
        // All plugins inherit options from global if not set already.
        "global": {
            "author": "cjwelborn"
        },
        // Default file name to use when only a plugin name is given.
        "default_filename": "new_file",
        // Default plugin to use when no plugin name or extension is given.
        "default_plugin": "python",
        // Names of DeferredPost plugins that will be ignored on every run.
        "disabled_deferred": [],
        // Names of PostPlugins that will be ignored on every run.
        "disabled_post": [],
        // Names of Plugins (template types) that will be ignored on every run.
        "disabled_types": []
    },
    "python": {
        // The python plugin allows a default version string for new files.
        "version": "0.0.1",
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

This must be subclassed to create a new plugin. Regular plugins are responsible
for creating content and returning it. All attributes and methods are
documented.


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

