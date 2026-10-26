# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import with_statement
import os
from datetime import datetime
import re


class Image(object):

    def __init__(self, metadata={}):
        self._metadata = metadata
        self._duplicates = []
        # path used to rebuild the folder structure in the target,
        # relative to the source directory (file name by default)
        self.relativePath = os.path.basename(metadata.get('SourceFile', ''))
        filename, self.creationDate, keys = self._GetOldestTimestamp()

    def __repr__(self):
        sourceFile = self._metadata.get('SourceFile', 'unknown')
        fileHash = self._metadata.get('Hash', 'no hash')
        return '{0};{1};{2};{3}'.format(
            sourceFile,
            self.creationDate,
            fileHash,
            len(self._duplicates)
        )

    def AddDuplicate(self, filePath):
        self._duplicates.append(filePath)

    """ Return true if the file has a creation date, false otherwise """

    def IsValid(self):
        return True

    """
    extract date info from EXIF data
    YYYY:MM:DD HH:MM:SS
    or YYYY:MM:DD HH:MM:SS+HH:MM
    or YYYY:MM:DD HH:MM:SS-HH:MM
    or YYYY:MM:DD HH:MM:SSZ
    """

    def _ParseExifDate(self, date_string):
        # split into date and time
        # ['YYYY:MM:DD', 'HH:MM:SS']
        # 2016:12:27 16:19:34
        elements = str(date_string).strip().split()

        if len(elements) < 1:
            return None

        # parse year, month, day
        date_entries = elements[0].split(':')  # ['YYYY', 'MM', 'DD']

        # check if three entries, nonzero data, and no decimal
        # (which occurs for timestamps with only time but no date)
        if len(date_entries) == 3 and date_entries[0] > '0000' and '.' not in ''.join(date_entries):
            year = int(date_entries[0])
            month = int(date_entries[1])
            day = int(date_entries[2])
        else:
            return None

        # parse hour, min, second
        hour = 12  # defaulting to noon if no time data provided
        minute = 0
        second = 0

        if len(elements) > 1:
            # ['HH:MM:SS', '+', 'HH:MM']: the time zone suffix is dropped,
            # the local time as written is used for sorting
            if '+' in elements[1] or '-' in elements[1] or 'Z' in elements[1]:
                time_entries = re.split(r'([+-]|Z)', elements[1])
                # ['HH', 'MM', 'SS']
            else:
                time_entries = [elements[1]]

            time = time_entries[0].split(':')
            if len(time) == 3:
                hour = int(time[0])
                minute = int(time[1])
                second = int(time[2].split('.')[0])
            elif len(time) == 2:
                hour = int(time[0])
                minute = int(time[1])

        # form date object
        try:
            date = datetime(year, month, day, hour, minute, second)
        except ValueError:
            return None  # errors in time format

        # try converting it (some "valid" dates are way before 1900
        # and cannot be parsed by strtime later)
        try:
            # any format with year, month, day, would work here.
            date.strftime('%Y/%m-%b')
        except ValueError:
            # errors in time format
            return None

        return date

    def _GetOldestTimestamp(self, print_all_tags=False):

        # save only the oldest date
        date_available = False
        oldest_date = datetime.now()
        oldest_keys = []

        # save src file
        src_file = self._metadata['SourceFile']

        # setup tags to ignore
        ignore_tags = ['SourceFile', 'Hash']

        if print_all_tags:
            print('All relevant tags:')

        # run through all keys
        for key in self._metadata.keys():

            # check if this key needs to be ignored, or is
            # in the set of tags that must be used
            if (key not in ignore_tags) and 'GPS' not in key:

                _date = self._metadata[key]

                if print_all_tags:
                    print(str(key) + ', ' + str(_date))

                # (rare) check if multiple dates returned in a list,
                # take the first one which is the oldest
                if isinstance(_date, list):
                    _date = _date[0]

                try:
                    # check for poor-formed exif data, but allow continuation
                    exifdate = self._ParseExifDate(_date)
                except Exception as e:
                    print('Error while parsing date: {0}'.format(e))
                    exifdate = None

                if exifdate and exifdate < oldest_date:
                    date_available = True
                    oldest_date = exifdate
                    oldest_keys = [key]

                elif exifdate and exifdate == oldest_date:
                    oldest_keys.append(key)

        if not date_available:
            try:
                mtime = os.path.getmtime(src_file)
            except OSError:
                mtime = 0
            oldest_date = datetime.fromtimestamp(mtime)

        if print_all_tags:
            print()

        return src_file, oldest_date, oldest_keys
