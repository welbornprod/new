""" jQuery download, post-processing plugin for New.
    Downloads jQuery for the jQuery plugin.
    -Christopher Welborn 12-25-14
"""
import os


from urllib import request
from urllib.error import HTTPError

from plugins import PostPlugin, debug, print_inplace


class JQueryDownloadPost(PostPlugin):

    def __init__(self):
        self.name = 'jquerydl'
        self.version = '0.0.1'
        self.description = '\n'.join((
            'Downloads a requested jquery version for the jquery plugin.',
            'This will not overwrite existing files.'
        ))

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
            raise Exception('Unable to download: {}\n{}'.format(url, ex))

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
            debug('Exists: {}'.format(destname))
            return destname

        return self.download_jquery(ver, destname)

    def get_jquery_file(self, ver):
        """ Get jquery filename for download based on version number. """
        return 'jquery-{ver}.min.js'.format(ver=ver)

    def process(self, plugin, filename):
        if not plugin.get_name() == 'jquery':
            return None
        ver = getattr(plugin, 'jquery_ver', None)
        if not ver:
            debug('No jquery_ver passed by jquery plugin!')
            return None
        elif ver.lower() in ('no', 'none'):
            debug('Skipping jquery download. Version was {}'.format(ver))
            return None

        self.ensure_jquery_version(ver, os.path.split(filename)[0])


exports = (JQueryDownloadPost(),)
