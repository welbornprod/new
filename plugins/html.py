""" Html plugin for New.
    -Christopher Welborn 12-25-14
"""
from plugins import Plugin, debug, print_inplace

import os

from urllib import request
from urllib.error import HTTPError


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
        self.version = '0.0.1-2'
        # Html files are not executable.
        self.ignore_post = ('chmodx',)
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

    def create(self, filename, args):
        """ Creates a simple html file. """
        title = args[0] if args else '...'
        cssfile = args[1] if len(args) > 1 else 'main.css'
        jsfile = args[2] if len(args) > 2 else 'main.js'
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
        self.version = '0.0.1-3'
        # Html files are not executable.
        self.ignore_post = ('chmodx',)
        self.load_config()
        self.usage = """
    Usage:
        jquery [version] [title] [cssfile]

    Options:
        cssfile  : Relative path to a css file to include.
                   Default: main.css
        title    : Title for the new file.
        version  : jQuery version to use.
                   Default: 2.1.3
    """

    def create(self, filename, args):
        """ Creates an html file including jQuery.
            This will download jQuery if needed.
        """
        if not args:
            args = self.get_default_args()

        ver = args[0] if args else '2.1.3'
        title = args[1] if len(args) > 1 else '...'
        cssfile = args[2] if len(args) > 2 else 'main.css'
        if self.config.get('no_download', False):
            debug('Skipping jquery download.')
            scripts = ''
        else:
            jqueryfile = self.ensure_jquery_version(ver)
            if not jqueryfile:
                errmsg = 'Unable to find or download jQuery {}!'
                raise Exception(errmsg.format(ver))
            scripts = template_scriptsrc.format(jqueryfile)

        template_args = {
            'title': title,
            'css': template_csssrc.format(cssfile),
            'scripts': scripts,
            'body': '...',
            'bodyend': template_scriptblk.format(template_ready)
        }
        return template.format(**template_args)

    def download_jquery(self, ver):
        """ Downloads a specific jquery version to the current directory.
            Returns the file name on success, or None on failure.
        """
        filename = 'jquery-{}.min.js'.format(ver)
        url = 'http://code.jquery.com/{}'.format(filename)

        self.print_status('Downloading: {}\n'.format(url))
        try:
            path, httpmsg = request.urlretrieve(
                url,
                filename=filename,
                reporthook=self.download_reporter)
        except HTTPError as ex:
            raise Exception('Unable to download: {}\n{}'.format(url, ex))

        return path

    def download_reporter(self, blocknum, readsize, totalsize):
        """ A reporter for downloads. Prints current status for the download.
        """
        size = (blocknum - 1) * readsize
        print_inplace('Downloading: {}b/{}b'.format(size, totalsize))

    def ensure_jquery_version(self, ver):
        """ Ensures that a local copy of jquery-{ver}.min.js can be found.
            If ver is None, returns None.
            If the file can't be found, it is downloaded.
            If the download fails, errors are printed and None is returned.
            Returns the filepath if the file exists, and None if it doesn't.
        """
        if ver is None:
            debug('ensure_jquery_version: None')
            return None

        filename = 'jquery-{ver}.min.js'.format(ver=ver)
        if os.path.exists(filename):
            debug('Exists: {}'.format(filename))
            return filename

        return self.download_jquery(ver)

exports = (HtmlPlugin(), JQueryPlugin())
