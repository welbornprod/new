""" jQuery download, post-processing plugin for New.
    Downloads jQuery for the jQuery plugin.
    -Christopher Welborn 12-25-14
"""
import os


from lxml import html
from urllib import request
from urllib.error import HTTPError

from plugins import PostPlugin, print_inplace


class JQueryDownloadPost(PostPlugin):
    jquery_url = 'https://code.jquery.com/jquery/'

    name = 'jquerydl'
    version = '0.0.1'
    description = '\n'.join((
        'Downloads a requested jquery version for the jquery plugin.',
        'This will not overwrite existing files.'
    ))

    docopt = True
    usage = """
    Usage:
        jquerydl [-l]

    Options:
        -l,--latest  : Only show the latest version of jquery.

    The default action is to list all available jquery versions.
    """

    def create_dl_reporter(self):
        """ Create a download reporter that tracks the total bytes read so far.
            Returns: A reporter function that will print download status.
        """
        readtotal = 0
        name = self.get_name()

        def reporter(blocknum, readsize, totalsize):
            """ Print number of bytes read so far, in place. """
            nonlocal name, readtotal
            readtotal += readsize
            if totalsize > 0:
                sizefmt = '{}b/~{}b'.format(readsize, totalsize)
            else:
                sizefmt = '{}b'.format(readsize)
            print_inplace('{:<15}: Downloading: {}'.format(name, sizefmt))
        return reporter

    def download_jquery(self, ver, dest):
        """ Downloads a specific jquery version to the current directory.
            Returns the file name on success, or None on failure.
        """
        url = 'http://code.jquery.com/{}'.format(self.get_jquery_file(ver))
        self.print_status('Downloading: {}\n'.format(url))
        try:
            path, httpmsg = request.urlretrieve(
                url,
                filename=dest,
                reporthook=self.create_dl_reporter())
            self.print_status('Download complete: {}'.format(path))
        except HTTPError as ex:
            msg = '\n'.join((
                'Unable to download: {}',
                '    {}'
            )).format(url, ex)
            if ex.code == 404:
                msg = '\n'.join((
                    msg,
                    'Use `new jquerydl --` to list known versions.'
                ))
            raise Exception(msg)

        return path

    def ensure_jquery_version(self, ver, basedir):
        """ Ensures that a local copy of jquery-{ver}.min.js can be found.
            If ver is None, returns None.
            If the file can't be found, it is downloaded.
            If the download fails, errors are printed and None is returned.
            Returns the filepath if the file exists, and None if it doesn't.
        """
        destname = os.path.join(basedir, self.get_jquery_file(ver))
        if os.path.exists(destname):
            self.debug('Exists: {}'.format(destname))
            return destname

        return self.download_jquery(ver, destname)

    def format_ver_info(self, ver, link):
        return '{:<16} - {}'.format(ver, link)

    def get_jquery_file(self, ver):
        """ Get jquery filename for download based on version number. """
        return 'jquery-{ver}.min.js'.format(ver=ver)

    def get_jquery_latest(self, versioninfo=None):
        """ Return the version and link for the latest stable release
            available for download in the form of {version: dl_link}.
        """
        versinfo = versioninfo or self.get_jquery_versions()
        if not versinfo:
            return {}
        numberedvers = set()
        for ver, link in versinfo.items():
            try:
                int(ver[0])
            except ValueError:
                continue
            numberedvers.add(ver)

        latestver = sorted(numberedvers)[-1]
        return {latestver: versinfo[latestver]}

    def get_jquery_page(self):
        """ Return the html response from the jquery download page. """
        try:
            response = request.urlopen(self.jquery_url)
        except Exception as ex:
            self.print_err(
                'Unable to connect to {}.\n{}'.format(self.jquery_url, ex))
            return None
        try:
            htmldata = response.read().decode()
        except Exception as ex:
            self.print_err(
                'Unable to read/decode {}.\n{}'.format(self.jquery_url, ex))
            return None
        return htmldata

    def get_jquery_versions(self, minified=True):
        """ Return a dict of all jquery download urls in the form of:
            {version: download_url}
        """
        htmldata = self.get_jquery_page()
        if htmldata is None:
            return {}
        htmlelem = html.fromstring(htmldata)
        if htmlelem is None:
            return {}

        linktext = 'minified' if minified else 'uncompressed'

        def is_dl_link(elem):
            return (elem.text == linktext) and elem.attrib.get('href', '')

        def get_link_info(elem):
            link = elem.attrib.get('href', '').lstrip('/')
            linkend = '-'.join(link.split('-')[1:])
            ver = linkend.replace('.js', '').replace('.min', '')
            return ver, link

        htmlroot = htmlelem.getroottree().getroot()
        return dict(
            get_link_info(l)
            for l in htmlroot.cssselect('a[href]')
            if is_dl_link(l)
        )

    def list_latest(self):
        """ Print the latest version of jquery available. """
        latestverinfo = self.get_jquery_latest()
        if not latestverinfo:
            self.print_err('Unable to get latest jquery version.')
            return 1
        for ver, link in latestverinfo.items():
            print(self.format_ver_info(ver, link))
        return 0

    def list_versions(self):
        """ Print all available jquery versions. """
        versinfo = self.get_jquery_versions()
        if not versinfo:
            self.print_err('Unable to get jquery versions.')
            return 1

        for ver in sorted(versinfo):
            # Not using print_status here, no plugin name is needed.
            print(self.format_ver_info(ver, versinfo[ver]))

        latestinfo = self.get_jquery_latest(versioninfo=versinfo)
        latestver = list(latestinfo)[0]
        print('\n{}'.format(
            self.format_ver_info('latest', latestinfo[latestver]))
        )

        return 0

    def process(self, plugin, filename):
        if plugin.get_name() != 'jquery':
            return None
        ver = getattr(plugin, 'jquery_ver', None)
        if not ver:
            self.debug('No jquery_ver passed by jquery plugin!')
            return None
        elif ver.lower() in ('no', 'none'):
            self.debug('Skipping jquery download. Version was {}'.format(ver))
            return None

        self.ensure_jquery_version(ver, os.path.split(filename)[0])

    def run(self):
        """ Run this plugin as a command. """
        if self.argd['--latest']:
            return self.list_latest()
        return self.list_versions()


exports = (JQueryDownloadPost,)
