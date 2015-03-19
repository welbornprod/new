""" Html plugin for New.
    -Christopher Welborn 12-25-14
"""
from plugins import Plugin, debug


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

    def __init__(self):
        self.name = ('html', 'htm')
        self.extensions = ('.html', '.htm')
        self.version = '0.0.1-3'
        # Html files are not executable.
        self.ignore_post = {'chmodx'}
        self.usage = """
    Usage:
        html [title] [cssfile] [jsfile]

    Options:
        cssfile  : Relative path to a css file to include.
                   Default: main.css
        jsfile   : Relative path to a js file to include.
                   Default: main.js
        title    : Title for the new file.
    """

    def create(self, filename):
        """ Creates a simple html file. """
        title = self.get_arg(0, '...')
        cssfile = self.get_arg(1, 'main.css')
        jsfile = self.get_arg(2, 'main.js')
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

    def __init__(self):
        self.name = ('jquery', 'jq', 'htmljq')
        self.extensions = ('.html', '.htm')
        self.version = '0.0.1-4'
        # Html files are not executable.
        self.ignore_post = {'chmodx'}
        self.load_config()
        self.usage = """
    Usage:
        jquery [version] [title] [cssfile]

    Options:
        cssfile  : Relative path to a css file to include.
                   Default: main.css
        title    : Title for the new file.
        version  : jQuery version to use.
                   Using 'no' or 'none' will skip the download entirely.
                   Default: 2.1.3
    """

    def create(self, filename):
        """ Creates an html file including jQuery.
            This will download jQuery if needed.
        """

        title = self.get_arg(1, '...')
        cssfile = self.get_arg(2, 'main.css')
        if self.config.get('no_download', False):
            debug('Skipping jquery download.')
            scripts = ''
            self.ignore_deferred.add('jquerydl')
        else:
            # Set an attribute for the jquerydl plugin.
            self.jquery_ver = (
                self.get_arg(0, self.config.get('jq_ver', '2.1.3')))
            jqueryfile = self.get_jquery_file(self.jquery_ver)
            scripts = template_scriptsrc.format(jqueryfile)

        template_args = {
            'title': title,
            'css': template_csssrc.format(cssfile),
            'scripts': scripts,
            'body': '...',
            'bodyend': template_scriptblk.format(template_ready)
        }
        return template.format(**template_args)

    def get_jquery_file(self, ver):
        """ Get jquery filename for download based on version number. """
        return 'jquery-{ver}.min.js'.format(ver=ver)

exports = (HtmlPlugin(), JQueryPlugin())
