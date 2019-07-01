""" Html plugin for New.
    -Christopher Welborn 12-25-14
"""
from plugins import Plugin, SignalExit
from plugins.jquerydl import JQueryDownloadPost

template = """<!DOCTYPE html>
<html>
    <head>
        <title>{title}</title>
{css}
{scripts}
    </head>
    <body>
        {body}
        {bodyend}
    </body>
</html>
"""

# Base template args
template_args = {
    'title': '...',
    'css': '',
    'scripts': '',
    'body': '',
    'bodyend': ''
}

template_ready = """
            $(document).ready(function () {

            });
"""
template_scriptblk = """<script type='text/javascript'>
            {}
        </script>
"""
template_scriptsrc = (
    '        <script type=\'text/javascript\' src=\'{}\'></script>'
)
template_csssrc = (
    '        <link type=\'text/css\' rel=\'stylesheet\' href=\'{}\'/>'
)


class HtmlPlugin(Plugin):

    """ Creates a blank HTML file with common css and js sources included. """
    name = ('html', 'htm')
    extensions = ('.html', '.htm')
    version = '0.0.2'
    # Html files are not executable.
    ignore_post = {'chmodx'}
    config_opts = {'author': 'Default author name for all files.'}
    docopt = True
    usage = """
    Usage:
        html [TITLE] [-c file...] [-j file...]

    Options:
        TITLE               : Title for the new file.
        -c file,--css file  : One or more relative paths to a css file to
                              include.
                              Default: main.css
        -j file,--js file   : One or more relative paths to a js file to
                              include.
                              Default: main.js
    """

    def __init__(self):
        self.load_config()

    def create(self, filename):
        """ Creates a simple html file. """
        title = self.argd['TITLE'] or '...'
        cssfiles = set(
            self.argd['--css'] or self.config.get('main_css', {'main.css'})
        )
        jsfiles = set(
            self.argd['--js'] or self.config.get('main_js', {'main.js'})
        )
        template_args = {
            'title': title,
            'css': '\n'.join(
                template_csssrc.format(s) for s in cssfiles
            ),
            'scripts': '\n'.join(
                template_scriptsrc.format(s) for s in jsfiles
            ),
            'body': '...',
            'bodyend': ''
        }
        return template.format(**template_args)


class JQueryPlugin(Plugin):

    """ Creates an html with jQuery boilerplate included.
        This will download jQuery if it is not found in the current directory.
    """
    name = ('jquery', 'jq', 'htmljq')
    extensions = ('.html', '.htm')
    version = '0.0.2'
    # Html files are not executable.
    ignore_post = {'chmodx'}

    docopt = True
    usage = """
    Usage:
        jquery [VERSION] [-c file...] [-j file...] [-t title]

    Options:
        VERSION             : jQuery version to use.
                              Using 'no' or 'none' will skip the download
                              entirely.
                              Default: latest
        -c file,--css file  : One or more relative paths to a css file to
                              include.
                              Default: main.css
        -j file,--js file   : One or more relative paths to a js file to
                              include.
                              Default: main.css
        -t str,--title str  : Title for the new file.
    """

    def __init__(self):
        self.load_config()

    def create(self, filename):
        """ Creates an html file including jQuery.
            This will download jQuery if needed.
        """

        cssfiles = set(
            self.argd['--css'] or self.config.get('main_css', ['main.css'])
        )
        jsfiles = set(
            self.argd['--js'] or self.config.get('main_js', set())
        )
        skipdl = (
            (self.argd['VERSION'] or '').lower() in {'no', 'none'} or
            self.config.get('no_download', False)
        )
        if skipdl:
            self.debug('Skipping jquery download.')
            self.ignore_deferred.add('jquerydl')
        else:
            # Set an attribute for the jquerydl plugin.
            jquerydl = JQueryDownloadPost()
            if self.argd['VERSION']:
                self.jquery_ver = self.argd['VERSION']
            else:
                verinfo = jquerydl.get_jquery_latest()
                if not verinfo:
                    raise SignalExit('Unable to get jquery version!')
                self.jquery_ver = list(verinfo.keys())[0]

            jqueryfile = jquerydl.get_jquery_file(self.jquery_ver)
            jsfiles.add(jqueryfile)

        template_args = {
            'title': self.argd['--title'] or '...',
            'css': '\n'.join(
                template_csssrc.format(s) for s in cssfiles
            ),
            'scripts': '\n'.join(
                template_scriptsrc.format(s) for s in jsfiles
            ),
            'body': '...',
            'bodyend': template_scriptblk.format(template_ready)
        }
        return template.format(**template_args)


exports = (HtmlPlugin, JQueryPlugin)
