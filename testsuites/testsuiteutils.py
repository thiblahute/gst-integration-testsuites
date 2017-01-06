# -*- Mode: Python -*- vi:si:et:sw=4:sts=4:ts=4:syntax=python
#
# Copyright (c) 2015, Thibault Saunier <thibault.saunier@collabora.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin St, Fifth Floor,
# Boston, MA 02110-1301, USA.


import json
import os
import subprocess
import sys

from urllib.request import urlretrieve
from urllib.parse import quote

try:
    from launcher.config import GST_VALIDATE_TESTSUITE_VERSION
except ImportError:
    GST_VALIDATE_TESTSUITE_VERSION = "master"


def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def reporthook(blocknum, blocksize, totalsize):
    readsofar = blocknum * blocksize
    if totalsize > 0:
        percent = readsofar * 1e2 / totalsize
        s = "\r%5.1f%% %s / %s" % (
            percent, sizeof_fmt(readsofar), sizeof_fmt(totalsize))
        sys.stderr.write(s)
        if readsofar >= totalsize: # near the end
            sys.stderr.write("\n")
    else: # total size is unknown
        sys.stderr.write("read %d\n" % (readsofar,))

def download_files(assets_dir):
    print("Downloading %s" % assets_dir)
    fdir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        '..', 'medias'))

    with open(os.path.join(fdir, 'files.json'), 'r') as f:
        files = json.load(f)

    for f, ref_filesize in files:
        if assets_dir and not f.startswith(assets_dir):
            continue

        fname = os.path.join(fdir, f)
        if os.path.exists(fname) and os.path.getsize(fname) == ref_filesize:
            print('%s... OK' % fname)
            continue

        rpath = fname[len(fdir) + 1:]
        url = 'https://gstreamer.freedesktop.org/data/media/gst-integration-testsuite/' + quote(rpath)
        print("Downloading %s" % (url))
        urlretrieve(url, fname, reporthook)
        if os.path.getsize(fname) != ref_filesize:
            print("ERROR: File %s expected size %s != %s, this should never happen!",
                  fname, os.path.getsize(fname), ref_filesize)
            exit(1)

def update_assets(options, assets_dir):
    try:
        if options.force_sync:
            subprocess.check_call(["git","reset", "--hard"])
        download_files(os.path.basename(os.path.join(assets_dir)))
    except Exception as e:
        print("ERROR: Could not update assets \n\n%s"
              "\n\nMAKE SURE YOU HAVE git-annex INSTALLED!" % (e))

        return False

    return True
