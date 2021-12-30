# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import with_statement
import subprocess
import os
import sys
try:
    import json
except ImportError:
    import simplejson as json
import locale

# Setting locale to the 'local' value
locale.setlocale(locale.LC_ALL, '')

# Perl script for Exif data extraction
exiftool_location = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 'exiftool',
                                 'exiftool')


# this class is based on code from Sven Marnach
# http://stackoverflow.com/questions/10075115/call-exiftool-from-a-python-script
class ExifTool(object):
    """used to run ExifTool from Python and keep it open"""

    sentinel = "{ready}"

    def __init__(self, executable=exiftool_location, verbose=False):
        self.executable = executable
        self.verbose = verbose

    def __enter__(self):
        self.process = subprocess.Popen(
            ['perl', self.executable, "-stay_open", "True",  "-@", "-"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.process.stdin.write(b'-stay_open\nFalse\n')
        self.process.stdin.flush()

    def execute(self, *args):
        args = args + ("-execute\n",)
        self.process.stdin.write(str.join("\n", args).encode('utf-8'))
        self.process.stdin.flush()
        output = ""
        fd = self.process.stdout.fileno()
        while not output.rstrip(' \t\n\r').endswith(self.sentinel):
            increment = os.read(fd, 4096)
            if self.verbose:
                sys.stdout.write(increment.decode('utf-8'))
            output += increment.decode('utf-8')
        return output.rstrip(' \t\n\r')[:-len(self.sentinel)]

    def get_metadata(self, *args):
        try:
            return json.loads(self.execute(*args))
        except ValueError:
            sys.stdout.write('No files to parse or invalid data\n')
