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
template_scriptsrc = '<script type=\'text/javascript\' src=\'{}\'></script>'
template_csssrc = '<link type=\'text/css\' rel=\'stylesheet\' href=\'{}\'/>'


class HtmlPlugin(Plugin):

    """ Creates a blank HTML file with common css and js sources included. """
    name = ('html', 'htm')
    extensions = ('.html', '.htm')
    version = '0.0.1-3'
    # Html files are not executable.
    ignore_post = {'chmodx'}
    usage = """
    Usage:
        html [title] [cssfile] [jsfile]

    Options:
        cssfile  : Relative path to a css file to include.
                   Default: main.css
        jsfile   : Relative path to a js file to include.
                   Default: main.js
        title    : Title for the new file.
    """

    def __init__(self):
        self.load_config()

    def create(self, filename):
        """ Creates a simple html file. """
        title = self.get_arg(0, '...')
        cssfile = self.get_arg(1, self.config.get('main_css', 'main.css'))
        jsfile = self.get_arg(2, self.config.get('main_js', 'main.js'))
        template_args = {
            'title': title,
            'css': template_csssrc.format(cssfile),
            'scripts': template_scriptsrc.format(jsfile),
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
    usage = """
    Usage:
        jquery [version] [title] [cssfile]

    Options:
        cssfile  : Relative path to a css file to include.
                   Default: main.css
        title    : Title for the new file.
        version  : jQuery version to use.
                   Using 'no' or 'none' will skip the download entirely.
                   Default: latest
    """

    def __init__(self):
        self.load_config()

    def create(self, filename):
        """ Creates an html file including jQuery.
            This will download jQuery if needed.
        """

        title = self.get_arg(1, '...')
        cssfile = self.get_arg(2, self.config.get('main_css', 'main.css'))
        if self.config.get('no_download', False):
            self.debug('Skipping jquery download.')
            scripts = ''
            self.ignore_deferred.add('jquerydl')
        else:
            # Set an attribute for the jquerydl plugin.
            jquerydl = JQueryDownloadPost()
            verarg = self.get_arg(0, default=None)
            if verarg:
                self.jquery_ver = verarg
            else:
                verinfo = jquerydl.get_jquery_latest()
                if not verinfo:
                    raise SignalExit('Unable to get jquery version!')
                self.jquery_ver = list(verinfo.keys())[0]

            jqueryfile = jquerydl.get_jquery_file(self.jquery_ver)
            scripts = template_scriptsrc.format(jqueryfile)

        template_args = {
            'title': title,
            'css': template_csssrc.format(cssfile),
            'scripts': scripts,
            'body': '...',
            'bodyend': template_scriptblk.format(template_ready)
        }
        return template.format(**template_args)

exports = (HtmlPlugin, JQueryPlugin)
