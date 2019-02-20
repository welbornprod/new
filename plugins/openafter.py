""" Open post-processing plugin for New.
    Opens files after they are created.
    -Christopher Welborn 12-25-14
"""
import os
import subprocess

from plugins import DeferredPostPlugin


class OpenPlugin(DeferredPostPlugin):

    name = 'open'
    version = '0.0.2'
    multifile = True

    def __init__(self):
        self.load_config()

    def open_files(self, editor, filepaths):
        """ Open a file using an editor.
            Returns the process from Popen (not really used though..)
        """
        # Open the process, we don't care what happens after.
        cmd = [editor]
        cmd.extend(filepaths)
        self.print_status('Opening with: {}'.format(' '.join(cmd)))
        proc = subprocess.Popen(cmd)
        return proc

    def process(self, plugin, path):
        """ Opens the file after creation using your favorite editor. """

        return self.process_multi(plugin, [path])

    def process_multi(self, plugin, paths):
        """ Opens the file after creation using your favorite editor. """

        editor = self.config.get('editor', os.environ.get('EDITOR', ''))
        if not editor:
            msg = '\n'.join((
                'No editor could be found!',
                '\nSet one in {} with:',
                '  {{',
                '      "open": {{',
                '          "editor": "path/editor"',
                '      }}',
                '  }}\n'))
            raise ValueError(msg.format(self.config_file))
            return 1

        try:
            self.open_files(editor, paths)
        except Exception as ex:
            print('Error opening editor: {} {}\n{}'.format(
                editor,
                ' '.join(paths),
                ex,
            ))
            return 1
        return 0


exports = (OpenPlugin,)
